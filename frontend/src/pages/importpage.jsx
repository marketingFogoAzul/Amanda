import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, Download, Loader, AlertTriangle, CheckCircle, Clock, Search } from 'react-feather';

// Utilitários e Serviços
import api from '../utils/api'; 
import { formatDateToBRStandard } from '../utils/formatDate'; 
// import { useAuth } from '../utils/auth'; // Para verificar se o usuário pode_fazer_upload

/**
 * Componente funcional para a página de Importação de Planilhas.
 * Acesso restrito a cargos com permissão de upload (Dev, Júnior, Marketing, Helper).
 */
const ImportPage = () => {
    // ⚙️ Estados de Carregamento e Dados
    const [file, setFile] = useState(null);
    const [uploadLoading, setUploadLoading] = useState(false);
    const [uploadMessage, setUploadMessage] = useState(null);
    
    // 📜 Histórico e Estatísticas
    const [historyLoading, setHistoryLoading] = useState(true);
    const [importHistory, setImportHistory] = useState([]);
    const [importStats, setImportStats] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [error, setError] = useState(null);

    // 🔑 Simulação de dados do usuário atual (Em produção, usaria useAuth)
    const mockCurrentUser = {
        id: 1,
        pode_fazer_upload: true, // Apenas usuários com esta flag podem usar a página
        eh_admin: true 
    };
    const user = mockCurrentUser; 
    
    // Configurações do backend (MOCK, viria da API em /api/system/config)
    const MAX_FILE_SIZE_MB = 50;
    const ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xls'];
    const REQUIRED_COLUMNS = ['produto', 'quantidade', 'preco']; // Colunas obrigatórias

    useEffect(() => {
        if (user.pode_fazer_upload) {
            fetchImportHistory(currentPage);
        } else {
            setError('Acesso negado. Apenas cargos administrativos ou de importação podem acessar esta página.');
            setHistoryLoading(false);
        }
    }, [currentPage, user.pode_fazer_upload]);

    // 📞 Função para buscar histórico e estatísticas
    const fetchImportHistory = async (page) => {
        setHistoryLoading(true);
        try {
            const historyRes = await api.get(`/api/import/history?page=${page}&per_page=10`); 
            const statsRes = await api.get('/api/import/stats');
            
            setImportHistory(historyRes.data.imports);
            setImportStats(statsRes.data.stats);
            setTotalPages(historyRes.data.pagination.pages);
        } catch (err) {
            setError(err.message || 'Falha ao carregar histórico de importações.');
        } finally {
            setHistoryLoading(false);
        }
    };

    // 📥 Download do Template
    const handleDownloadTemplate = async () => {
        setUploadMessage(null);
        try {
            // 1. Pede a URL do template para o backend (que o gera)
            const templateRes = await api.get('/api/import/template'); 
            const downloadUrl = templateRes.data.template_url;

            // 2. Redireciona para o download do arquivo (simulação)
            // Em um sistema real, o frontend faria:
            // window.open(downloadUrl, '_blank'); 
            
            // Simulação de mensagem de sucesso para o usuário
            setUploadMessage({ type: 'success', text: 'Template solicitado com sucesso. O download iniciará em breve.' });

        } catch (err) {
            setUploadMessage({ type: 'error', text: err.message || 'Falha ao obter o template de importação.' });
        }
    };


    // 🚀 Submissão do Arquivo
    const handleFileUpload = async (e) => {
        e.preventDefault();
        if (!file) {
            setUploadMessage({ type: 'error', text: 'Selecione um arquivo para upload.' });
            return;
        }

        // 1. Validação Client-Side
        const extension = file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            setUploadMessage({ type: 'error', text: `Extensão inválida. Use: ${ALLOWED_EXTENSIONS.join(', ')}.` });
            return;
        }

        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
            setUploadMessage({ type: 'error', text: `Arquivo muito grande. Máximo: ${MAX_FILE_SIZE_MB}MB.` });
            return;
        }

        setUploadLoading(true);
        setUploadMessage(null);
        setError(null);

        // 2. Preparar dados
        const formData = new FormData();
        formData.append('file', file);

        try {
            // 3. Chamada à API (/api/import/upload)
            const response = await api.post('/api/import/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            // 4. Tratar Resposta
            const resData = response.data;
            setUploadMessage({ 
                type: resData.success ? 'success' : 'error', 
                text: resData.message || 'Processamento concluído.' 
            });
            
            setFile(null); // Limpa o arquivo selecionado
            fetchImportHistory(1); // Recarrega histórico e stats

        } catch (err) {
            console.error('Erro no upload:', err);
            setUploadMessage({ type: 'error', text: err.message || 'Erro no processamento do servidor.' });
        } finally {
            setUploadLoading(false);
        }
    };
    
    if (error && !user.pode_fazer_upload) {
        return <div className="p-6 text-center text-red-400">Acesso Negado: {error}</div>;
    }


    return (
        <div className="p-6 bg-dark-bg min-h-screen">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center">
                <FileText size={28} className="mr-3 text-yellow-400" />
                Importação de Planilhas
            </h1>

            {/* --- 1. Bloco de Upload --- */}
            <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border mb-8">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <UploadCloud size={20} className="mr-2 text-primary-brand-400" />
                    Fazer Upload
                </h2>
                
                {/* Instruções e Template */}
                <div className="text-sm text-gray-400 mb-4 space-y-2 p-3 bg-gray-800 rounded-lg border border-gray-700">
                    <p className="font-semibold text-white">Instruções:</p>
                    <ul className="list-disc list-inside space-y-1">
                        <li>Arquivos permitidos: {ALLOWED_EXTENSIONS.join(', ').toUpperCase()}. Máx. {MAX_FILE_SIZE_MB}MB.</li>
                        <li>Colunas obrigatórias: <span className="font-bold text-red-400">{REQUIRED_COLUMNS.join(', ')}</span>.</li>
                        <li>O preço deve usar **ponto** como separador decimal (ex: 25.90).</li>
                    </ul>
                    <button
                        onClick={handleDownloadTemplate}
                        className="mt-3 px-3 py-1 text-xs font-semibold rounded-full bg-green-600 hover:bg-green-700 text-white transition duration-150 flex items-center"
                    >
                        <Download size={14} className="mr-1" /> Baixar Template
                    </button>
                </div>
                
                {/* Mensagem de Status */}
                {uploadMessage && (
                    <div className={`p-3 rounded mb-4 text-sm ${uploadMessage.type === 'success' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                        {uploadMessage.text}
                    </div>
                )}

                {/* Formulário de Upload */}
                <form onSubmit={handleFileUpload} className="flex space-x-2 items-center">
                    <input
                        type="file"
                        onChange={(e) => setFile(e.target.files[0])}
                        accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
                        className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 cursor-pointer"
                        disabled={uploadLoading}
                        required
                    />
                    <button
                        type="submit"
                        className={`flex items-center px-6 py-2 text-sm font-bold rounded-lg transition duration-150 ${
                            uploadLoading ? 'bg-gray-500' : 'bg-primary-brand-600 hover:bg-primary-brand-700'
                        } text-white`}
                        disabled={uploadLoading || !file}
                    >
                        {uploadLoading ? <Loader size={18} className="animate-spin mr-1" /> : 'Processar'}
                    </button>
                </form>
            </div>

            {/* --- 2. Histórico de Importações --- */}
            <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <Clock size={20} className="mr-2 text-yellow-400" /> 
                    Histórico Recente
                </h2>

                {/* Estatísticas de Sucesso */}
                {importStats && (
                    <div className="grid grid-cols-3 gap-4 mb-4 text-center">
                        <StatItem title="Total Processado" value={importStats.total_imports} color="gray" />
                        <StatItem title="Taxa de Sucesso (%)" value={importStats.taxa_sucesso_geral.toFixed(1)} color="green" />
                        <StatItem title="Linhas com Erro" value={importStats.total_linhas_processadas - importStats.total_linhas_sucesso} color="red" />
                    </div>
                )}

                {historyLoading ? (
                    <div className="text-center text-primary-brand-300 p-4"><Loader size={20} className="animate-spin inline mr-2" /> Carregando Histórico...</div>
                ) : (
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                        {importHistory.length > 0 ? (
                            importHistory.map((log) => (
                                <ImportLogItem key={log.id} log={log} />
                            ))
                        ) : (
                            <p className="text-gray-500 text-sm">Nenhum histórico de importação encontrado.</p>
                        )}
                    </div>
                )}
                
                {/* Paginação */}
                <Pagination currentPage={currentPage} totalPages={totalPages} setCurrentPage={setCurrentPage} />
            </div>
        </div>
    );
};

// --- Sub-Componentes Auxiliares de UI ---

const StatItem = ({ title, value, color }) => (
    <div className={`p-3 bg-gray-800 rounded-lg border border-gray-700`}>
        <p className={`text-2xl font-bold text-white ${color === 'red' ? 'text-red-400' : color === 'green' ? 'text-green-400' : 'text-primary-brand-300'}`}>{value}</p>
        <p className="text-sm font-medium text-gray-400 mt-1">{title}</p>
    </div>
);


const ImportLogItem = ({ log }) => {
    let icon = <Clock size={16} className="text-yellow-400" />;
    let statusClass = 'bg-yellow-900/50 text-yellow-400';
    
    if (log.status === 'concluido') {
        icon = <CheckCircle size={16} className="text-green-400" />;
        statusClass = 'bg-green-900/50 text-green-400';
    } else if (log.status === 'falhou') {
        icon = <AlertTriangle size={16} className="text-red-400" />;
        statusClass = 'bg-red-900/50 text-red-400';
    }

    return (
        <div className="p-4 bg-gray-800 rounded-lg border border-gray-700 hover:bg-gray-700/50 transition duration-150">
            <div className="flex justify-between items-center mb-2">
                <div className="flex items-center">
                    {icon}
                    <p className="font-semibold text-white ml-2">{log.nome_arquivo}</p>
                </div>
                <span className={`px-3 py-1 text-xs font-medium rounded-full ${statusClass}`}>
                    {log.status.toUpperCase()}
                </span>
            </div>
            
            <p className="text-sm text-gray-400">Linhas Processadas: <span className="font-semibold">{log.quantidade_linhas}</span></p>
            <p className={`text-xs ${log.erro_quantidade > 0 ? 'text-red-400' : 'text-green-400'}`}>
                Sucesso: {log.sucesso_quantidade} | Erros: {log.erro_quantidade}
            </p>
            <p className="text-xs text-gray-500 mt-1">
                Enviado por: {log.usuario_nome} em {formatDateToBRStandard(log.criado_em)}
            </p>
            {log.erro_quantidade > 0 && (
                <button 
                    onClick={() => alert(`Primeiro erro: ${log.erros[0]?.erro || 'Detalhes indisponíveis'}`)}
                    className="mt-2 text-xs text-red-400 hover:text-red-300 font-semibold"
                >
                    Ver Detalhes dos Erros ({log.erro_quantidade})
                </button>
            )}
        </div>
    );
};

const Pagination = ({ currentPage, totalPages, setCurrentPage }) => {
    if (totalPages <= 1) return null;
    
    return (
        <div className="flex justify-center mt-4 space-x-2">
            <button
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm rounded-lg bg-gray-700 text-white disabled:opacity-50 hover:bg-gray-600"
            >
                Anterior
            </button>
            <span className="px-3 py-1 text-sm text-gray-300">
                Página {currentPage} de {totalPages}
            </span>
            <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm rounded-lg bg-gray-700 text-white disabled:opacity-50 hover:bg-gray-600"
            >
                Próxima
            </button>
        </div>
    );
};

export default ImportPage;