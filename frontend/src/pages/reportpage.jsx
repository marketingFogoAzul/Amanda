import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, CheckCircle, Trash2, Search, Loader, MessageSquare, Shield, Send, X } from 'react-feather';

// Utilitários e Serviços
import api from '../utils/api';
import { formatDateToBRStandard } from '../utils/formatDate'; 
// import { useAuth } from '../utils/auth'; // Para obter dados do usuário e permissões

/**
 * Componente funcional para a Página de Reports/Denúncias.
 * Exibe reports do usuário logado e/ou reports para administradores.
 */
const ReportPage = () => {
    // ⚙️ Estados de Carregamento e Dados
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reports, setReports] = useState([]);
    const [stats, setStats] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [statusFilter, setStatusFilter] = useState('');
    
    // 🔨 Estados do Modal de Resolução (Apenas Admin)
    const [isResolutionModalOpen, setIsResolutionModalOpen] = useState(false);
    const [targetReport, setTargetReport] = useState(null);
    const [resolutionData, setResolutionData] = useState({ resolucao: '', acao_tomada: 'nenhuma' });
    const [resolutionLoading, setResolutionLoading] = useState(false);

    // 🔑 Simulação do usuário atual (Em produção, viria do useAuth)
    const mockCurrentUser = {
        id: 1,
        eh_admin: true, // Exemplo: Simula um administrador vendo todos os reports
        nome_cargo: 'Desenvolvedor'
    };
    const user = mockCurrentUser; 
    
    const REPORTS_PER_PAGE = 10;

    useEffect(() => {
        fetchReports(currentPage, statusFilter);
    }, [currentPage, statusFilter, user.eh_admin]);

    // 📞 Função para buscar relatórios (Diferente para Admin e Cliente)
    const fetchReports = async (page, status) => {
        setLoading(true);
        setError(null);
        try {
            let endpoint = user.eh_admin ? '/api/report/admin/all' : '/api/report/my-reports';
            
            // Adiciona filtros e paginação
            const params = new URLSearchParams({
                page: page,
                per_page: REPORTS_PER_PAGE,
            });
            if (status) {
                params.append('status', status);
            }
            
            const response = await api.get(`${endpoint}?${params.toString()}`);
            
            setReports(response.data.reports);
            setStats(response.data.stats);
            setTotalPages(response.data.pagination.pages);
        } catch (err) {
            setError(err.message || 'Falha ao carregar relatórios.');
        } finally {
            setLoading(false);
        }
    };

    // --- Ações de Admin ---

    const openResolutionModal = (report) => {
        setTargetReport(report);
        setResolutionData({ resolucao: '', acao_tomada: 'nenhuma' });
        setIsResolutionModalOpen(true);
    };

    const handleAction = async (actionType, reportId, data = {}) => {
        setResolutionLoading(true);
        setError(null);

        let endpoint = `/api/report/admin/${reportId}`;
        let payload = {};

        try {
            switch (actionType) {
                case 'resolve':
                    endpoint += '/resolve';
                    payload = data;
                    break;
                case 'discard':
                    endpoint += '/discard';
                    payload = data;
                    break;
                case 'analyze':
                    endpoint += '/analyze';
                    break;
                default:
                    return;
            }
            
            await api.post(endpoint, payload);
            alert(`Report #${reportId} ${actionType === 'resolve' ? 'resolvido' : actionType === 'discard' ? 'descartado' : 'em análise'} com sucesso!`);
            
            setIsResolutionModalOpen(false);
            fetchReports(currentPage, statusFilter); // Recarrega dados

        } catch (err) {
            setError(err.message || `Falha ao ${actionType} report.`);
        } finally {
            setResolutionLoading(false);
        }
    };
    
    const handleFilterChange = (status) => {
        setStatusFilter(status);
        setCurrentPage(1); // Reinicia paginação
    };

    // --- Renderização Principal ---

    if (loading) {
        return <div className="text-center text-primary-brand-300 p-8"><Loader size={24} className="animate-spin inline mr-2" /> Carregando Página de Reports...</div>;
    }

    if (error && !loading) {
        return <div className="p-6 text-center text-red-500">Erro: {error}</div>;
    }

    return (
        <div className="p-6 bg-dark-bg min-h-screen">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center">
                <AlertTriangle size={28} className="mr-3 text-red-500" />
                {user.eh_admin ? 'Painel de Moderação de Reports' : 'Meus Reports Enviados'}
            </h1>

            {/* --- 1. Estatísticas e Filtros --- */}
            <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border mb-8">
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                        <StatItem title="Total" value={stats.total} statusKey="total" currentStatus={statusFilter} onFilterChange={handleFilterChange} />
                        <StatItem title="Pendentes" value={stats.pendentes} statusKey="pendente" currentStatus={statusFilter} onFilterChange={handleFilterChange} />
                        <StatItem title="Em Análise" value={stats.em_analise || 0} statusKey="em_analise" currentStatus={statusFilter} onFilterChange={handleFilterChange} />
                        <StatItem title="Resolvidos" value={stats.resolvidos} statusKey="resolvido" currentStatus={statusFilter} onFilterChange={handleFilterChange} />
                        <StatItem title="Descartados" value={stats.descartados || 0} statusKey="descartado" currentStatus={statusFilter} onFilterChange={handleFilterChange} />
                    </div>
                )}
                
                {/* Botão para limpar filtro */}
                {statusFilter && (
                    <div className="text-right">
                         <button onClick={() => handleFilterChange('')} className="text-xs text-gray-400 hover:text-white transition duration-150">
                            Limpar Filtro
                        </button>
                    </div>
                )}
            </div>

            {/* --- 2. Lista de Reports --- */}
            <div className="space-y-4">
                {reports.length > 0 ? (
                    reports.map((report) => (
                        <ReportItem 
                            key={report.id} 
                            report={report} 
                            isAdmin={user.eh_admin} 
                            onAnalyze={() => handleAction('analyze', report.id)}
                            onResolve={() => openResolutionModal(report)}
                            onDiscard={() => {
                                const motivo = prompt("Motivo para descartar:");
                                if (motivo) handleAction('discard', report.id, { motivo });
                            }}
                        />
                    ))
                ) : (
                    <p className="text-center text-gray-500 p-8">
                        {user.eh_admin ? 'Nenhum report encontrado com o filtro atual.' : 'Você ainda não enviou nenhum report.'}
                    </p>
                )}
            </div>

            {/* Paginação */}
            <Pagination currentPage={currentPage} totalPages={totalPages} setCurrentPage={setCurrentPage} />
            
            {/* --- Modal de Resolução --- */}
            {isResolutionModalOpen && targetReport && (
                <ResolutionModal 
                    report={targetReport}
                    resolutionData={resolutionData}
                    setResolutionData={setResolutionData}
                    onSubmit={handleAction}
                    onClose={() => setIsResolutionModalOpen(false)}
                    loading={resolutionLoading}
                    error={error}
                />
            )}

        </div>
    );
};

