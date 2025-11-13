// frontend/js/chat.js

/**
 * Lógica da página de Chat (chat.html).
 */

document.addEventListener('DOMContentLoaded', () => {
    // Referências do DOM
    const chatListUL = $('#chat-list-ul');
    const chatWindow = $('.chat-window');
    const messagesContainer = $('#chat-messages');
    const messageInput = $('#message-input');
    const sendButton = $('#send-message-button');
    const chatTitle = $('#chat-title');
    const newChatButton = $('#new-chat-button');
    const placeholder = $('.chat-placeholder');

    let currentChatId = null; // Armazena o ID do chat ativo

    // --- 1. INICIALIZAÇÃO ---
    
    // (Futuro) Carregar a lista de chats do usuário
    // loadChatList();

    // Habilita a área de input se um chat estiver selecionado (ex: por URL)
    // if (currentChatId) {
    //     enableChatInput();
    // }

    // --- 2. EVENT LISTENERS ---

    // Enviar mensagem com o botão
    sendButton.addEventListener('click', sendMessage);
    
    // Enviar mensagem com 'Enter' (e Shift+Enter para nova linha)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Impede a nova linha
            sendMessage();
        }
    });

    // (Futuro) Clicar em um item da lista de chat
    // chatListUL.addEventListener('click', (e) => {
    //     const chatItem = e.target.closest('.chat-list-item');
    //     if (chatItem) {
    //         const chatId = chatItem.dataset.chatId;
    //         if (chatId !== currentChatId) {
    //             selectChat(chatId);
    //         }
    //     }
    // });
    
    // (Futuro) Botão de Novo Chat
    // newChatButton.addEventListener('click', createNewChat);


    // --- 3. FUNÇÕES PRINCIPAIS ---

    /**
     * (Função de exemplo - precisa ser ativada)
     * Seleciona um chat, carrega o histórico e o ativa.
     */
    async function selectChat(chatId) {
        currentChatId = chatId;
        
        // Limpa a janela
        messagesContainer.innerHTML = '';
        
        // Ativa o CSS
        $$('.chat-list-item').forEach(item => item.classList.remove('active'));
        $(`.chat-list-item[data-chat-id="${chatId}"]`).classList.add('active');

        // Carrega o histórico
        try {
            const history = await fetchApi(`/chat/history/${chatId}`, 'GET', null, true);
            history.forEach(renderMessage); // Renderiza cada mensagem
            
            // Atualiza o título e ativa o input
            chatTitle.textContent = "Carregando..."; // (Ajustar para pegar o título real)
            enableChatInput();
            
        } catch (error) {
            showMessage('chat-error', error.message); // (Precisa de um elemento de erro no HTML)
        }
    }

    /**
     * Envia a mensagem do usuário para o backend.
     */
    async function sendMessage() {
        const content = messageInput.value.trim();
        if (!content || !currentChatId) return;

        // 1. Limpa o input e desativa
        messageInput.value = '';
        messageInput.disabled = true;
        sendButton.disabled = true;

        // 2. Renderiza a mensagem do usuário imediatamente
        renderMessage({
            sender_role: 'user',
            content: content,
            created_at: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
        });
        
        // 3. Mostra o "Digitando..." da Amanda
        showAmandaTyping();

        try {
            // 4. Envia para a API
            // (fetchApi está em api.js)
            const aiResponse = await fetchApi('/chat/send', 'POST', {
                chat_id: currentChatId,
                content: content
            }, true);
            
            // 5. Remove o "Digitando..."
            hideAmandaTyping();
            
            // 6. Renderiza a resposta da Amanda
            // A API já retorna o JSON estruturado
            renderMessage({
                sender_role: 'amanda',
                content: JSON.stringify(aiResponse), // O renderizador espera a string JSON
                created_at: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
            });

        } catch (error) {
            // Se der erro (ex: moderação 403 ou erro 500)
            hideAmandaTyping();
            
            // A API de erro *também* envia um JSON estruturado
            renderMessage({
                sender_role: 'amanda',
                content: error.message, // O 'fetchApi' já extrai a msg de erro
                created_at: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
                is_error: true // Flag para estilização especial se quisermos
            });
        }

        // 7. Reativa o input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }

    /**
     * "Desenha" uma nova mensagem na tela.
     */
    function renderMessage(message) {
        // Remove o placeholder se for a primeira mensagem
        if (placeholder) placeholder.style.display = 'none';

        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${message.sender_role}`;
        
        // Se a mensagem for um erro
        if (message.is_error) {
            wrapper.innerHTML = `
                <div classT="message-bubble error">
                    <p><strong>Erro:</strong> ${message.content}</p>
                    <span class="message-timestamp">${message.created_at}</span>
                </div>`;
            messagesContainer.appendChild(wrapper);
            scrollToBottom();
            return;
        }

        // Se for uma mensagem normal do usuário
        if (message.sender_role === 'user') {
            wrapper.innerHTML = `
                <div class="message-bubble">
                    <p>${message.content}</p>
                    <span class="message-timestamp">${message.created_at}</span>
                </div>`;
        } 
        
        // Se for uma mensagem da Amanda (JSON Estruturado)
        if (message.sender_role === 'amanda') {
            try {
                // O backend envia o JSON como string
                const data = JSON.parse(message.content); 
                
                // Monta os botões de ação
                const actionsHTML = data.acoes_sugeridas.map(action => 
                    `<li><button class="btn-action">${action}</button></li>`
                ).join('');
                
                wrapper.innerHTML = `
                    <div class="message-bubble">
                        <div class="amanda-response">
                            <p>${data.mensagem_amanda}</p>
                            
                            <div class="amanda-analysis">
                                <strong>Resumo:</strong> ${data.resumo}<br>
                                <strong>Análise:</strong> ${data.analise}
                            </div>
                            
                            <div class="amanda-actions">
                                <strong>Próximos Passos:</strong>
                                <ul>${actionsHTML}</ul>
                            </div>
                            <span class="message-timestamp">${message.created_at}</span>
                        </div>
                    </div>`;
            } catch (e) {
                // Fallback se a resposta não for o JSON esperado
                // (Ex: a mensagem de bloqueio por moderação)
                 wrapper.innerHTML = `
                    <div class="message-bubble amanda-moderation">
                        <p>${message.content.replace(/\n/g, '<br>')}</p>
                        <span class="message-timestamp">${message.created_at}</span>
                    </div>`;
            }
        }
        
        messagesContainer.appendChild(wrapper);
        scrollToBottom(); // Rola para a nova mensagem
    }

    // --- 4. FUNÇÕES AUXILIARES ---

    function showAmandaTyping() {
        if ($('#amanda-typing')) return; // Já está visível
        
        const typingEl = document.createElement('div');
        typingEl.id = 'amanda-typing';
        typingEl.className = 'message-wrapper amanda';
        typingEl.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>`;
        messagesContainer.appendChild(typingEl);
        scrollToBottom();
    }

    function hideAmandaTyping() {
        const typingEl = $('#amanda-typing');
        if (typingEl) typingEl.remove();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function enableChatInput() {
        messageInput.disabled = false;
        sendButton.disabled = false;
        if(placeholder) placeholder.style.display = 'none';
        $('#btn-proposta-formal').style.display = 'block';
        $('#btn-chat-details').style.display = 'block';
    }

    // ----- Mockup para Teste (Remover em produção) -----
    // Simula a seleção de um chat para habilitar o input
    currentChatId = "mock-chat-123";
    enableChatInput();
    chatTitle.textContent = "Negociação Mockup #123";
    messagesContainer.innerHTML = ''; // Limpa o placeholder inicial
    // --------------------------------------------------

});