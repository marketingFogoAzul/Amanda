# backend/services/csv_service.py

import pandas as pd
import os
from typing import List, Dict, Tuple
from config import get_config

# Carrega a configuração para obter a pasta de UPLOAD
app_config = get_config()

class CSVService:
    """
    Serviço para processar (ler e validar) arquivos CSV e XLSX.
    """
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Verifica se a extensão do arquivo é permitida."""
        allowed_extensions = app_config.ALLOWED_EXTENSIONS
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def read_spreadsheet(file_path: str) -> Tuple[List[Dict], str]:
        """
        Lê um arquivo (CSV ou XLSX) e o converte para uma lista de dicionários.
        Retorna (dados, erro)
        """
        if not os.path.exists(file_path):
            return None, "Arquivo não encontrado no servidor."
            
        try:
            # Identifica a extensão
            ext = file_path.rsplit('.', 1)[1].lower()
            
            if ext == 'csv':
                # Tenta detectar o separador (;, ou \t)
                try:
                    df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
                except Exception:
                     # Fallback para latin1 se utf-8 falhar
                    df = pd.read_csv(file_path, sep=None, engine='python', encoding='latin1')

            elif ext == 'xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
                
            else:
                return None, "Formato de arquivo não suportado."

            # Limpeza: Remove linhas completamente vazias
            df.dropna(how='all', inplace=True)
            
            # Limpeza: Converte colunas para tipos 'str' para evitar
            # problemas de formatação (ex: 5.0 -> "5")
            df = df.astype(str)
            
            # Limpeza: Substitui 'NaN' (Not a Number) por strings vazias
            df.fillna('', inplace=True)
            
            # Converte o DataFrame do Pandas para o formato JSON (lista de dicts)
            data = df.to_dict('records')
            
            if not data:
                return None, "A planilha está vazia ou em formato incorreto."

            return data, None

        except Exception as e:
            print(f"Erro ao ler planilha: {e}")
            return None, f"Erro ao processar o arquivo: {e}"

    @staticmethod
    def map_columns(data: List[Dict], mapping: Dict) -> Tuple[List[Dict], str]:
        """
        Renomeia as colunas da planilha (ex: "Nome do Cliente") para
        as colunas do nosso sistema (ex: "razao_social").
        
        'mapping' deve ser: {"Nome na Planilha": "Nome no Sistema"}
        """
        if not data:
            return None, "Nenhum dado para mapear."
            
        mapped_data = []
        try:
            for row in data:
                new_row = {}
                for spreadsheet_col, system_col in mapping.items():
                    if spreadsheet_col in row:
                        new_row[system_col] = row[spreadsheet_col]
                    else:
                        # (Opcional) Se uma coluna mapeada não for encontrada
                        new_row[system_col] = None 
                        
                mapped_data.append(new_row)
            
            return mapped_data, None
        
        except Exception as e:
            print(f"Erro ao mapear colunas: {e}")
            return None, f"Erro de mapeamento: {e}"

# --- Exemplo de uso (não faz parte do arquivo) ---
# if __name__ == "__main__":
#     # Simula um upload
#     test_file_path = "caminho/para/seu/teste.xlsx" 
#     data, err = CSVService.read_spreadsheet(test_file_path)
    
#     if err:
#         print(err)
#     else:
#         print(f"Lidos {len(data)} registros.")
#         print("Primeiro registro:", data[0])
        
#         # Mapeamento exemplo
#         col_map = {
#             "CNPJ DO COMPRADOR": "cnpj_comprador",
#             "SKU Produto": "sku",
#             "Quantidade": "qty"
#         }
#         mapped_data, map_err = CSVService.map_columns(data, col_map)
#         if map_err:
#             print(map_err)
#         else:
#             print("Primeiro registro mapeado:", mapped_data[0])