import React, { createContext, useContext, useState, useEffect } from 'react';
import api from './api'; // Importa a instância Axios configurada

/**
 * Contexto de Autenticação para gerenciar o estado do usuário (logado/deslogado).
 */
const AuthContext = createContext();

/**
 * Provedor de Autenticação (AuthProvider).
 * Centraliza o estado do usuário, funções de login/logout e verifica a sessão ao iniciar.
 */
export const AuthProvider = ({ children }) => {
    // 🔑 Estado do usuário logado
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true); // Indica se a verificação inicial está em andamento

    useEffect(() => {
        // 🔄 Verifica a sessão ao carregar o aplicativo
        checkUserSession();
    }, []);

    // 📞 Verifica se há uma sessão Flask-Login ativa
    const checkUserSession = async () => {
        try {
            // O endpoint 'check-session' deve retornar o perfil do usuário se estiver autenticado (auth_routes.py)
            const response = await api.get('/auth/check-session');
            if (response.data.authenticated) {
                setUser(response.data.user);
            } else {
                setUser(null);
            }
        } catch (error) {
            // Se houver erro (ex: 500, falha de rede), assume-se que não está logado
            console.error('Falha ao verificar sessão:', error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    // 🔑 Função de Login: Chamada após uma submissão bem-sucedida do formulário
    const login = async (userData) => {
        // Assume que o userData já vem validado e é a resposta da API Flask /auth/login
        setUser(userData);
        // Redirecionamento deve ser feito no componente que chama esta função (ex: LoginForm)
        return true;
    };

    // 🚪 Função de Logout
    const logout = async () => {
        setLoading(true);
        try {
            // Chama o endpoint de logout do Flask para limpar a sessão do lado do servidor
            await api.post('/auth/logout');
        } catch (error) {
            console.error('Erro ao fazer logout no servidor:', error);
        } finally {
            setUser(null);
            setLoading(false);
            // Redirecionamento deve ser feito após a chamada desta função
        }
    };

    // 👥 Função para atualizar o perfil (ex: após mudar endereço ou cargo via Admin)
    const updateProfile = (newUserData) => {
        setUser(prevUser => ({
            ...prevUser,
            ...newUserData
        }));
    };

    // 📦 Valores expostos pelo contexto
    const contextValue = {
        user,
        isAuthenticated: !!user,
        loading,
        login,
        logout,
        updateProfile,
    };

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

/**
 * Hook customizado para fácil acesso ao contexto de autenticação.
 */
export const useAuth = () => {
    return useContext(AuthContext);
};