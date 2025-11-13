// frontend/js/import.js

/**
 * Lógica da página de Importação (import.html).
 */

document.addEventListener('DOMContentLoaded', () => {
    // Referências do DOM
    const uploadStage = $('#upload-stage');
    const mappingStage = $('#mapping-stage');
    
    const uploadForm = $('#upload-form');
    const dropzone = $('#dropzone');
    const fileInput = $('#file-input');
    const fileNameEl = $('#file-name');
    const processButton = $('#process-file-button');

    const mappingForm = $('#mapping-form');
    const mappingFieldsContainer = $('#mapping-fields');
    
    let uploadedFile = null;
    let serverFileId = null; // ID do arquivo salvo no backend
    let fileHeaders = []; // Colunas da planilha

    // --- 1. LÓGICA DO UPLOAD (DRAG & DROP) ---

    // Previne o comportamento padrão do navegador
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Destaca a área ao arrastar
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('hover'), false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('hover'), false);
    });

    // Pega o arquivo ao "soltar"
    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }, false);

    // Pega o arquivo pelo clique no <input>
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    /**
     * Valida e armazena o arquivo selecionado.
     */
    function handleFile(file) {
        // Validação simples (pode ser mais robusta)
        if (!file.type.match(/csv/) && !file.type.match(/spreadsheetml/)) {
            showMessage('upload-error-message', 'Formato inválido. Use .csv ou .xlsx');
            return;
        }
        
        uploadedFile = file;
        fileNameEl.textContent = file.name;
        processButton.disabled = false; // Ativa o botão
        hideMessage('upload-error-message');
    }

    // --- 2. LÓGICA DE PROCESSAMENTO (ENVIO) ---

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!uploadedFile) return;

        processButton.disabled = true;
        processButton.textContent = 'Enviando...';
        
        // Precisamos usar FormData para enviar arquivos
        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            // (fetchApi não suporta FormData, precisamos de uma chamada customizada)
            const response = await fetch(`${API_BASE_URL}/import/upload`, {
                method: 'POST',
                body: formData,
                headers: {
                    // NÃO definimos 'Content-Type', o navegador faz isso
                    'Authorization': `Bearer ${getToken()}`
                }
            });
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro no upload');
            }

            // Sucesso!
            serverFileId = data.file_path_id;
            fileHeaders = data.headers;
            
            // Transição para o Estágio 2
            uploadStage.style.display = 'none';
            mappingStage.style.display = 'block';
            
            // Constrói a interface de mapeamento
            buildMappingUI(fileHeaders);

        } catch (error) {
            showMessage('upload-error-message', error.message);
            processButton.disabled = false;
            processButton.textContent = 'Processar e Mapear Colunas';
        }
    });

    // --- 3. LÓGICA DE MAPEAMENTO ---

    /**
     * Constrói os campos <select> para o mapeamento.
     */
    function buildMappingUI(headers) {
        // Definição dos campos que o NOSSO SISTEMA espera
        const systemFields = [
            { key: 'cnpj_comprador', label: 'CNPJ do Comprador' },
            { key: 'razao_social', label: 'Razão Social (Comprador)' },
            { key: 'sku_produto', label: 'SKU do Produto' },
            { key: 'quantidade', label: 'Quantidade' },
            { key: 'preco_unitario', label: 'Preço Unitário' }
        ];

        // Limpa o container
        mappingFieldsContainer.innerHTML = '';
        
        // Cria uma linha para cada coluna da planilha
        headers.forEach(header => {
            const row = document.createElement('div');
            row.className = 'mapping-row';
            
            // Cria as opções do <select>
            const options = systemFields.map(field => 
                `<option value="${field.key}">${field.label}</option>`
            ).join('');

            row.innerHTML = `
                <div class="mapping-col-sheet">
                    <label>${header}</label>
                </div>
                <i data-feather="arrow-right"></i>
                <div class="mapping-col-system">
                    <select data-sheet-column="${header}">
                        <option value="">Ignorar Coluna</option>
                        ${options}
                    </select>
                </div>
            `;
            mappingFieldsContainer.appendChild(row);
        });
        
        feather.replace(); // Ativa os novos ícones
    }

    /**
     * (Futuro) Envia o mapeamento final para o backend.
     */
    mappingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const mapping = {};
        // Pega o mapeamento de todos os <select>
        $$('#mapping-fields select').forEach(select => {
            const sheetColumn = select.dataset.sheetColumn;
            const systemColumn = select.value;
            
            if (systemColumn) { // Se não for "Ignorar Coluna"
                mapping[sheetColumn] = systemColumn;
            }
        });

        console.log("Mapeamento final:", mapping);
        console.log("ID do arquivo no servidor:", serverFileId);

        // (Aqui viria a chamada 'fetchApi' para /api/import/process_mapping
        // que ainda não criamos no backend)
        
        showMessage('mapping-error-message', 'Em construção. O mapeamento foi logado no console.', 'success');
    });

});