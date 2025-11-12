import React, { useState, useEffect } from 'react';
import { Briefcase, Users, Star, MessageSquare, Plus, Trash2, Bell, CheckCircle, ChevronRight, Loader } from 'react-feather';

// Utilitários
import api from '../utils/api';
import { formatDateToBRStandard } from '../utils/formatDate';

/**
 * Componente funcional para renderizar o Painel de Gerenciamento da Empresa.
 * Acesso restrito a Representantes (4) e Vendedores (5).
 */
const CompanyPanel = ({ currentUser }) => {
    // 📊 Estados do painel
    const [panelData, setPanelData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 👤 Estados de gerenciamento de membros
    const [newMemberEmail, setNewMemberEmail] = useState('');
    const [memberLoading, setMemberLoading] = useState(false);
    const [memberMessage, setMemberMessage] = useState(null);
    
    // 📢 Estados de criação de aviso
    const [newNoticeTitle, setNewNoticeTitle] = useState('');
    const [newNoticeContent, setNewNoticeContent] = useState('');
    const [noticeLoading, setNoticeLoading] = useState(false);
    const [noticeMessage, setNoticeMessage] = useState(null);

    // Permissões
    const isRepresentative = currentUser?.cargo === 4;

    useEffect(() => {
        fetchPanelData();
    }, []);

    const fetchPanelData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get('/company/panel');
            setPanelData(response.data);
        } catch (err) {
            setError(err.message || 'Falha ao carregar dados do painel.');
        } finally {
            setLoading(false);
        }
    };
    
    // 💬 Ação: Assumir um chat disponível
    const handleClaimChat = async (chatId) => {
        if (!window.confirm(`Deseja realmente assumir o chamado #${chatId} para atendimento humano?`)) {
            return;
        }

        setLoading(true);
        try {
            await api.post('/company/claim-chat', { chat_id: chatId });
            alert(`Chamado #${chatId} assumido com sucesso!`);
            fetchPanelData(); // Recarrega os dados para atualizar listas
        } catch (err) {
            alert(`Erro ao assumir chat: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };
    
    // 👤 Ação: Adicionar membro (apenas Representante)
    const handleAddMember = async (e) => {
        e.preventDefault();
        if (!isRepresentative || !newMemberEmail) return;

        setMemberLoading(true);
        setMemberMessage(null);

        try {
            // No backend, o Representante só pode adicionar o cargo 5 (Vendedor)
            const response = await api.post('/company/add-member', { 
                email: newMemberEmail,
                cargo: 5 // Vendedor
            });
            
            setMemberMessage({ type: 'success', text: response.data.message });
            setNewMemberEmail('');
            fetchPanelData();
        } catch (err) {
            setMemberMessage({ type: 'error', text: err.message || 'Erro ao adicionar membro.' });
        } finally {
            setMemberLoading(false);
        }
    };

    // 🗑️ Ação: Remover membro (apenas Representante)
    const handleRemoveMember = async (userId, userName) => {
        if (!isRepresentative || userId === currentUser.id) {
            alert('Você não pode remover a si mesmo ou não tem permissão.');
            return;
        }
        
        if (!window.confirm(`Tem certeza que deseja remover ${userName} da equipe?`)) {
            return;
        }
        
        setMemberLoading(true);
        setMemberMessage(null);

        try {
            const response = await api.post('/company/remove-member', { user_id: userId });
            setMemberMessage({ type: 'success', text: response.data.message });
            fetchPanelData();
        } catch (err) {
            setMemberMessage({ type: 'error', text: err.message || 'Erro ao remover membro.' });
        } finally {
            setMemberLoading(false);
        }
    };

    // 📢 Ação: Criar novo aviso (apenas Representante)
    const handleCreateNotice = async (e) => {
        e.preventDefault();
        if (!isRepresentative || !newNoticeTitle || !newNoticeContent) return;

        setNoticeLoading(true);
        setNoticeMessage(null);

        try {
            const response = await api.post('/company/create-notice', { 
                title: newNoticeTitle, 
                content: newNoticeContent 
            });
            
            setNoticeMessage({ type: 'success', text: response.data.message });
            setNewNoticeTitle('');
            setNewNoticeContent('');
            fetchPanelData();
        } catch (err) {
            setNoticeMessage({ type: 'error', text: err.message || 'Erro ao criar aviso.' });
        } finally {
            setNoticeLoading(false);
        }
    };

    if (loading) {
        return <div className="text-center text-primary-brand-300 p-8"><Loader size={24} className="animate-spin inline mr-2" /> Carregando Painel Empresarial...</div>;
    }

    if (error) {
        return <div className="text-center text-red-500 p-8">Erro: {error}</div>;
    }

    if (!panelData) return null;

    return (
        <div className="p-6 bg-dark-bg min-h-screen">
            <h1 className="text-3xl font-bold text-white mb-6 flex items-center">
                <Briefcase size={28} className="mr-3 text-primary-brand-400" />
                Painel da Empresa: {panelData.company.nome_fantasia}
            </h1>

            {/* --- 1. Cartões de Estatísticas --- */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <StatCard 
                    icon={<MessageSquare />} 
                    title="Total de Chats" 
                    value={panelData.stats.total_chats} 
                    color="blue"
                />
                <StatCard 
                    icon={<Users />} 
                    title="Membros da Equipe" 
                    value={panelData.stats.team_members} 
                    color="purple"
                />
                <StatCard 
                    icon={<Star />} 
                    title="Avaliação Média" 
                    value={panelData.stats.avg_rating.toFixed(1)} 
                    color="yellow"
                />
                <StatCard 
                    icon={<Bell />} 
                    title="Chamados Disponíveis" 
                    value={panelData.stats.available_calls} 
                    color="green"
                />
            </div>

            {/* --- 2. Gestão de Chamados (Core do Vendedor) --- */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                {/* Meus Chamados (Assumidos) */}
                <ChatList 
                    title={`Meus Chamados Ativos (${panelData.stats.my_calls})`}
                    chats={panelData.my_calls}
                    actionLabel="Liberar Chat"
                    onAction={() => alert('Ação de Liberar Chat (release-chat) deve ser implementada.')}
                    showAction={false}
                    statusColor="yellow"
                />
                
                {/* Chamados Disponíveis (Para Assumir) */}
                <ChatList 
                    title={`Chamados Disponíveis (${panelData.stats.available_calls})`}
                    chats={panelData.available_calls}
                    actionLabel="Assumir Chamado"
                    onAction={handleClaimChat}
                    showAction={true}
                    statusColor="green"
                />
            </div>
            
            {/* --- 3. Membros da Equipe e Avisos (Foco Representante) --- */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                
                {/* Membros da Equipe */}
                <div className="lg:col-span-2 bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border">
                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                        <Users size={20} className="mr-2 text-purple-400" /> 
                        Membros da Equipe
                    </h3>
                    
                    {/* Formulário de Adição (Apenas Representante) */}
                    {isRepresentative && (
                        <form onSubmit={handleAddMember} className="flex space-x-2 mb-4">
                            <input
                                type="email"
                                value={newMemberEmail}
                                onChange={(e) => setNewMemberEmail(e.target.value)}
                                placeholder="E-mail do novo Vendedor"
                                className="flex-1 p-2 bg-dark-bg border border-gray-600 rounded text-dark-text"
                                required
                                disabled={memberLoading}
                            />
                            <button
                                type="submit"
                                className={`flex items-center px-4 py-2 text-sm font-bold rounded transition duration-150 ${
                                    memberLoading ? 'bg-gray-500' : 'bg-primary-brand-600 hover:bg-primary-brand-700'
                                } text-white`}
                                disabled={memberLoading}
                            >
                                {memberLoading ? <Loader size={16} className="animate-spin mr-1" /> : <Plus size={16} className="mr-1" />}
                                Adicionar
                            </button>
                        </form>
                    )}
                    
                    {memberMessage && (
                        <div className={`p-3 rounded mb-4 text-sm ${memberMessage.type === 'success' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                            {memberMessage.text}
                        </div>
                    )}

                    {/* Lista de Membros */}
                    <div className="space-y-3 mt-4 max-h-80 overflow-y-auto">
                        {panelData.team_performance.map(member => (
                            <div key={member.id} className="flex justify-between items-center p-3 bg-gray-800 rounded-lg border border-gray-700">
                                <div>
                                    <p className="font-semibold text-white">{member.nome}</p>
                                    <p className="text-xs text-gray-400">{member.cargo} - Chats Atendidos: {member.chats_atendidos}</p>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <span className={`text-sm font-bold ${member.avaliacao_media >= 4 ? 'text-yellow-400' : 'text-gray-400'}`}>
                                        <Star size={14} className="inline mr-1" /> {member.avaliacao_media.toFixed(1)}
                                    </span>
                                    {isRepresentative && member.cargo !== 'Representante' && member.id !== currentUser.id && (
                                        <button 
                                            onClick={() => handleRemoveMember(member.id, member.nome)}
                                            className="text-red-500 hover:text-red-400 p-1 rounded transition duration-150"
                                            title="Remover Vendedor"
                                            disabled={memberLoading}
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Avisos e Avaliações */}
                <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border">
                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                        <Bell size={20} className="mr-2 text-yellow-400" /> 
                        Avisos da Empresa
                    </h3>

                    {/* Formulário de Criação de Aviso (Apenas Representante) */}
                    {isRepresentative && (
                        <form onSubmit={handleCreateNotice} className="mb-4 p-3 bg-gray-800 rounded-lg">
                            <h4 className="text-sm font-bold text-primary-brand-300 mb-2">Novo Aviso</h4>
                            <input
                                type="text"
                                value={newNoticeTitle}
                                onChange={(e) => setNewNoticeTitle(e.target.value)}
                                placeholder="Título"
                                className="w-full p-2 mb-2 bg-dark-bg border border-gray-600 rounded text-dark-text text-sm"
                                required
                                disabled={noticeLoading}
                            />
                            <textarea
                                value={newNoticeContent}
                                onChange={(e) => setNewNoticeContent(e.target.value)}
                                placeholder="Conteúdo do aviso..."
                                className="w-full p-2 mb-2 bg-dark-bg border border-gray-600 rounded text-dark-text text-sm h-16"
                                required
                                disabled={noticeLoading}
                            />
                            <button
                                type="submit"
                                className={`w-full flex items-center justify-center px-4 py-1.5 text-xs font-bold rounded transition duration-150 ${
                                    noticeLoading ? 'bg-gray-500' : 'bg-green-600 hover:bg-green-700'
                                } text-white`}
                                disabled={noticeLoading}
                            >
                                {noticeLoading ? <Loader size={14} className="animate-spin mr-1" /> : <CheckCircle size={14} className="mr-1" />}
                                Publicar Aviso
                            </button>
                            {noticeMessage && (
                                <p className={`mt-2 text-xs ${noticeMessage.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>{noticeMessage.text}</p>
                            )}
                        </form>
                    )}

                    {/* Lista de Avisos */}
                    <div className="space-y-3 mt-4 max-h-48 overflow-y-auto">
                        {panelData.notices.length > 0 ? (
                            panelData.notices.map(notice => (
                                <div key={notice.id} className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                                    <p className="font-bold text-white text-sm">{notice.titulo}</p>
                                    <p className="text-xs text-gray-400 mt-1">{notice.conteudo.substring(0, 50)}...</p>
                                    <p className="text-xxs text-gray-500 mt-1">Por: {notice.autor_nome} em {formatDateToBRStandard(notice.criado_em)}</p>
                                </div>
                            ))
                        ) : (
                            <p className="text-gray-500 text-sm">Nenhum aviso ativo.</p>
                        )}
                    </div>
                </div>
            </div>
            
            {/* --- 4. Últimas Avaliações (Apenas Representante pode ver a listagem completa) --- */}
            {isRepresentative && (
                <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border mt-8">
                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                        <Star size={20} className="mr-2 text-yellow-400" /> 
                        Últimas Avaliações Recebidas
                    </h3>
                    
                    <div className="space-y-4">
                        {panelData.evaluations.length > 0 ? (
                            panelData.evaluations.map(evalu => (
                                <div key={evalu.id} className="p-3 border-b border-gray-700 last:border-b-0">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <span className="text-lg font-bold text-yellow-400">{evalu.nota} <span className="text-sm text-gray-400">/ 5</span></span>
                                            <p className="text-sm text-gray-300 inline ml-4">{evalu.classificacao}</p>
                                            <p className="text-xs text-gray-500">Chat: {evalu.chat_titulo} | Cliente: {evalu.usuario_nome}</p>
                                        </div>
                                        <span className="text-xs text-gray-500">{formatDateToBRStandard(evalu.criado_em)}</span>
                                    </div>
                                    {evalu.comentario && (
                                        <p className="text-sm italic text-gray-400 mt-2">"{evalu.comentario}"</p>
                                    )}
                                    {evalu.categorias_selecionadas.length > 0 && (
                                        <div className="mt-2 flex flex-wrap gap-1">
                                            {evalu.categorias_selecionadas.map(cat => (
                                                <span key={cat} className="text-xxs px-2 py-0.5 bg-purple-900/50 text-purple-300 rounded-full">{cat}</span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))
                        ) : (
                            <p className="text-gray-500">Nenhuma avaliação recente.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

// --- Sub-Componentes Auxiliares ---

const StatCard = ({ icon, title, value, color }) => (
    <div className={`p-4 bg-dark-card rounded-lg shadow-lg border border-dark-border flex items-center justify-between transition duration-300 hover:border-${color}-500/50`}>
        <div>
            <p className="text-sm font-medium text-gray-400">{title}</p>
            <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div className={`p-3 rounded-full bg-${color}-500/20 text-${color}-400`}>
            {icon}
        </div>
    </div>
);

const ChatList = ({ title, chats, actionLabel, onAction, showAction, statusColor }) => (
    <div className="bg-dark-card p-6 rounded-lg shadow-xl border border-dark-border">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
            <MessageSquare size={20} className={`mr-2 text-${statusColor}-400`} /> 
            {title}
        </h3>
        
        <div className="space-y-3 max-h-96 overflow-y-auto">
            {chats.length > 0 ? (
                chats.map(chat => (
                    <div key={chat.id} className="p-3 bg-gray-800 rounded-lg flex justify-between items-center border border-gray-700">
                        <div>
                            <p className="font-semibold text-white">{chat.titulo.substring(0, 40)}...</p>
                            <p className="text-xs text-gray-400">Cliente: {chat.usuario_nome}</p>
                            <p className="text-xs text-gray-500">Criado em: {formatDateToBRStandard(chat.criado_em)}</p>
                        </div>
                        {showAction && (
                            <button 
                                onClick={() => onAction(chat.id)}
                                className={`px-3 py-1 text-xs font-bold rounded-full bg-${statusColor}-600 hover:bg-${statusColor}-700 text-white transition duration-150 flex items-center`}
                            >
                                <ChevronRight size={14} className="mr-1" />
                                {actionLabel}
                            </button>
                        )}
                    </div>
                ))
            ) : (
                <p className="text-gray-500 text-sm">Nenhum chamado neste momento.</p>
            )}
        </div>
    </div>
);


export default CompanyPanel;