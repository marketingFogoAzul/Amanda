// frontend/js/auth.js

/**
 * Lida com a lógica das páginas de Login e Registro.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Roteamento: decide qual formulário inicializar
    if ($('#login-form')) {
        initLoginPage();
    }
    
    if ($('#register-form')) {
        initRegisterPage();
    }
});

// --- LÓGICA DE LOGIN ---
function initLoginPage() {
    const loginForm = $('#login-form');
    const loginButton = $('#login-button');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Impede o envio padrão do form
        
        // Pega os dados
        const email = $('#email').value;
        const password = $('#password').value;
        
        // Desativa o botão para evitar cliques duplos
        loginButton.disabled = true;
        loginButton.textContent = 'Aguarde...';
        hideMessage('error-message');

        try {
            // Chama a API (definida em api.js)
            const data = await fetchApi('/auth/login', 'POST', { email, password }, false);
            
            // Sucesso!
            handleAuthSuccess(data);

        } catch (error) {
            // Mostra a mensagem de erro (vinda do backend)
            showMessage('error-message', error.message);
            
            // Reativa o botão
            loginButton.disabled = false;
            loginButton.textContent = 'Entrar';
        }
    });
}

// --- LÓGICA DE REGISTRO ---
function initRegisterPage() {
    const registerForm = $('#register-form');
    const registerButton = $('#register-button');

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        registerButton.disabled = true;
        registerButton.textContent = 'Registrando...';
        hideMessage('error-message');
        hideMessage('success-message');
        
        // 1. Gerar o token reCAPTCHA
        grecaptcha.ready(async () => {
            try {
                // (RECAPTCHA_SITE_KEY é definido em app.js)
                const token = await grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: 'register' });
                $('#recaptcha_token').value = token;
                
                // 2. Coletar dados do formulário
                const formData = {
                    full_name: $('#full_name').value,
                    email: $('#email').value,
                    password: $('#password').value,
                    cnpj: $('#cnpj').value,
                    razao_social: $('#razao_social').value,
                    uf: $('#uf').value.toUpperCase(),
                    cidade: $('#cidade').value,
                    recaptcha_token: token
                };
                
                // 3. Enviar para a API de registro
                // (O 'fetchApi' está em api.js)
                await fetchApi('/auth/register', 'POST', formData, false);

                // 4. Se o registro funcionou (201), tenta fazer login
                showMessage('success-message', 'Registro concluído! Fazendo login...');
                
                const loginData = await fetchApi('/auth/login', 'POST', {
                    email: formData.email,
                    password: formData.password
                }, false);
                
                // 5. Sucesso!
                handleAuthSuccess(loginData);

            } catch (error) {
                // Erro (do registro ou do login)
                showMessage('error-message', error.message);
                registerButton.disabled = false;
                registerButton.textContent = 'Registrar e Acessar';
            }
        });
    });
}

/**
 * Função chamada após um Login ou Registro bem-sucedido.
 * @param {object} data - A resposta da API (/auth/login).
 */
function handleAuthSuccess(data) {
    // 1. Salva o token e os dados do usuário no localStorage
    localStorage.setItem('jwt_token', data.access_token);
    
    // O backend envia o objeto 'user' no login
    localStorage.setItem('current_user', JSON.stringify(data.user)); 

    // 2. Redireciona para o dashboard
    window.location.href = 'dashboard.html';
}