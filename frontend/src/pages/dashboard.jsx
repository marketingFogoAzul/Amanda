import React, { useState, useEffect } from 'react';
import { MessageSquare, Clock, XCircle, FileText, Briefcase, Layers, PlusSquare, Loader, Star } from 'react-feather';

// Utilitários e Serviços
import api from '../utils/api'; 
// import { useAuth } from '../utils/auth'; // Para obter dados do usuário autenticado

/**
 * Componente funcional para o Dashboard Principal do Usuário.
 * Exibe estatísticas personalizadas (chats, importações, etc.) e links rápidos.
 */
const Dashboard = () => {
    // ⚙️ Estados
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [userStats, setUserStats] = useState(null);
    const [importStats, setImportStats] = useState(null);

    // 🔑 Simulação de dados do usuário logado (Em produção, viria do useAuth)
    const mockCurrentUser = {
        id: 1,
        nome_completo: 'Gabriel Oliveira',
        cargo: 4, // Exemplo: 4 (Representante)
        nome_cargo: 'Representante',
        pode_upload: false, // Simulação: Representante não pode fazer upload
        eh_admin: false,
        eh_empresa: true
    };
    const user = mockCurrentUser; // Uso do mock

    useEffect(() => {
        if (user) {
            fetchDashboardData();
        }
    }, [user]);

    const fetchDashboardData = async () => {
        setLoading(true);
        setError(null);
        try {
            // 1. Obter Estatísticas de Chat (Relevante para todos os usuários)
            const chatRes = await api.get('/api/chat/stats');
            setUserStats(chatRes.data.stats);

            // 2. Obter Estatísticas de Importação (Se o usuário tiver permissão)
            if (user.pode_upload || user.eh_admin) {
                const importRes = await api.get('/api/import/stats');
                setImportStats(importRes.data.stats);
            }
            
        } catch (err) {
            setError(err.message || 'Falha ao carregar dados do Dashboard.');
        } finally {
            setLoading(false);
        }
    };

    if (!user) {
        return <div className="p-6 text-center text-red-400">Usuário não autenticado. Redirecionando...</div>;
    }

    if (loading || !userStats) {
        return <div className="text-center text-primary-brand-300 p-8"><Loader size={24} className="animate-spin inline mr-2" /> Carregando Painel Principal...</div>;
    }

    // 📊 Dados de Chat para exibição
    const chatStats = userStats.chats;
    const avaliacoes = userStats.avaliacoes;

    return (
        <div className="p-6 bg-dark-bg min-h-screen">
            <h1 className="text-3xl font-bold text-white mb-2">
                Olá, {user.nome_completo.split(' ')[0]}
            </h1>
            <p className="text-gray-400 mb-8">Bem-vindo(a) ao Dashboard da Amanda AI. Seu cargo atual é: <span className="font-semibold text-primary-brand-300">{user.nome_cargo}</span></p>

            {/* --- 1. Resumo Rápido e Ações --- */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                {/* Card de Ação Principal: Nova Negociação */}
                <QuickActionCard 
                    icon={PlusSquare} 
                    title="Iniciar Nova Negociação" 
                    subtitle="Clique para começar um novo chat com Amanda AI."
                    path="/chat/new"
                    color="green"
                />
                
                {/* Card de Ação Condicional: Painéis */}
                {user.eh_admin && (
                    <QuickActionCard 
                        icon={Layers} 
                        title="Acessar Painel Admin" 
                        subtitle="Métricas globais e gestão de usuários/reports."
                        path="/admin-panel"
                        color="red"
                    />
                )}
                
                {user.eh_empresa && (
                    <QuickActionCard 
                        icon={Briefcase} 
                        title="Acessar Painel Empresa" 
                        subtitle="Gerencie sua equipe e assuma chamados."
                        path="/company-panel"
                        color="purple"
                    />
                )}
                
                {/* Card de Ação Condicional: Importação */}
                {(user.pode_upload || user.eh_admin) && (
                     <QuickActionCard 
                        icon={FileText} 
                        title="Importar Planilhas" 
                        subtitle="Faça upload de dados de produtos e regras fiscais."
                        path="/import"
                        color="yellow"
                    />
                )}

                {/* Se não for admin nem empresa, mostra o histórico */}
                {!user.eh_admin && !user.eh_empresa && (
                    <QuickActionCard 
                        icon={MessageSquare} 
                        title="Ver Histórico de Chats" 
                        subtitle={`Você tem ${chatStats.total} negociações salvas.`}
                        path="/chat/history"
                        color="blue"
                    />
                )}
            </div>

            {/* --- 2. Estatísticas de Atividade (Chats) --- */}
            <h2 className="text-xl font-semibold text-gray-300 mb-4 flex items-center"><BarChart size={20} className="mr-2 text-primary-brand-400" /> Minha Atividade</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <StatCard title="Total de Negociações" value={chatStats.total} icon={MessageSquare} color="purple" />
                <StatCard title="Chats Ativos (AI)" value={chatStats.ativos} icon={Clock} color="green" />
                <StatCard title="Chats Assumidos (Humano)" value={chatStats.assumidos} icon={Briefcase} color="yellow" />
                <StatCard title="Negociações Finalizadas" value={chatStats.fechados} icon={XCircle} color="blue" />
            </div>

            {/* --- 3. Estatísticas Secundárias (Importação/Avaliação) --- */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Estatísticas de Importação (Se aplicável) */}
                {(user.pode_upload || user.eh_admin) && importStats && (
                    <InfoBlock title="Resumo de Importação" icon={FileText} color="yellow">
                        <p>Total de Importações: <span className="font-semibold">{importStats.total_imports}</span></p>
                        <p>Taxa de Sucesso (Linhas): <span className="font-semibold text-green-400">{importStats.taxa_sucesso_linhas.toFixed(1)}%</span></p>
                        <p>Importações 30 Dias: <span className="font-semibold">{importStats.imports_30_dias}</span></p>
                    </InfoBlock>
                )}
                
                {/* Estatísticas de Avaliação (Se for usuário Empresa/Admin) */}
                {user.eh_empresa && avaliacoes && avaliacoes.total > 0 && (
                    <InfoBlock title="Métricas de Avaliação" icon={Star} color="yellow">
                        <p>Avaliação Média: <span className="text-2xl font-bold text-yellow-400">{avaliacoes.media.toFixed(1)}</span> / 5</p>
                        <p>Total de Reviews: <span className="font-semibold">{avaliacoes.total}</span></p>
                        <p>Distribuição (4-5 Estrelas): <span className="font-semibold text-green-400">{avaliacoes.distribuicao[5] + avaliacoes.distribuicao[4]}</span></p>
                    </InfoBlock>
                )}

                {/* Bloco de Mensagem Genérica ou Próximos Passos */}
                <InfoBlock title="Próximos Passos" icon={Layers} color="purple">
                    <p className="font-semibold text-white mb-2">Seu Foco Hoje:</p>
                    {user.eh_empresa ? (
                        <p>Verifique os <span className="text-green-400 font-semibold">Chamados Disponíveis</span> no Painel da Empresa para assumir uma negociação.</p>
                    ) : (
                        <p>Inicie uma <span className="text-primary-brand-300 font-semibold">Nova Negociação</span> para obter os melhores preços para seus produtos.</p>
                    )}
                </InfoBlock>
            </div>
        </div>
    );
};

// --- Sub-Componentes Auxiliares de UI ---

const StatCard = ({ icon: Icon, title, value, color }) => (
    <div className={`p-4 bg-dark-card rounded-lg shadow-lg border border-dark-border flex items-center justify-between transition duration-300 hover:border-${color}-500/50`}>
        <div>
            <p className="text-sm font-medium text-gray-400">{title}</p>
            <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div className={`p-3 rounded-full bg-${color}-500/20 text-${color}-400`}>
            <Icon size={24} />
        </div>
    </div>
);

const QuickActionCard = ({ icon: Icon, title, subtitle, path, color }) => (
    <a href={path} className={`block p-4 bg-dark-card rounded-lg shadow-lg border border-dark-border cursor-pointer transition duration-300 hover:border-${color}-500/50 hover:shadow-xl`}>
        <div className={`flex items-center text-${color}-400 mb-2`}>
            <Icon size={24} className="mr-3" />
            <p className="text-lg font-bold text-white">{title}</p>
        </div>
        <p className="text-sm text-gray-400">{subtitle}</p>
    </a>
);

const InfoBlock = ({ title, icon: Icon, color, children }) => (
    <div className={`p-6 bg-dark-card rounded-lg shadow-xl border border-dark-border transition duration-300 hover:border-${color}-500/50`}>
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
            <Icon size={20} className={`mr-2 text-${color}-400`} /> 
            {title}
        </h3>
        <div className="text-sm text-gray-400 space-y-2">
            {children}
        </div>
    </div>
);

export default Dashboard;