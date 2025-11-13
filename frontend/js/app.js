// frontend/js/app.js

/**
 * Script principal da aplicação (para páginas internas).
 * Lida com a inicialização da página, autenticação e UI global.
 */

// Chave da API do reCAPTCHA (para o 'auth.js' usar)
// Substitua pela sua Chave de SITE
const RECAPTCHA_SITE_KEY = '6LfhuAssAAAAAI3GfXs_5vif4Uq9d8dj_UAayXvV';

// Executa o script quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Ativa os Ícones (Feather Icons)
    // (A tag <script> do feather.js precisa estar no HTML)
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // 2. Verifica a Autenticação
    // Esta é a principal proteção de rota do frontend
    // O 'auth.js' é para as páginas de login/registro.
    // O 'app.js' é para o resto da app.
    
    const isAuthPage = window.location.pathname.endsWith('login.html') || 
                       window.location.pathname.endsWith('register.html') ||
                       window.location.pathname.endsWith('index.html') ||
                       window.location.pathname === '/'; // Protege a raiz

    if (!isAuthPage) {
        // Se NÃO estamos na página de login/registro/index
        if (!isAuthenticated()) {
            // Se o usuário NÃO está logado, chuta para o login
            console.warn('Usuário não autenticado. Redirecionando para /login.html');
            window.location.href = 'login.html';
            return; // Para a execução
        }
        
        // Se está logado, popula a UI
        populateUserUI();
        setupSidebarMenu();
        setupLogout();

    } else if (window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('register.html')) {
        // Se ESTAMOS na página de login/registro
        if (isAuthenticated()) {
            // E o usuário JÁ está logado, chuta para o dashboard
            console.log('Usuário já autenticado. Redirecionando para /dashboard.html');
            window.location.href = 'dashboard.html';
        }
    }
});

/**
 * Preenche a barra lateral com os dados do usuário.
 */
function populateUserUI() {
    const user = getCurrentUser(); // (Função do utils.js)
    if (!user) return;

    if ($('#user-full-name')) {
        $('#user-full-name').textContent = user.full_name;
    }
    if ($('#welcome-user-name')) {
        $('#welcome-user-name').textContent = user.full_name.split(' ')[0]; // Só o primeiro nome
    }
    if ($('#user-role-name')) {
        $('#user-role-name').textContent = user.role;
    }
    
    // (Opcional) Carregar avatar
    // if ($('#user-avatar')) { ... }
}

/**
 * Configura a visibilidade dos itens de menu com base no cargo (role).
 */
function setupSidebarMenu() {
    const user = getCurrentUser();
    if (!user || user.role_level === null) return;

    const level = user.role_level; // Nível 0-7

    // Esconde todos os itens de menu baseados em cargo
    $$('.role-item').forEach(item => {
        item.style.display = 'none';
    });

    // Mostra os itens que o usuário tem permissão
    // Ex: <li class="menu-item role-item role-0 role-1">
    // O seletor CSS `.role-0` (ou .role-1 etc.) é o que faz a mágica
    $$(`.role-${level}`).forEach(item => {
        item.style.display = 'block';
    });
}

/**
 * Adiciona o evento de clique no botão "Sair" (Logout).
 */
function setupLogout() {
    const logoutButton = $('#logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            // Limpa o localStorage
            localStorage.removeItem('jwt_token');
            localStorage.removeItem('current_user');
            
            // Redireciona para o login
            window.location.href = 'login.html';
        });
    }
}