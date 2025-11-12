import axios from 'axios';

// 🌐 Configuração da URL base do Backend Flask
// Em um ambiente real, esta URL viria de uma variável de ambiente (process.env.REACT_APP_API_URL)
const API_BASE_URL = 'http://localhost:5000/api'; 

/**
 * Instância do Axios pré-configurada para o Backend da Amanda AI.
 * Centraliza a gestão de tokens, a URL base e o tratamento de erros.
 */
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000, // Tempo limite de 15 segundos
    // Esta configuração é CRUCIAL para o Flask-Login funcionar, 
    // garantindo que os cookies de sessão sejam enviados e recebidos
    withCredentials: true, 
    headers: {
        'Content-Type': 'application/json',
    }
});

// 🔄 Interceptor de Request: Adiciona o token de autenticação (se usar JWT/Bearer)
api.interceptors.request.use(config => {
    // Se o projeto migrar para JWT, a lógica de token seria adicionada aqui
    return config;
}, error => {
    return Promise.reject(error);
});

// 🛑 Interceptor de Response: Trata erros globais (Ex: Sessão expirada)
api.interceptors.response.use(response => {
    return response;
}, error => {
    // 401 (Não Autorizado) -> Sessão expirada ou não logado.
    if (error.response && error.response.status === 401) {
        console.error("Sessão expirada ou não autenticada. Redirecionando para login.");
        
        // Em um sistema real, aqui você limparia o estado global e forçaria o redirecionamento:
        // window.location.href = '/login'; 
        
        // Cria uma nova instância de erro para que os componentes saibam do 401
        return Promise.reject(new Error(error.response.data.error || 'Não autenticado.'));
    }

    // 403 (Acesso Proibido) -> Permissão negada.
    if (error.response && error.response.status === 403) {
        console.error("Acesso negado por permissão.");
    }
    
    // Extrai a mensagem de erro da resposta da API do Flask (se existir)
    const errorMessage = error.response && error.response.data && (error.response.data.error || error.response.data.message)
                        ? (error.response.data.error || error.response.data.message)
                        : error.message;

    return Promise.reject(new Error(errorMessage));
});


// 📦 Exporta a instância para ser usada por todos os serviços do frontend
export default api;