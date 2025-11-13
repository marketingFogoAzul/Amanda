// frontend/js/api.js

/**
 * Módulo de API para comunicação com o Backend Flask (Amanda AI - ZIPBUM).
 */

// A URL base da sua API Flask (deve ser a mesma do app.py/server_config.py)
const API_BASE_URL = 'http://127.0.0.1:5000/api'; 

/**
 * Retorna o token JWT salvo no localStorage.
 * @returns {string | null} O token JWT.
 */
function getToken() {
    return localStorage.getItem('jwt_token');
}

/**
 * Função principal para realizar requisições à API.
 * Lida automaticamente com a adição do Token de Autorização
 * e com a formatação de JSON.
 *
 * @param {string} endpoint O caminho da API (ex: '/auth/login').
 * @param {string} method O método HTTP (GET, POST, PUT, etc.).
 * @param {object | null} body O corpo da requisição (para POST/PUT).
 * @param {boolean} requiresAuth Se a rota exige um token JWT.
 * @returns {Promise<object>} Os dados da resposta (JSON).
 */
async function fetchApi(endpoint, method = 'GET', body = null, requiresAuth = false) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers = new Headers();
    headers.append('Content-Type', 'application/json');

    // Adiciona o token JWT se a rota exigir
    if (requiresAuth) {
        const token = getToken();
        if (!token) {
            console.error('API Error: Token não encontrado, mas é necessário.');
            // Se o token sumir, força o logout
            window.location.href = 'login.html';
            throw new Error('Token de autenticação não encontrado.');
        }
        headers.append('Authorization', `Bearer ${token}`);
    }

    const config = {
        method: method,
        headers: headers,
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, config);

        // Tenta pegar o JSON mesmo se a resposta for um erro (ex: 400, 401)
        // O backend envia um JSON de erro (ex: {"error": "..."})
        const responseData = await response.json();

        if (!response.ok) {
            // Se o servidor retornou um erro (4xx, 5xx),
            // a 'responseData' conterá a mensagem de erro.
            console.error(`API Error ${response.status}:`, responseData.error || response.statusText);
            // Lança o erro para o .catch() da chamada original
            throw new Error(responseData.error || `Erro ${response.status}`);
        }

        // Se a resposta for OK (2xx), retorna os dados
        return responseData;

    } catch (error) {
        // Pega erros de rede (fetch falhou) ou erros lançados acima
        console.error('Falha na requisição API:', error.message);
        // Re-lança o erro para a função que chamou (ex: auth.js)
        throw error;
    }
}