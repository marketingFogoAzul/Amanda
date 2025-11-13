// frontend/js/utils.js

/**
 * Funções utilitárias globais.
 */

/**
 * Atalho para querySelector, para facilitar.
 * @param {string} selector - O seletor CSS.
 * @returns {HTMLElement | null} O elemento.
 */
function $(selector) {
    return document.querySelector(selector);
}

/**
 * Atalho para querySelectorAll.
 * @param {string} selector - O seletor CSS.
 * @returns {NodeListOf<HTMLElement>} A lista de elementos.
 */
function $$(selector) {
    return document.querySelectorAll(selector);
}

/**
 * Obtém os dados do usuário logado do localStorage.
 * @returns {object | null} O objeto do usuário ou null.
 */
function getCurrentUser() {
    const user = localStorage.getItem('current_user');
    return user ? JSON.parse(user) : null;
}

/**
 * Obtém o token JWT do localStorage.
 * @returns {string | null} O token.
 */
function getToken() {
    return localStorage.getItem('jwt_token');
}

/**
 * Verifica se o usuário está autenticado.
 * @returns {boolean} True se houver token e dados do usuário.
 */
function isAuthenticated() {
    return getToken() && getCurrentUser();
}

/**
 * Formata um CNPJ (apenas para exibição, não valida).
 * @param {string} cnpj - CNPJ (limpo ou não).
 * @returns {string} CNPJ formatado (00.000.000/0000-00).
 */
function formatCnpj(cnpj) {
    if (!cnpj) return '';
    const cleaned = cnpj.replace(/\D/g, ''); // Remove tudo que não é dígito
    if (cleaned.length !== 14) return cnpj; // Retorna original se inválido
    
    return cleaned.replace(
        /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
        '$1.$2.$3/$4-$5'
    );
}

/**
 * Mostra uma mensagem de erro genérica.
 * @param {string} elementId - O ID do elemento de mensagem.
 * @param {string} message - A mensagem a ser exibida.
 */
function showMessage(elementId, message, type = 'error') {
    const el = $(`#${elementId}`);
    if (el) {
        el.textContent = message;
        el.className = type === 'error' ? 'error-message' : 'success-message';
        el.style.display = 'block';
    }
}

/**
 * Esconde uma mensagem.
 * @param {string} elementId - O ID do elemento de mensagem.
 */
function hideMessage(elementId) {
    const el = $(`#${elementId}`);
    if (el) {
        el.style.display = 'none';
    }
}