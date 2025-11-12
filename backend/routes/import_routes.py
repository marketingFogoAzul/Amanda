from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
import os
import json
from models import db, LogImportacao, LogAuditoria
from config import Config
from utils.validators import Validadores
import tempfile

import_bp = Blueprint('import', __name__)

# 📁 Configurações de upload
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
UPLOAD_FOLDER = tempfile.gettempdir()  # Pasta temporária do sistema
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file):
    """Valida o tamanho do arquivo"""
    file.seek(0, 2)  # Vai para o final do arquivo
    file_size = file.tell()
    file.seek(0)  # Volta para o início
    return file_size <= MAX_FILE_SIZE

@import_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Upload de arquivo para importação (apenas cargos específicos)
    """
    # 🔒 Verificar permissão para upload
    if not current_user.pode_fazer_upload():
        return jsonify({'error': 'Apenas cargos Dev, Júnior, Marketing e Fundador podem fazer upload de planilhas'}), 403
    
    # 📁 Verificar se o arquivo foi enviado
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    
    # 📁 Verificar se o arquivo foi selecionado
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # 📁 Verificar extensão do arquivo
    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de arquivo não permitido. Use CSV, XLSX ou XLS'}), 400
    
    # 📁 Verificar tamanho do arquivo
    if not validate_file_size(file):
        return jsonify({'error': f'Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    try:
        # 🔒 Nome seguro do arquivo
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        # 📁 Criar log de importação
        log_importacao = LogImportacao(
            usuario_id=current_user.id,
            nome_arquivo=filename,
            tipo_arquivo=file_extension,
            status='processando'
        )
        db.session.add(log_importacao)
        db.session.flush()  # Para obter o ID
        
        # 💾 Salvar arquivo temporariamente
        temp_path = os.path.join(UPLOAD_FOLDER, f"import_{log_importacao.id}_{filename}")
        file.save(temp_path)
        
        # 📊 Processar arquivo
        resultado = processar_arquivo(temp_path, file_extension, log_importacao.id)
        
        # 🗑️ Limpar arquivo temporário
        try:
            os.remove(temp_path)
        except:
            pass  # Ignora erro na remoção
        
        # 📝 Atualizar log de importação
        log_importacao.quantidade_linhas = resultado.get('total_linhas', 0)
        log_importacao.sucesso_quantidade = resultado.get('sucesso_quantidade', 0)
        log_importacao.erro_quantidade = resultado.get('erro_quantidade', 0)
        log_importacao.erros = json.dumps(resultado.get('erros', []), ensure_ascii=False)
        log_importacao.status = 'concluido' if resultado['sucesso'] else 'falhou'
        log_importacao.concluido_em = Config.get_current_timestamp()
        log_importacao.tamanho_arquivo = resultado.get('tamanho_arquivo', 0)
        
        # 📝 Log de auditoria
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='arquivo_importado',
            modulo='import',
            tipo_recurso='importacao',
            recurso_id=log_importacao.id,
            detalhes=f'Arquivo {filename} importado. Sucessos: {resultado["sucesso_quantidade"]}, Erros: {resultado["erro_quantidade"]}',
            status='sucesso' if resultado['sucesso'] else 'erro',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': resultado['sucesso'],
            'message': resultado['mensagem'],
            'import_id': log_importacao.id,
            'stats': {
                'total_linhas': resultado['total_linhas'],
                'sucesso_quantidade': resultado['sucesso_quantidade'],
                'erro_quantidade': resultado['erro_quantidade'],
                'taxa_sucesso': resultado['taxa_sucesso']
            },
            'erros': resultado['erros'][:10]  # Retorna apenas os primeiros 10 erros
        })
        
    except Exception as e:
        print(f'❌ Erro no upload: {e}')
        db.session.rollback()
        
        # 📝 Log de erro
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='upload_erro',
            modulo='import',
            tipo_recurso='importacao',
            detalhes=f'Erro no upload: {str(e)}',
            status='erro',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({'error': f'Erro no processamento do arquivo: {str(e)}'}), 500

def processar_arquivo(file_path, file_extension, import_id):
    """
    Processa o arquivo de importação
    """
    erros = []
    sucesso_quantidade = 0
    total_linhas = 0
    
    try:
        # 📊 Ler arquivo baseado na extensão
        if file_extension == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8', dtype=str)
        else:  # xlsx ou xls
            df = pd.read_excel(file_path, dtype=str)
        
        # 🔍 Obter informações do arquivo
        total_linhas = len(df)
        tamanho_arquivo = os.path.getsize(file_path)
        
        # 🛡️ Validar colunas obrigatórias
        colunas_obrigatorias = ['produto', 'quantidade', 'preco']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            erros.append(f'Colunas obrigatórias faltantes: {", ".join(colunas_faltantes)}')
            return {
                'sucesso': False,
                'mensagem': f'Arquivo inválido: colunas {", ".join(colunas_faltantes)} não encontradas',
                'total_linhas': total_linhas,
                'sucesso_quantidade': 0,
                'erro_quantidade': total_linhas,
                'taxa_sucesso': 0,
                'erros': erros,
                'tamanho_arquivo': tamanho_arquivo
            }
        
        # 🔄 Processar cada linha
        for index, row in df.iterrows():
            linha_numero = index + 2  # +2 porque index começa em 0 e header é linha 1
            
            try:
                # 🛡️ Validar dados da linha
                produto = str(row['produto']).strip() if pd.notna(row['produto']) else ''
                quantidade_str = str(row['quantidade']).strip() if pd.notna(row['quantidade']) else ''
                preco_str = str(row['preco']).strip() if pd.notna(row['preco']) else ''
                
                # 🛡️ Validações
                if not produto:
                    erros.append(f'Linha {linha_numero}: Produto é obrigatório')
                    continue
                
                if len(produto) > 200:
                    erros.append(f'Linha {linha_numero}: Nome do produto muito longo (máximo 200 caracteres)')
                    continue
                
                # 🔢 Validar quantidade
                try:
                    quantidade = int(quantidade_str)
                    if quantidade <= 0:
                        erros.append(f'Linha {linha_numero}: Quantidade deve ser maior que zero')
                        continue
                except (ValueError, TypeError):
                    erros.append(f'Linha {linha_numero}: Quantidade inválida: {quantidade_str}')
                    continue
                
                # 💰 Validar preço
                try:
                    # Substituir vírgula por ponto para decimal
                    preco_str = preco_str.replace(',', '.')
                    preco = float(preco_str)
                    if preco <= 0:
                        erros.append(f'Linha {linha_numero}: Preço deve ser maior que zero')
                        continue
                except (ValueError, TypeError):
                    erros.append(f'Linha {linha_numero}: Preço inválido: {preco_str}')
                    continue
                
                # ✅ Linha processada com sucesso
                sucesso_quantidade += 1
                
                # 💾 Aqui você salvaria no banco de dados
                # Exemplo: salvar_produto(produto, quantidade, preco, current_user.id)
                
            except Exception as e:
                erros.append(f'Linha {linha_numero}: Erro inesperado - {str(e)}')
                continue
        
        # 📈 Calcular taxa de sucesso
        taxa_sucesso = (sucesso_quantidade / total_linhas) * 100 if total_linhas > 0 else 0
        
        mensagem = f'Importação concluída: {sucesso_quantidade} de {total_linhas} linhas processadas com sucesso ({taxa_sucesso:.1f}%)'
        
        return {
            'sucesso': True,
            'mensagem': mensagem,
            'total_linhas': total_linhas,
            'sucesso_quantidade': sucesso_quantidade,
            'erro_quantidade': len(erros),
            'taxa_sucesso': taxa_sucesso,
            'erros': erros,
            'tamanho_arquivo': tamanho_arquivo
        }
        
    except Exception as e:
        print(f'❌ Erro no processamento do arquivo: {e}')
        erros.append(f'Erro na leitura do arquivo: {str(e)}')
        return {
            'sucesso': False,
            'mensagem': f'Erro na leitura do arquivo: {str(e)}',
            'total_linhas': total_linhas,
            'sucesso_quantidade': 0,
            'erro_quantidade': total_linhas,
            'taxa_sucesso': 0,
            'erros': erros,
            'tamanho_arquivo': 0
        }

@import_bp.route('/history', methods=['GET'])
@login_required
def get_import_history():
    """
    Obtém histórico de importações do usuário
    """
    try:
        # 📋 Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 📋 Filtros
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # 🔍 Query base
        query = LogImportacao.query.filter_by(usuario_id=current_user.id)
        
        # 🎯 Aplicar filtros
        if status:
            query = query.filter_by(status=status)
        
        if date_from:
            try:
                # Converter data do formato DD/MM/YYYY para comparação
                date_from_obj = datetime.strptime(date_from, '%d/%m/%Y')
                query = query.filter(LogImportacao.criado_em >= date_from_obj.strftime('%d/%m/%Y 00:00:00'))
            except ValueError:
                pass  # Ignora data inválida
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%d/%m/%Y')
                query = query.filter(LogImportacao.criado_em <= date_to_obj.strftime('%d/%m/%Y 23:59:59'))
            except ValueError:
                pass  # Ignora data inválida
        
        # 📊 Ordenar e paginar
        imports = query.order_by(LogImportacao.criado_em.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        # 📈 Estatísticas
        total_imports = query.count()
        imports_concluidas = query.filter_by(status='concluido').count()
        imports_falhas = query.filter_by(status='falhou').count()
        imports_processando = query.filter_by(status='processando').count()
        
        return jsonify({
            'success': True,
            'imports': [import_log.to_dict() for import_log in imports.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': imports.total,
                'pages': imports.pages
            },
            'stats': {
                'total': total_imports,
                'concluidas': imports_concluidas,
                'falhas': imports_falhas,
                'processando': imports_processando
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter histórico de importações: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@import_bp.route('/<int:import_id>', methods=['GET'])
@login_required
def get_import_details(import_id):
    """
    Obtém detalhes de uma importação específica
    """
    try:
        import_log = LogImportacao.query.get(import_id)
        
        if not import_log:
            return jsonify({'error': 'Importação não encontrada'}), 404
        
        # 🔒 Verificar se o usuário tem acesso a esta importação
        if import_log.usuario_id != current_user.id and not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        return jsonify({
            'success': True,
            'import': import_log.to_dict()
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter detalhes da importação: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@import_bp.route('/template', methods=['GET'])
@login_required
def download_template():
    """
    Download do template para importação
    """
    try:
        # 📋 Criar template básico
        template_data = {
            'produto': ['Produto A', 'Produto B', 'Produto C'],
            'quantidade': ['10', '5', '20'],
            'preco': ['25.90', '15.50', '30.00'],
            'categoria': ['Eletrônicos', 'Casa', 'Escritório'],
            'descricao': ['Descrição do produto A', 'Descrição do produto B', 'Descrição do produto C']
        }
        
        df = pd.DataFrame(template_data)
        
        # 💾 Salvar template temporariamente
        temp_path = os.path.join(UPLOAD_FOLDER, f"template_importacao_{current_user.id}.xlsx")
        df.to_excel(temp_path, index=False)
        
        # 📝 Log de download do template
        log_auditoria = LogAuditoria(
            usuario_id=current_user.id,
            acao='template_baixado',
            modulo='import',
            tipo_recurso='template',
            detalhes='Template de importação baixado',
            status='sucesso',
            endereco_ip=request.remote_addr,
            agente_usuario=request.user_agent.string
        )
        db.session.add(log_auditoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template criado com sucesso',
            'template_url': f'/api/import/template/download/{current_user.id}',
            'columns': {
                'obrigatorias': ['produto', 'quantidade', 'preco'],
                'opcionais': ['categoria', 'descricao', 'marca', 'codigo']
            },
            'instructions': [
                'As colunas "produto", "quantidade" e "preco" são obrigatórias',
                'Quantidade deve ser um número inteiro maior que zero',
                'Preço deve usar ponto como separador decimal (ex: 25.90)',
                'Arquivos suportados: CSV, XLSX, XLS',
                'Tamanho máximo: 50MB'
            ]
        })
        
    except Exception as e:
        print(f'❌ Erro ao criar template: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@import_bp.route('/template/download/<int:user_id>', methods=['GET'])
@login_required
def download_template_file(user_id):
    """
    Download do arquivo template
    """
    try:
        # 🔒 Verificar se o usuário tem acesso
        if current_user.id != user_id and not current_user.eh_admin():
            return jsonify({'error': 'Acesso não autorizado'}), 403
        
        temp_path = os.path.join(UPLOAD_FOLDER, f"template_importacao_{user_id}.xlsx")
        
        if not os.path.exists(temp_path):
            return jsonify({'error': 'Template não encontrado'}), 404
        
        # 📤 Enviar arquivo
        from flask import send_file
        return send_file(
            temp_path,
            as_attachment=True,
            download_name='template_importacao_amanda_ai.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f'❌ Erro no download do template: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@import_bp.route('/stats', methods=['GET'])
@login_required
def get_import_stats():
    """
    Obtém estatísticas de importação do usuário
    """
    try:
        # 📊 Estatísticas gerais
        total_imports = LogImportacao.query.filter_by(usuario_id=current_user.id).count()
        imports_concluidas = LogImportacao.query.filter_by(usuario_id=current_user.id, status='concluido').count()
        imports_falhas = LogImportacao.query.filter_by(usuario_id=current_user.id, status='falhou').count()
        
        # 📈 Total de linhas processadas
        total_linhas = db.session.query(db.func.sum(LogImportacao.quantidade_linhas)).filter_by(usuario_id=current_user.id).scalar() or 0
        total_sucesso = db.session.query(db.func.sum(LogImportacao.sucesso_quantidade)).filter_by(usuario_id=current_user.id).scalar() or 0
        
        # 📅 Últimos 30 dias
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y 00:00:00')
        imports_30_dias = LogImportacao.query.filter(
            LogImportacao.usuario_id == current_user.id,
            LogImportacao.criado_em >= thirty_days_ago
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_imports': total_imports,
                'imports_concluidas': imports_concluidas,
                'imports_falhas': imports_falhas,
                'taxa_sucesso_geral': (imports_concluidas / total_imports * 100) if total_imports > 0 else 0,
                'total_linhas_processadas': total_linhas,
                'total_linhas_sucesso': total_sucesso,
                'taxa_sucesso_linhas': (total_sucesso / total_linhas * 100) if total_linhas > 0 else 0,
                'imports_30_dias': imports_30_dias
            }
        })
        
    except Exception as e:
        print(f'❌ Erro ao obter estatísticas: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

print("✅ Import routes carregadas com sucesso!")