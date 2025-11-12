import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// 🔑 Contexto de Autenticação
import { AuthProvider, useAuth } from './utils/auth'; 

// 📱 Componentes de Layout
// Ajustado para minúsculo (seu estilo)
import Sidebar from './components/sidebar';
import LoginForm from './components/loginform'; 

// 🖥️ Páginas Principais
// Ajustado para minúsculo (seu estilo)
import Dashboard from './pages/dashboard';
import ImportPage from './pages/importpage';
import ReportPage from './pages/reportpage';
import AdminPanel from './pages/adminpanel';
import CompanyPanel from './components/companypanel'; 
import ChatWindow from './components/chatwindow'; 

/**
 * Rota protegida: Componente que verifica a autenticação antes de renderizar a página.
 */
const ProtectedRoute = ({ element: Element, ...rest }) => {
    const { isAuthenticated, loading } = useAuth();
    
    // Mostra um spinner enquanto a sessão está sendo verificada
    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-dark-bg text-white">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                <span className="ml-3">Verificando sessão...</span>
            </div>
        );
    }
    
    // Se autenticado, renderiza a página. Caso contrário, redireciona para o login.
    return isAuthenticated ? <Element {...rest} /> : <Navigate to="/login" replace />;
};

/**
 * Layout Principal: Aplica o Sidebar ao redor do conteúdo da página.
 */
const MainLayout = ({ children }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
    
    return (
        <div className="flex min-h-screen bg-dark-bg">
            <Sidebar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
            <main className={`flex-1 p-4 transition-all duration-300 ${isSidebarOpen ? 'ml-0 md:ml-0' : 'ml-0 md:ml-0'}`}>
                {children}
            </main>
        </div>
    );
};

/**
 * Componente principal da aplicação (App.jsx).
 * Configura o roteamento e o provedor de autenticação.
 */
const App = () => {
    // Nota: Os nomes dos componentes na rota (element) devem continuar com a primeira letra maiúscula
    // (ex: <Dashboard />), mas a importação (linha 11) reflete seu estilo.
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    {/* --- Rota de Autenticação --- */}
                    <Route path="/login" element={
                        <div className="flex items-center justify-center min-h-screen bg-dark-bg">
                            <LoginForm />
                        </div>
                    } />
                    
                    {/* Redirecionamento para o Dashboard como rota padrão */}
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />

                    {/* --- Rotas Protegidas (Exigem Login) --- */}
                    <Route 
                        path="/dashboard" 
                        element={<ProtectedRoute element={() => <MainLayout><Dashboard /></MainLayout>} />} 
                    />
                    
                    {/* Rotas de Chat */}
                    <Route 
                        path="/chat/:type" 
                        element={<ProtectedRoute element={() => <MainLayout><ChatWindow initialChatId={null} /></MainLayout>} />} 
                    />

                    {/* Rotas de Painéis */}
                    <Route 
                        path="/company-panel" 
                        element={<ProtectedRoute element={() => <MainLayout><CompanyPanel currentUser={useAuth().user} /></MainLayout>} />} 
                    />
                    <Route 
                        path="/admin-panel" 
                        element={<ProtectedRoute element={() => <MainLayout><AdminPanel /></MainLayout>} />} 
                    />

                    {/* Rotas de Funcionalidades */}
                    <Route 
                        path="/import" 
                        element={<ProtectedRoute element={() => <MainLayout><ImportPage /></MainLayout>} />} 
                    />
                    <Route 
                        path="/reports" 
                        element={<ProtectedRoute element={() => <MainLayout><ReportPage /></MainLayout>} />} 
                    />

                    {/* --- Tratamento de Rotas Não Encontradas --- */}
                    <Route path="*" element={
                        <div className="flex items-center justify-center h-screen bg-dark-bg text-white">
                            <h1 className="text-3xl text-red-500">404 - Página Não Encontrada</h1>
                        </div>
                    } />
                </Routes>
            </Router>
        </AuthProvider>
    );
};

export default App;