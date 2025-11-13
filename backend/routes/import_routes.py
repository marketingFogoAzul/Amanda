# backend/routes/import_routes.py

from flask import request, jsonify
from . import import_bp # Importa o Blueprint
from services.csv_service import CSVService
from services.role_service import roles_required
from utils.constants import Cargos
from config import get_config
from werkzeug.utils import secure_filename
import os
import uuid

# Carrega a configuração (para UPLOAD_FOLDER)
app_config = get_config()

@import_bp.route('/upload', methods=['POST'])
@roles_required([Cargos.REPRESENTANTE, Cargos.VENDEDOR, Cargos.ADMIN_ZIPBUM]) # Apenas usuários de empresa ou admins
def upload_spreadsheet():
    """
    Endpoint para upload de planilhas (CSV/XLSX).
    Recebe o arquivo, lê e retorna os dados e cabeçalhos.
    """
    
    # 1. Verifica se o arquivo está na requisição
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado. (Verifique o 'name' do form-data)"}), 400
        
    file = request.files['file']
    
    # 2. Verifica se o nome do arquivo não está vazio
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio."}), 400

    # 3. Valida a extensão do arquivo
    if not CSVService.allowed_file(file.filename):
        return jsonify({"error": "Extensão de arquivo não permitida (use .csv ou .xlsx)."}), 400

    try:
        # 4. Salva o arquivo temporariamente com um nome seguro
        
        # Gera um nome de arquivo único para evitar conflitos
        filename = secure_filename(file.filename)
        unique_filename = f"{str(uuid.uuid4())}_{filename}"
        
        # Caminho completo para salvar
        upload_folder = app_config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder) # Cria a pasta se não existir
            
        file_path = os.path.join(upload_folder, unique_filename)
        
        file.save(file_path)

        # 5. Processa a planilha usando o CSVService
        data, error = CSVService.read_spreadsheet(file_path)
        
        if error:
            # (Opcional) Remover o arquivo se a leitura falhar
            os.remove(file_path)
            return jsonify({"error": error}), 400
            
        # 6. Extrai os cabeçalhos (nomes das colunas) da planilha
        if not data:
            os.remove(file_path)
            return jsonify({"error": "Planilha está vazia."}), 400
            
        headers = list(data[0].keys())

        # 7. Sucesso! Retorna os dados, cabeçalhos e o caminho do arquivo
        # O frontend usará 'file_path_id' (o nome do arquivo)
        # para enviar na próxima etapa (mapeamento).
        return jsonify({
            "message": "Arquivo lido com sucesso!",
            "file_path_id": unique_filename, # ID para a próxima etapa
            "headers": headers, # Colunas da planilha
            "data_preview": data[:10] # Prévia dos 10 primeiros registros
        }), 200

    except Exception as e:
        print(f"Erro no upload da planilha: {e}")
        # Tenta remover o arquivo se der erro
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500