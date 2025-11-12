import React, { useState, useEffect, useRef } from 'react';
import { Send, CornerDownLeft, X, MessageSquare, Star, ChevronsDown } from 'react-feather';

// Importa utilitários do frontend
import api from '../utils/api'; // Conexão com a API
import { formatDateToBRStandard } from '../utils/formatDate'; // Formatação de data
// import EvaluationModal from './EvaluationModal'; // Importação futura para o modal de avaliação

// --- Sub-Componentes de Exibição ---

/**
 * Renderiza uma mensagem simples do usuário.
 */
const UserMessage = ({ message }) => (
    <div className="flex justify-end mb-4">
        <div className="bg-primary-brand-600 text-white p-3 rounded-t-xl rounded-bl-xl max-w-lg shadow-md">
            <p className="font-medium">{message.conteudo}</p>
            <span className="text-xs text-primary-brand-200 mt-1 block text-right">
                {formatDateToBRStandard(message.timestamp)}
            </span>
        </div>
    </div>
);

/**
 * Renderiza uma mensagem da Amanda AI ou de um Atendente Humano.
 * Inclui o resumo do LLM e as ofertas calculadas proceduralmente.
 */
const AmandaAIMessage = ({ message, handleAction, loading }) => {
    // Verifica se a mensagem contém a estrutura de oferta (do ai_service.py)
    const hasOffers = message.ofertas && message.ofertas.length > 0;

    return (
        <div className="flex justify-start mb-4">
            <div className="flex-shrink-0 mr-3">
                <div className="w-8 h-8 rounded-full bg-purple-900 flex items-center justify-center text-primary-brand-300 font-bold text-xs">
                    {message.tipo_remetente === 'amanda' ? 'AI' : 'HU'}
                </div>
            </div>
            
            <div className="bg-dark-card p-4 rounded-b-xl rounded-tr-xl max-w-3xl shadow-lg border border-primary-brand-900/50">
                {/* Cabeçalho */}
                <p className="font-semibold text-primary-brand-400 mb-2">
                    {message.tipo_remetente === 'amanda' ? 'Amanda AI - Negociação' : 'Atendente Humano'}
                </p>
                
                {/* Conteúdo Principal (Resumo Curto) */}
                <p className="text-dark-text mb-4 whitespace-pre-wrap">
                    {message.conteudo}
                </p>

                {/* --- Bloco de Ofertas (Se Existir) --- */}
                {hasOffers && (
                    <div className="bg-dark-bg p-3 rounded-lg border border-primary-brand-800 my-3">
                        <h4 className="text-sm font-bold text-primary-brand-300 mb-2 border-b border-primary-brand-900 pb-1">
                            Propostas de Negociação:
                        </h4>
                        
                        {message.ofertas.map((offer, index) => (
                            <div key={index} className={`mb-3 p-2 rounded ${offer.tipo === 'oferta_final' ? 'bg-green-900/30' : 'bg-gray-700/30'}`}>
                                <p className="font-bold text-sm text-white">{offer.titulo}</p>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {offer.condicoes}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
                
                {/* --- Ações Sugeridas (Botões) --- */}
                {message.acoes && message.acoes.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-2 border-t border-primary-brand-900 pt-3">
                        {message.acoes.map((action, index) => (
                            <button
                                key={index}
                                onClick={() => handleAction(action.acao_tipo)}
                                className="px-3 py-1 text-xs font-semibold rounded-full bg-primary-brand-700 text-white hover:bg-primary-brand-600 transition duration-150"
                                disabled={loading}
                            >
                                {action.label}
                            </button>
                        ))}
                    </div>
                )}

                <span className="text-xs text-gray-500 mt-2 block text-right">
                    {formatDateToBRStandard(message.timestamp)}
                </span>
            </div>
        </div>
    );
};

/**
 * Renderiza mensagens do Sistema (ex: chat fechado, reportado, assumido por humano).
 */
const SystemMessage = ({ message }) => (
    <div className="text-center my-4">
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-400">
            <CornerDownLeft size={12} className="mr-1" />
            {message.conteudo}
        </span>
    </div>
);

// --- Componente Principal ---

const ChatWindow = ({ initialChatId }) => {
    // 💬 Estados da interface de chat
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [chatId, setChatId] = useState(initialChatId || null);
    const [chatStatus, setChatStatus] = useState('ativo'); // ativo, assumido, fechado, reportado
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    // const [showEvaluationModal, setShowEvaluationModal] = useState(false); // Estado para modal

    // 🔗 Referência para o fim da tela (auto-scroll)
    const messagesEndRef = useRef(null);
    const chatStatusRef = useRef(chatStatus);

    useEffect(() => {
        chatStatusRef.current = chatStatus;
        scrollToBottom();
    }, [messages, chatStatus]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // 📜 Efeito para carregar histórico do chat
    useEffect(() => {
        if (chatId) {
            fetchChatHistory(chatId);
        } else {
            // Se não há chatId inicial, mostra mensagem de boas-vindas
            setMessages([{
                id: 0,
                tipo_remetente: 'amanda',
                conteudo: 'Olá! Sou a Amanda AI. Inicie a negociação enviando sua primeira mensagem.',
                timestamp: formatDateToBRStandard(new Date()),
                acoes: [],
                ofertas: []
            }]);
        }
    }, [initialChatId]);

    // 📞 Função MOCK para carregar histórico
    const fetchChatHistory = async (id) => {
        setLoading(true);
        try {
            // Em um sistema real, faria: const response = await api.get(`/chat/history?chat_id=${id}`);
            // MOCK de dados de histórico
            const mockHistory = [
                { id: 1, tipo_remetente: 'amanda', conteudo: 'Bem-vindo ao canal de negociação ZIPBUM! Como posso ajudar?', timestamp: '10/11/2025 09:00:00', acoes: [], ofertas: [] },
                { id: 2, tipo_remetente: 'usuario', conteudo: 'Gostaria de negociar 20 unidades do Copo a R$8,00.', timestamp: '10/11/2025 09:00:30', acoes: [], ofertas: [] },
                { 
                    id: 3, 
                    tipo_remetente: 'amanda', 
                    conteudo: 'Sua proposta é interessante. Para atingir R$8,00, precisamos de um volume maior. Apresento duas contra-ofertas:', 
                    timestamp: '10/11/2025 09:00:45', 
                    acoes: [
                        { label: 'Aceitar Opção 2', acao_tipo: 'confirm_offer_2' },
                        { label: 'Falar com Humano', acao_tipo: 'handoff' }
                    ], 
                    ofertas: [
                        { tipo: 'contra_oferta', titulo: 'Opção 1: 24 unid. @ R$8,80 (Total: R$211,20)', condicoes: 'Valor unitário com 8% de ajuste. Quantidade mínima 24 unid.' },
                        { tipo: 'contra_oferta', titulo: 'Opção 2: 24 unid. @ R$8,40 (Total: R$201,60)', condicoes: 'Valor unitário com 4% de ajuste. Quantidade mínima 24 unid.' },
                        { tipo: 'oferta_final', titulo: 'Oferta Final: 20 unid. @ R$8,00 (Total: R$160,00)', condicoes: 'Preço de desconto por volume (Tier 20) liberado.' }
                    ]
                }
            ];
            
            setMessages(mockHistory);
            // setChatStatus(response.data.chat.status); // Em um sistema real
        } catch (e) {
            setError('Falha ao carregar histórico.');
        } finally {
            setLoading(false);
        }
    };

    // 📤 Função para enviar mensagem (e tratar a resposta estruturada)
    const sendMessage = async (messageContent, isAction = false) => {
        if (loading || (!messageContent.trim() && !isAction) || chatStatusRef.current === 'fechado' || chatStatusRef.current === 'reportado') {
            return;
        }

        const messageToSend = messageContent.trim();
        const currentChatId = chatId;

        // 1. Adiciona a mensagem do usuário na tela imediatamente (otimista)
        const userMsg = {
            id: Date.now(),
            tipo_remetente: 'usuario',
            conteudo: messageToSend,
            timestamp: formatDateToBRStandard(new Date()),
            acoes: [], ofertas: []
        };
        setMessages(prev => [...prev, userMsg]);
        setInputMessage('');
        setLoading(true);

        try {
            // 2. Chamada à API
            const response = await api.post('/chat/send', { 
                message: messageToSend, 
                chat_id: currentChatId
            });
            
            setLoading(false);

            if (response.data.success) {
                // Se for o primeiro chat, atualiza o ID
                if (!currentChatId) {
                    setChatId(response.data.chat_id);
                }

                // 3. Adiciona a resposta da Amanda (AI/Humano)
                const amandaResponse = {
                    id: response.data.message_id || Date.now() + 1,
                    tipo_remetente: response.data.human_handling ? 'humano' : 'amanda',
                    conteudo: response.data.amanda_response || 'Mensagem encaminhada para o humano.',
                    timestamp: formatDateToBRStandard(new Date()),
                    acoes: response.data.actions,
                    ofertas: response.data.ofertas || [],
                    // Se o chat foi assumido ou fechado/reportado, atualiza o status
                    status: response.data.chat_status || chatStatusRef.current
                };
                setMessages(prev => [...prev, amandaResponse]);
                setChatStatus(amandaResponse.status);
            } else {
                // Trata falha (ex: violação de regras)
                if (response.data.chat_closed) {
                    setChatStatus('reportado');
                }
                setError(response.data.error || 'Falha ao processar mensagem.');
            }

        } catch (err) {
            console.error(err);
            setError(err.message || 'Erro ao comunicar com o servidor.');
            setLoading(false);
        }
    };
    
    // 💡 Função de Ação: executada ao clicar em um botão
    const handleActionClick = (actionType) => {
        // Implementa a lógica para cada tipo de ação
        let message;
        
        switch (actionType) {
            case 'confirm_offer_2':
                message = 'Confirmo a Opção 2 da proposta. Por favor, prossiga com a finalização do pedido.';
                break;
            case 'handoff':
                message = 'Preciso falar com um atendente humano agora.';
                // Poderia disparar uma API específica aqui: api.post('/chat/handoff', { chatId });
                break;
            case 'start_new':
                // Lógica para iniciar um novo chat (recarregar a tela)
                // window.location.reload(); 
                message = 'Iniciando nova negociação.';
                break;
            default:
                message = `Ação ${actionType} selecionada.`;
        }
        
        // Envia a mensagem de ação de volta para o backend
        sendMessage(message, true);
    };

    // 🔒 Ações do menu superior (Reportar, Fechar Chat)
    const handleCloseChat = async () => {
        if (!chatId || chatStatus === 'fechado') return;

        if (window.confirm('Tem certeza que deseja finalizar esta negociação e fechar o chat?')) {
            setLoading(true);
            try {
                // Chamada API para fechar o chat
                await api.post(`/chat/${chatId}/close`);
                setChatStatus('fechado');
                // setShowEvaluationModal(true); // Abre o modal de avaliação
                setMessages(prev => [...prev, {
                    id: Date.now(),
                    tipo_remetente: 'sistema',
                    conteudo: 'Negociação finalizada e chat fechado. Por favor, avalie o atendimento.',
                    timestamp: formatDateToBRStandard(new Date()),
                }]);
            } catch (e) {
                setError('Falha ao fechar chat.');
            } finally {
                setLoading(false);
            }
        }
    };

    const handleReportChat = () => {
        if (!chatId) return;

        const reason = prompt("Por favor, informe o motivo da denúncia:");
        if (reason) {
            setLoading(true);
            try {
                // Chamada API para criar report
                // api.post('/report/create', { chat_id: chatId, motivo: reason, categoria: 'outros' });
                setError('Report enviado com sucesso. Nossa equipe irá analisar.');
            } catch (e) {
                setError('Falha ao enviar report.');
            } finally {
                setLoading(false);
            }
        }
    };
    
    const isChatOpen = chatStatus !== 'fechado' && chatStatus !== 'reportado';
    const isHumanHandling = chatStatus === 'assumido';

    return (
        <div className="flex flex-col h-full bg-dark-card rounded-xl shadow-2xl overflow-hidden">
            
            {/* --- Cabeçalho do Chat --- */}
            <div className="flex justify-between items-center p-4 bg-gray-900 border-b border-gray-700">
                <h2 className="text-lg font-bold text-white">
                    {messages.length > 1 ? `Negociação ID: ${chatId || 'Nova'}` : 'Nova Negociação'}
                </h2>
                <div className="flex items-center space-x-3">
                    {/* Botão de Avaliar (visível apenas se fechado) */}
                    {chatStatus === 'fechado' && (
                        <button className="text-yellow-400 hover:text-yellow-300 transition duration-150 flex items-center text-sm">
                            <Star size={18} className="mr-1" />
                            Avaliar
                        </button>
                    )}
                    
                    {/* Botão de Reportar */}
                    <button 
                        onClick={handleReportChat}
                        className="text-gray-400 hover:text-red-400 transition duration-150 flex items-center text-sm"
                        title="Denunciar este chat"
                    >
                        <MessageSquare size={18} />
                    </button>

                    {/* Botão de Fechar Chat */}
                    {isChatOpen && (
                        <button 
                            onClick={handleCloseChat}
                            className="text-gray-400 hover:text-red-400 transition duration-150 flex items-center text-sm"
                            title="Finalizar e Fechar Chat"
                        >
                            <X size={18} />
                        </button>
                    )}
                </div>
            </div>

            {/* --- Área de Mensagens --- */}
            <div className="flex-1 overflow-y-auto p-6 space-y-2 custom-scrollbar">
                {messages.map(msg => {
                    if (msg.tipo_remetente === 'usuario') {
                        return <UserMessage key={msg.id} message={msg} />;
                    } else if (msg.tipo_remetente === 'amanda' || msg.tipo_remetente === 'humano') {
                        return <AmandaAIMessage key={msg.id} message={msg} handleAction={handleActionClick} loading={loading} />;
                    } else if (msg.tipo_remetente === 'sistema') {
                        return <SystemMessage key={msg.id} message={msg} />;
                    }
                    return null;
                })}
                {/* âncora para auto-scroll */}
                <div ref={messagesEndRef} />
            </div>

            {/* --- Status e Input --- */}
            <div className="p-4 bg-gray-900 border-t border-gray-700">
                
                {error && <div className="text-red-400 text-sm mb-2 p-2 bg-red-900/30 rounded">{error}</div>}

                {/* Aviso de Status do Chat */}
                {isHumanHandling && (
                    <div className="bg-yellow-900/30 text-yellow-400 text-sm p-2 rounded mb-2 flex items-center justify-center">
                        <ChevronsDown size={14} className="mr-2" />
                        Atendimento com Humano. Amanda AI está em espera.
                    </div>
                )}
                {chatStatus === 'fechado' && (
                    <div className="bg-red-900/30 text-red-400 text-sm p-2 rounded mb-2 text-center font-semibold">
                        Chat Fechado. A negociação foi finalizada.
                    </div>
                )}

                {/* Área de Input */}
                <form onSubmit={(e) => { e.preventDefault(); sendMessage(inputMessage); }} className="flex items-center">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder={isChatOpen ? "Digite sua proposta ou pergunta..." : "Chat finalizado."}
                        className="flex-1 p-3 mr-2 bg-dark-bg border border-gray-700 rounded-lg text-white focus:ring-purple-500 focus:border-purple-500 transition duration-150"
                        disabled={!isChatOpen || loading}
                    />
                    <button
                        type="submit"
                        className={`p-3 rounded-lg text-white transition duration-150 flex items-center justify-center ${
                            !isChatOpen || loading ? 'bg-gray-700 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'
                        }`}
                        disabled={!isChatOpen || loading}
                    >
                        {loading ? (
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        ) : (
                            <Send size={20} />
                        )}
                    </button>
                </form>
            </div>
            
            {/* {showEvaluationModal && (
                <EvaluationModal 
                    chatId={chatId} 
                    onClose={() => setShowEvaluationModal(false)}
                    onComplete={() => console.log('Avaliação concluída')}
                />
            )} */}
        </div>
    );
};

export default ChatWindow;