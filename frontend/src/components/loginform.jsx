import React, { useState } from 'react';
import api from '../utils/api'; // Conexão com a API

/**
 * Componente funcional para o formulário de Login.
 * Implementa a lógica de estado, validação básica e submissão para o backend.
 */
const LoginForm = () => {
    // 🔑 Estados do formulário
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [rememberMe, setRememberMe] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    // 🛡️ Lógica de validação simples
    const validateForm = () => {
        if (!email || !password) {
            setError('E-mail e senha são obrigatórios.');
            return false;
        }
        // Validação básica de formato de e-mail
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError('Por favor, insira um e-mail válido.');
            return false;
        }
        setError(null);
        return true;
    };

    // 🚀 Lógica de submissão do formulário
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        setLoading(true);
        setError(null);
        setSuccessMessage(null);

        // --- Chamada API para o Backend Flask (/auth/login) ---
        try {
            const response = await api.post('/auth/login', { 
                email, 
                password, 
                remember_me: rememberMe 
            });
            
            if (response.status === 200 && response.data.success) {
                setSuccessMessage(response.data.message + ' Redirecionando...');
                // Implementação real faria loginUser(response.data.user) e redirecionamento.
            } else {
                 // Esta parte pode não ser alcançada se o interceptor do Axios tratar erros 4xx
                setError(response.data.error || 'Erro desconhecido durante o login.');
            }

        } catch (err) {
            // Captura erros do Axios, incluindo a mensagem tratada no interceptor (ex: 401 Credenciais inválidas)
            console.error('Erro de login:', err.message);
            setError(err.message || 'Falha de conexão. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-form-container bg-gray-800 p-8 rounded-lg shadow-2xl w-full max-w-md">
            
            <div className="text-center mb-6">
                <h1 className="text-3xl font-bold text-white">
                    Amanda AI
                </h1>
                <p className="text-gray-400">Plataforma de Negociação ZIPBUM</p>
            </div>

            {/* Mensagem de Erro/Sucesso */}
            {error && (
                <div className="bg-red-500 text-white p-3 rounded mb-4 text-sm">
                    {error}
                </div>
            )}
            {successMessage && (
                <div className="bg-green-500 text-white p-3 rounded mb-4 text-sm">
                    {successMessage}
                </div>
            )}
            
            <form onSubmit={handleSubmit}>
                <div className="mb-4">
                    <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="email">
                        E-mail
                    </label>
                    <input
                        className="shadow appearance-none border border-gray-700 rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 transition duration-150"
                        id="email"
                        type="email"
                        placeholder="seu@email.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                
                <div className="mb-6">
                    <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="password">
                        Senha
                    </label>
                    <input
                        className="shadow appearance-none border border-gray-700 rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:ring-2 focus:ring-purple-500 transition duration-150"
                        id="password"
                        type="password"
                        placeholder="********"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>

                <div className="flex items-center justify-between mb-6">
                    <label className="flex items-center text-sm text-gray-300">
                        <input
                            type="checkbox"
                            className="form-checkbox h-4 w-4 text-purple-600 transition duration-150 ease-in-out bg-gray-700 border-gray-600 rounded"
                            checked={rememberMe}
                            onChange={(e) => setRememberMe(e.target.checked)}
                            disabled={loading}
                        />
                        <span className="ml-2">Lembrar de mim</span>
                    </label>
                    {/* Placeholder para link de 'Esqueceu a senha' */}
                    <a className="inline-block align-baseline font-bold text-sm text-purple-400 hover:text-purple-300 transition duration-150" href="#">
                        Esqueceu a senha?
                    </a>
                </div>

                <div className="flex flex-col items-center justify-center">
                    <button
                        className={`w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? 'Acessando...' : 'Fazer Login'}
                    </button>
                    
                    {/* Link para o cadastro */}
                    <p className="mt-4 text-sm text-gray-400">
                        Não tem uma conta? 
                        <a className="text-purple-400 hover:text-purple-300 ml-1 font-bold transition duration-150" href="#">
                            Cadastre-se
                        </a>
                    </p>
                </div>
                
                {/* 🤖 Placeholder para reCAPTCHA, conforme demanda */}
                <div className="mt-4 text-center text-xs text-gray-500">
                    (reCAPTCHA será verificado no envio)
                </div>

            </form>
        </div>
    );
};

export default LoginForm;