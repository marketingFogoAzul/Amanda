import React, { useState, useEffect } from 'react';
import { Settings, Users, Layers, Briefcase, BarChart, FileText, Loader, Search, Trash2, Shield, AlertTriangle, ChevronsRight, Unlock } from 'react-feather';

// Utilitários e Serviços
import api from '../utils/api';
import { formatDateToBRStandard } from '../utils/formatDate'; 
// import { useAuth } from '../utils/auth'; // Para verificar o usuário logado

/**
 * Componente funcional para o Painel Administrativo (ZIPBUM).
 * Acesso restrito a cargos 0 (Desenvolvedor) a 3 (Helper Amanda IA).
 */
const AdminPanel = () => {
    // ⚙️ Estados de Carregamento e Dados
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [globalStats, setGlobalStats] = useState(null);
    
    // 👥 Estados de Usuário e Busca
    const [usersData, setUsersData] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    
    // 📂 Estados de Logs de Importação
    const [importsData, setImportsData] = useState([]);
    const [importPage, setImportPage] = useState(1);
    const [importTotalPages, setImportTotalPages] = useState(1);

    // 🔨 Estados do Modal de Moderação
    const [isModerationModalOpen, setIsModerationModalOpen] = useState(false);
    const [targetUser, setTargetUser] = useState(null);
    const [moderationAction, setModerationAction] = useState({ action: 'ban', reason: '', days: 3 });
    const [moderationLoading, setModerationLoading] = useState(false);
    
    // 🔑 Simulação do usuário atual (Em produção, usaria useAuth)
    const mockCurrentUser = { cargo: 0, id: 1 }; // Exemplo: Desenvolvedor

    useEffect(() => {
        if (!mockCurrentUser.cargo || mockCurrentUser.cargo > 3) {
            setError('Acesso não autorizado ao Painel Administrativo.');
            setLoading(false);
            return;
        }

        fetchInitialData();
    }, []);

    useEffect(() => {
        if (!error && mockCurrentUser.cargo <= 3) {
            fetchUsersData(currentPage, searchTerm);
        }
    }, [currentPage, searchTerm]);

    const fetchInitialData = async () => {
        try {
            // 1. Métricas Globais
            const statsRes = await api.get('/api/system/status'); 
            setGlobalStats(statsRes.data);

            // 2. Logs de Importação (Primeira Página)
            const importsRes = await api.get('/api/import/history?page=1&per_page=10');
            setImportsData(importsRes.data.imports);
            setImportTotalPages(importsRes.data.pagination.pages);
            
            // 3. Usuários (Será chamado no useEffect separado)

        } catch (err) {
            setError(err.message || 'Falha ao carregar dados iniciais.');
        } finally {
            setLoading(false);
        }
    };
    
    const fetchUsersData = async (page, search) => {
        setLoading(true);
        try {
            const usersRes = await api.get(`/api/user/list?page=${page}&per_page=10&search=${search}`); // Endpoint simulado
            setUsersData(usersRes.data.users);
            setTotalPages(usersRes.data.pagination.pages);
        } catch (err) {
            setError('Falha ao carregar lista de usuários.');
        } finally {
            setLoading(false);
        }
    };

    const handleSearchChange = (e) => {
        setSearchTerm(e.target.value);
        setCurrentPage(1); // Reinicia a paginação na busca
    };

    // --- Ações de Moderação ---

    const openModerationModal = (user) => {
        setTargetUser(user);
        setIsModerationModalOpen(true);
        setModerationAction({ action: user.banido ? 'unban' : 'ban', reason: '', days: user.congelado ? 3 : 3 });
    };

    const handleModerationSubmit = async (e) => {
        e.preventDefault();
        setModerationLoading(true);

        const actionType = moderationAction.action;
        let endpoint = '';
        let payload = {};

        try {
            switch (actionType) {
                case 'ban':
                    if (!moderationAction.reason) { setError('Motivo é obrigatório para banimento.'); setModerationLoading(false); return; }
                    endpoint = '/api/admin/user/ban'; // Endpoint simulado
                    payload = { user_id: targetUser.id, motivo: moderationAction.reason };
                    break;
                case 'unban':
                    endpoint = '/api/admin/user/unban'; // Endpoint simulado
                    break;
                case 'freeze':
                    if (!moderationAction.days || moderationAction.days <= 0) { setError('Dias de congelamento inválidos.'); setModerationLoading(false); return; }
                    endpoint = '/api/admin/user/freeze'; // Endpoint simulado
                    payload = { user_id: targetUser.id, days: moderationAction.days, motivo: moderationAction.reason || 'Suspensão temporária' };
                    break;
                case 'reset_password':
                    endpoint = '/api/admin/user/reset-password'; // Endpoint simulado
                    break;
                default:
                    return;
            }
            
            // Chamada API de Moderação
            const res = await api.post(endpoint, { user_id: targetUser.id, ...payload });
            
            alert(res.data.message || 'Ação de moderação concluída.');
            setIsModerationModalOpen(false);
            fetchUsersData(currentPage, searchTerm); // Recarrega dados

        } catch (err) {
            setError(err.message || 'Falha na ação de moderação.');
        } finally {
            setModerationLoading(false);
        }
    };


    if (loading) {
        return <div className="text-center text-primary-brand-300 p-8"><Loader size={24} className="animate-spin inline mr-2" /> Carregando Painel ZIPBUM...</div>;
    }

    if (error && mockCurrentUser.cargo > 3) {
         return <div className="text-center text-red-500 p-8">Acesso Negado: {error}</div>;
    }


    return (
        <div className="p-6 bg-dark-bg min-h-screen">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center">
                <Layers size={28} className="mr-3 text-red-500" />
                Painel ZIPBUM (Administrativo)
            </h1>
            
            {/* --- 1. Dashboard de Métricas Globais --- */}
            <h2 className="text-xl font-semibold text-gray-300 mb-4 flex items-center"><BarChart size={20} className="mr-2 text-primary-brand-400" /> Dashboard Global</h2>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
                <StatCard title="Usuários Totais" value={globalStats?.total_users} color="purple" />
                <StatCard title="Empresas Ativas" value={globalStats?.total_companies} color="green" />
                <StatCard title="Chats Fechados" value={globalStats?.chats_by_status?.fechado || 0} color="blue" />
                <StatCard title="Reports Pendentes" value={globalStats?.pending_reports} color="red" />
                <StatCard title="Total Importações" value={globalStats?.total_imports} color="yellow" />
            </div>

            {/* --- 2. Gestão de Usuários e Moderação --- */}
            <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border mb-8">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <Users size={20} className="mr-2 text-primary-brand-400" /> 
                    Gerenciar Usuários
                </h2>
                
                {/* Barra de Busca (as-you-type) */}
                <div className="flex mb-4">
                    <div className="relative w-full">
                        <input
                            type="text"
                            placeholder="Buscar por nome ou e-mail..."
                            value={searchTerm}
                            onChange={handleSearchChange}
                            className="w-full p-2 pl-10 bg-gray-800 border border-gray-700 rounded-lg text-white focus:ring-purple-500 focus:border-purple-500"
                        />
                        <Search size={18} className="absolute left-3 top-2.5 text-gray-500" />
                    </div>
                </div>

                {/* Tabela de Usuários */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-700">
                        <thead className="bg-gray-800">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Usuário</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Cargo</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Último Login</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="bg-dark-card divide-y divide-gray-700">
                            {usersData.map((user) => (
                                <tr key={user.id} className="hover:bg-gray-800 transition duration-150">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                                        {user.nome_completo}
                                        <p className="text-xs text-gray-400">{user.email}</p>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.nome_cargo}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <UserStatusTag status={user.admin_status} />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{user.ultimo_login ? formatDateToBRStandard(user.ultimo_login) : 'N/A'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button 
                                            onClick={() => openModerationModal(user)}
                                            className="text-primary-brand-400 hover:text-primary-brand-300 mr-2"
                                            title="Moderar Usuário"
                                        >
                                            <Shield size={18} />
                                        </button>
                                        <button 
                                            onClick={() => handleModerationSubmit({preventDefault: () => {}}, 'reset_password', user)}
                                            className="text-yellow-500 hover:text-yellow-400"
                                            title="Resetar Senha"
                                        >
                                            <Unlock size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Paginação */}
                <Pagination currentPage={currentPage} totalPages={totalPages} setCurrentPage={setCurrentPage} />
            </div>

            {/* --- 3. Logs de Importação --- */}
            <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <FileText size={20} className="mr-2 text-yellow-400" /> 
                    Logs de Importação (Usuários)
                </h2>
                <div className="space-y-4">
                    {importsData.map((log) => (
                        <div key={log.id} className="p-3 bg-gray-800 rounded-lg border border-gray-700 hover:bg-gray-700/50 transition duration-150">
                            <div className="flex justify-between items-center">
                                <p className="font-semibold text-white">{log.nome_arquivo} - {log.status.toUpperCase()}</p>
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${log.status === 'concluido' ? 'bg-green-500/20 text-green-400' : log.status === 'falhou' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                                    {log.status}
                                </span>
                            </div>
                            <p className="text-sm text-gray-400">Linhas: {log.quantidade_linhas} | Sucesso: {log.sucesso_quantidade} ({log.taxa_sucesso.toFixed(1)}%)</p>
                            <p className="text-xs text-gray-500 mt-1">Usuário: {log.usuario_nome} em {formatDateToBRStandard(log.criado_em)}</p>
                            {log.erros_raw && log.erro_quantidade > 0 && (
                                <p className="text-xs text-red-400 mt-2 flex items-center">
                                    <AlertTriangle size={12} className="mr-1" /> {log.erro_quantidade} erros. Clique para detalhes.
                                </p>
                            )}
                        </div>
                    ))}
                </div>
                <Pagination currentPage={importPage} totalPages={importTotalPages} setCurrentPage={setImportPage} />
            </div>

            {/* --- Modal de Moderação --- */}
            {isModerationModalOpen && targetUser && (
                <ModerationModal 
                    user={targetUser} 
                    action={moderationAction}
                    setAction={setModerationAction}
                    onSubmit={handleModerationSubmit}
                    onClose={() => setIsModerationModalOpen(false)}
                    loading={moderationLoading}
                    error={error}
                />
            )}

        </div>
    );
};

// --- Sub-Componentes Auxiliares ---

const StatCard = ({ title, value, color }) => (
    <div className={`p-4 bg-dark-card rounded-lg shadow-lg border border-dark-border transition duration-300 hover:border-${color}-500/50`}>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className="text-3xl font-bold text-white mt-1">{value}</p>
    </div>
);

const UserStatusTag = ({ status }) => {
    let colorClass = 'bg-gray-500/20 text-gray-300';
    if (status === 'Banido') colorClass = 'bg-red-500/20 text-red-400';
    if (status === 'Congelado') colorClass = 'bg-yellow-500/20 text-yellow-400';
    if (status === 'Disponível') colorClass = 'bg-green-500/20 text-green-400';
    
    return (
        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${colorClass}`}>
            {status}
        </span>
    );
};

const Pagination = ({ currentPage, totalPages, setCurrentPage }) => {
    if (totalPages <= 1) return null;
    
    return (
        <div className="flex justify-center mt-4 space-x-2">
            <button
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm rounded-lg bg-gray-700 text-white disabled:opacity-50"
            >
                Anterior
            </button>
            <span className="px-3 py-1 text-sm text-gray-300">
                Página {currentPage} de {totalPages}
            </span>
            <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm rounded-lg bg-gray-700 text-white disabled:opacity-50"
            >
                Próxima
            </button>
        </div>
    );
};

// --- Modal de Moderação ---
const ModerationModal = ({ user, action, setAction, onSubmit, onClose, loading, error }) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm">
        <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-md mx-4 border border-purple-800/50 p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                <Shield size={24} className="mr-2 text-red-500" />
                Moderação de: {user.nome_completo}
            </h3>
            <p className="text-sm text-gray-400 mb-4">Cargo: {user.nome_cargo} | Status: <UserStatusTag status={user.admin_status} /></p>

            <form onSubmit={onSubmit}>
                <div className="mb-4">
                    <label className="block text-gray-300 text-sm font-bold mb-2">Ação:</label>
                    <select
                        value={action.action}
                        onChange={(e) => setAction({ ...action, action: e.target.value })}
                        className="w-full p-2 bg-gray-800 border border-gray-700 rounded text-white"
                        disabled={loading}
                    >
                        {user.banido ? <option value="unban">Desbanir</option> : <option value="ban">Banir Permanentemente</option>}
                        {user.congelado ? null : <option value="freeze">Congelar (Suspender Temporariamente)</option>}
                        <option value="reset_password">Resetar Senha</option>
                    </select>
                </div>

                {/* Campos Condicionais (Motivo / Dias) */}
                {(action.action === 'ban' || action.action === 'freeze') && (
                    <div className="mb-4">
                        <label className="block text-gray-300 text-sm font-bold mb-2">Motivo da Ação:</label>
                        <textarea
                            value={action.reason}
                            onChange={(e) => setAction({ ...action, reason: e.target.value })}
                            className="w-full p-2 bg-gray-800 border border-gray-700 rounded text-white"
                            placeholder="Descreva a violação/motivo..."
                            rows="2"
                            required={action.action === 'ban'}
                            disabled={loading}
                        />
                    </div>
                )}
                
                {action.action === 'freeze' && (
                    <div className="mb-4">
                        <label className="block text-gray-300 text-sm font-bold mb-2">Dias de Suspensão:</label>
                        <input
                            type="number"
                            min="1"
                            value={action.days}
                            onChange={(e) => setAction({ ...action, days: parseInt(e.target.value) || 1 })}
                            className="w-full p-2 bg-gray-800 border border-gray-700 rounded text-white"
                            required
                            disabled={loading}
                        />
                    </div>
                )}


                {error && (
                    <div className="bg-red-500/20 text-red-400 p-2 rounded mb-4 text-xs text-center">
                        {error}
                    </div>
                )}

                <div className="flex justify-end space-x-3 mt-6">
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
                            loading ? 'bg-purple-800 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'
                        }`}
                        disabled={loading}
                    >
                        {loading && <Loader size={16} className="animate-spin mr-2" />}
                        {action.action === 'reset_password' ? 'Confirmar Reset' : 'Aplicar Ação'}
                    </button>
                </div>
            </form>
        </div>
    </div>
);


export default AdminPanel;