// --- Sub-Componentes Auxiliares de UI ---

const StatItem = ({ title, value, statusKey, currentStatus, onFilterChange }) => {
    const isActive = statusKey === currentStatus;
    
    let colorClass = 'border-gray-700 text-gray-400';
    if (statusKey === 'pendente') colorClass = 'border-red-500/50 text-red-400';
    if (statusKey === 'resolvido') colorClass = 'border-green-500/50 text-green-400';
    if (statusKey === 'em_analise') colorClass = 'border-yellow-500/50 text-yellow-400';
    if (statusKey === 'total') colorClass = 'border-purple-500/50 text-purple-400';

    return (
        <button
            onClick={() => onFilterChange(isActive ? '' : statusKey)}
            className={`p-3 bg-gray-800 rounded-lg shadow-lg border-2 w-full transition duration-150 ${colorClass} ${isActive ? 'ring-2 ring-offset-2 ring-offset-dark-card ring-purple-500' : 'hover:bg-gray-700/50'}`}
        >
            <p className="text-xl font-bold">{value}</p>
            <p className="text-xs font-medium mt-1">{title}</p>
        </button>
    );
};

const ReportItem = ({ report, isAdmin, onAnalyze, onResolve, onDiscard }) => {
    let statusColor = 'text-gray-400';
    let statusBg = 'bg-gray-500/20';

    if (report.status === 'pendente') { statusColor = 'text-red-400'; statusBg = 'bg-red-500/20'; }
    if (report.status === 'em_analise') { statusColor = 'text-yellow-400'; statusBg = 'bg-yellow-500/20'; }
    if (report.status === 'resolvido') { statusColor = 'text-green-400'; statusBg = 'bg-green-500/20'; }
    if (report.status === 'descartado') { statusColor = 'text-purple-400'; statusBg = 'bg-purple-500/20'; }

    return (
        <div className="p-4 bg-dark-card rounded-lg shadow-xl border border-dark-border flex justify-between items-start hover:shadow-2xl transition duration-150">
            {/* Informações do Report */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3 mb-1">
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${statusBg} ${statusColor}`}>
                        #{report.id} - {report.status.toUpperCase().replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-500">
                        {report.categoria.toUpperCase()}
                    </span>
                </div>
                
                <p className="text-sm font-semibold text-white truncate">Motivo: {report.motivo}</p>
                <p className="text-xs text-gray-400 mt-1">Chat: {report.chat_titulo} (ID: {report.chat_id})</p>
                <p className="text-xs text-gray-500">Relator: {report.relator_nome} em {formatDateToBRStandard(report.criado_em)}</p>
                
                {report.resolucao && (
                    <div className="mt-2 p-2 bg-gray-800 rounded text-xs text-green-400 border border-gray-700">
                        <p className="font-semibold">Resolução:</p>
                        <p className="text-gray-300">{report.resolucao}</p>
                        <p className="text-gray-500 mt-1">Ação Tomada: {report.acao_tomada.toUpperCase()}</p>
                    </div>
                )}
            </div>

            {/* Ações (Apenas Admin) */}
            {isAdmin && report.status !== 'resolvido' && report.status !== 'descartado' && (
                <div className="flex flex-col space-y-2 ml-4">
                    {report.status === 'pendente' && (
                        <button
                            onClick={onAnalyze}
                            className="text-xs px-3 py-1 rounded-full bg-yellow-600 hover:bg-yellow-700 text-white transition duration-150 flex items-center"
                            title="Marcar como em Análise"
                        >
                            <Clock size={14} className="mr-1" /> Analisar
                        </button>
                    )}
                    {(report.status === 'pendente' || report.status === 'em_analise') && (
                        <>
                            <button
                                onClick={onResolve}
                                className="text-xs px-3 py-1 rounded-full bg-green-600 hover:bg-green-700 text-white transition duration-150 flex items-center"
                                title="Resolver Report"
                            >
                                <CheckCircle size={14} className="mr-1" /> Resolver
                            </button>
                            <button
                                onClick={onDiscard}
                                className="text-xs px-3 py-1 rounded-full bg-purple-600 hover:bg-purple-700 text-white transition duration-150 flex items-center"
                                title="Descartar Report"
                            >
                                <Trash2 size={14} className="mr-1" /> Descartar
                            </button>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

const Pagination = ({ currentPage, totalPages, setCurrentPage }) => {
    if (totalPages <= 1) return null;
    
    return (
        <div className="flex justify-center mt-6 space-x-2">
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

// --- Modal de Resolução (Admin) ---
const ResolutionModal = ({ report, resolutionData, setResolutionData, onSubmit, onClose, loading }) => {
    const acoes = [
        { value: 'nenhuma', label: 'Nenhuma Ação (Apenas Aviso)' },
        { value: 'advertencia', label: 'Advertência Formal' },
        { value: 'suspensao', label: 'Suspensão Temporária (3 dias)' },
        { value: 'banimento', label: 'Banimento Permanente' }
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm">
            <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-lg mx-4 border border-red-800/50 p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                    <Shield size={24} className="mr-2 text-red-500" />
                    Resolver Report #{report.id}
                </h3>
                <p className="text-sm text-gray-400 mb-4">Motivo: <span className="font-semibold">{report.motivo}</span></p>

                <form onSubmit={(e) => { e.preventDefault(); onSubmit('resolve', report.id, resolutionData); }}>
                    {/* Ação Tomada */}
                    <div className="mb-4">
                        <label className="block text-gray-300 text-sm font-bold mb-2">Ação sobre o Usuário:</label>
                        <select
                            value={resolutionData.acao_tomada}
                            onChange={(e) => setResolutionData({ ...resolutionData, acao_tomada: e.target.value })}
                            className="w-full p-2 bg-gray-800 border border-gray-700 rounded text-white"
                            disabled={loading}
                        >
                            {acoes.map(a => (
                                <option key={a.value} value={a.value}>{a.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Descrição da Resolução */}
                    <div className="mb-6">
                        <label className="block text-gray-300 text-sm font-bold mb-2">Descrição da Resolução (Interna):</label>
                        <textarea
                            value={resolutionData.resolucao}
                            onChange={(e) => setResolutionData({ ...resolutionData, resolucao: e.target.value })}
                            className="w-full p-2 bg-gray-800 border border-gray-700 rounded text-white"
                            placeholder="Descreva o resultado da análise e as medidas tomadas..."
                            rows="4"
                            required
                            disabled={loading}
                        />
                    </div>
                    
                    <div className="flex justify-end space-x-3 mt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-semibold rounded-lg bg-gray-600 text-white hover:bg-gray-700"
                            disabled={loading}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className={`px-4 py-2 text-sm font-semibold rounded-lg text-white transition duration-150 flex items-center ${
                                loading ? 'bg-green-800 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
                            }`}
                            disabled={loading}
                        >
                            {loading && <Loader size={16} className="animate-spin mr-2" />}
                            Resolver e Aplicar Ação
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};


export default ReportPage;