import os
import json
import pandas as pd
from typing import List, Dict, Any

# Assumindo que Config está disponível para constantes como REQUIRED_COLUMNS
from config import Config 

# Nota: A classe 'Validadores' (mencionada em import_routes.py) 
# não é estritamente necessária aqui, pois as rotas usam apenas verificações básicas 
# de tipo/string. Mantemos a lógica conforme a implementação original.

class CSVImportService:
    """
    Serviço dedicado ao processamento e validação de arquivos de importação 
    (CSV, XLSX, XLS), seguindo as regras de negócio da plataforma ZIPBUM.
    Esta classe encapsula a lógica de processamento que era encontrada em 'import_routes.py'.
    """

    def __init__(self):
        """Inicializa o serviço de importação."""
        # Colunas obrigatórias definidas em config.py
        # Baseado em import_routes.py e config.py, as colunas são: 
        # ['produto', 'quantidade', 'preco']
        try:
            self.required_columns = Config.IMPORT['required_columns']
        except AttributeError:
             # Fallback caso Config.IMPORT não esteja totalmente definida
             self.required_columns = ['produto', 'quantidade', 'preco']


    def _read_file_to_dataframe(self, file_path: str, file_extension: str) -> pd.DataFrame:
        """Lê o arquivo e retorna um DataFrame."""
        if file_extension == 'csv':
            # Tenta ler com encoding utf-8; dtype=str para evitar inferência de tipos
            return pd.read_csv(file_path, encoding='utf-8', dtype=str)
        elif file_extension in ['xlsx', 'xls']:
            return pd.read_excel(file_path, dtype=str)
        else:
            # Esta exceção deve ser tratada ANTES pelo upload_file da rota
            raise ValueError(f"Extensão de arquivo não suportada: {file_extension}")

    def process_file(self, file_path: str, file_extension: str) -> Dict[str, Any]:
        """
        Processa o arquivo de importação, realiza validações por coluna e por linha.
        Retorna um dicionário com estatísticas e lista de erros.
        """
        erros: List[Dict[str, Any]] = []
        sucesso_quantidade = 0
        total_linhas = 0
        tamanho_arquivo = 0

        try:
            # 1. Leitura do Arquivo
            df = self._read_file_to_dataframe(file_path, file_extension)
            total_linhas = len(df)
            tamanho_arquivo = os.path.getsize(file_path)
            
            if total_linhas == 0:
                 erros.append({'linha': 1, 'erro': 'Arquivo vazio ou sem dados.'})
                 raise Exception('Arquivo vazio ou sem dados.')

            # 2. Validação de Colunas Obrigatórias
            colunas_faltantes = [col for col in self.required_columns if col not in df.columns]
            
            if colunas_faltantes:
                erros.append({
                    'linha': 1, 
                    'erro': f'Colunas obrigatórias faltantes: {", ".join(colunas_faltantes)}'
                })
                # Retorna com erro de validação de estrutura
                return self._create_result(False, f'Arquivo inválido: Colunas faltantes: {", ".join(colunas_faltantes)}', 
                                           total_linhas, 0, total_linhas, erros, tamanho_arquivo)


            # 3. Processamento e Validação por Linha
            for index, row in df.iterrows():
                linha_numero = index + 2  # +2: index (0) + header (1)
                linha_erros: List[str] = []
                
                # Obtém e limpa campos
                produto = str(row.get('produto', '')).strip()
                quantidade_str = str(row.get('quantidade', '')).strip()
                preco_str = str(row.get('preco', '')).strip()
                
                # a) Validação do Produto
                if not produto:
                    linha_erros.append('Produto é obrigatório')
                elif len(produto) > 200:
                    linha_erros.append('Nome do produto muito longo (máximo 200 caracteres)')
                
                # b) Validação da Quantidade (Inteiro > 0)
                try:
                    quantidade = int(quantidade_str)
                    if quantidade <= 0:
                        linha_erros.append('Quantidade deve ser um número inteiro maior que zero')
                except (ValueError, TypeError):
                    linha_erros.append(f'Quantidade inválida: "{quantidade_str}"')
                
                # c) Validação do Preço (Float > 0)
                try:
                    # Suporta vírgula por ponto para decimal, conforme regra brasileira
                    preco_str = preco_str.replace(',', '.')
                    preco = float(preco_str)
                    if preco <= 0:
                        linha_erros.append('Preço deve ser maior que zero')
                except (ValueError, TypeError):
                    linha_erros.append(f'Preço inválido: "{preco_str}"')
                
                
                if linha_erros:
                    # Linha falhou na validação
                    erros.append({
                        'linha': linha_numero, 
                        'erro': '; '.join(linha_erros),
                        'dados_raw': row.to_dict()
                    })
                else:
                    # ✅ Linha validada com sucesso (Simula a inserção no DB)
                    sucesso_quantidade += 1
        
        except Exception as e:
            # Erro fatal durante o processamento (ex: arquivo corrompido)
            if not erros: 
                 erros.append({'linha': 1, 'erro': f'Erro fatal durante o processamento: {str(e)}'})

            return self._create_result(False, f'Erro grave no processamento: {str(e)}', 
                                       total_linhas, 0, total_linhas, erros, tamanho_arquivo)


        # 4. Retorno de Resultado Final
        taxa_sucesso = (sucesso_quantidade / total_linhas * 100) if total_linhas > 0 else 0
        final_success = sucesso_quantidade > 0

        mensagem = f'Importação concluída: {sucesso_quantidade} de {total_linhas} linhas processadas com sucesso ({taxa_sucesso:.1f}%)'
        if not final_success:
            mensagem = f'Importação falhou: Nenhuma linha processada com sucesso. Total de erros: {len(erros)}'

        return self._create_result(final_success, mensagem, total_linhas, 
                                   sucesso_quantidade, len(erros), erros, tamanho_arquivo)


    def _create_result(self, success: bool, message: str, total_lines: int, success_qty: int, error_qty: int, errors: List[Dict[str, Any]], file_size: int) -> Dict[str, Any]:
        """Função auxiliar para formatar o resultado de forma consistente."""
        taxa_sucesso = (success_qty / total_lines * 100) if total_lines > 0 else 0
        
        return {
            'sucesso': success,
            'mensagem': message,
            'total_linhas': total_lines,
            'sucesso_quantidade': success_qty,
            'erro_quantidade': error_qty,
            'taxa_sucesso': taxa_sucesso,
            'erros': errors,
            'tamanho_arquivo': file_size
        }