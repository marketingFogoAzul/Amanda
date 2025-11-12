import React, { useState } from 'react';
import { Menu, X, MessageSquare, PlusSquare, Clock, LogOut, User, Settings, Layers, Briefcase, ChevronDown, ChevronRight } from 'react-feather';
import { useNavigate } from 'react-router-dom'; 
import api from '../utils/api'; 
// import { useAuth } from '../utils/auth'; // Contexto de autenticação para pegar o usuário e o logout

/**
 * Componente funcional para a Barra Lateral (Sidebar).
 * Contém a navegação, o perfil do usuário e o menu de ações.
 */
const Sidebar = ({ isSidebarOpen, toggleSidebar }) => {
    // ⚙️ Simulação de dados do usuário logado (Em produção, viria do useAuth)
    const mockCurrentUser = {
        nome_completo: 'Gabriel Oliveira',
        email: 'gabriel.oliver@zipbum.com',
        cargo: 4, // Exemplo: 4 (Representante)
        nome_cargo: 'Representante',
        foto_url: 'https://i.pravatar.cc/150?img=1' // URL mock
    };

    // Estados
    const navigate = useNavigate();
    const [user, setUser] = useState(mockCurrentUser); // Usaria useAuth().user
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isSubMenuOpen, setIsSubMenuOpen] = useState(false);
    
    // Permissões
    const isClient = user.cargo >= 6; // Cliente Pro ou Básico
    const isAdmin = user.cargo <= 3; // Dev, Junior, Marketing, Helper
    const isCompanyUser = user.cargo >= 4 && user.cargo <= 5; // Representante, Vendedor

    // 🚪 Simulação da função de Logout (Em produção, usaria useAuth().logout)
    const handleLogout = async () => {
        if (window.confirm('Tem certeza que deseja sair?')) {
            try {
                // await api.post('/auth/logout');
                // Redireciona para login
                // navigate('/login'); 
                console.log('Logout realizado com sucesso. (Simulado)');
                // navigate('/login'); 
            } catch (error) {
                console.error('Erro ao fazer logout:', error.message);
            }
        }
    };

    // ⚙️ Função para navegar
    const handleNavigation = (path) => {
        navigate(path);
        setIsMenuOpen(false);
        // Fecha a sidebar em telas pequenas
        if (window.innerWidth < 768) {
             toggleSidebar();
        }
    };

    // 📋 Item de navegação genérico
    const NavItem = ({ icon: Icon, label, path, requiresAdmin = false, requiresCompany = false }) => {
        
        if (requiresAdmin && !isAdmin) return null;
        if (requiresCompany && !isCompanyUser) return null;
        
        return (
            <li 
                className="py-2 px-4 flex items-center text-sm font-medium text-gray-300 hover:bg-gray-700 rounded-lg cursor-pointer transition duration-150"
                onClick={() => handleNavigation(path)}
            >
                <Icon size={20} className="mr-3" />
                <span className={`${isSidebarOpen ? 'block' : 'hidden'}`}>{label}</span>
            </li>
        );
    };

    return (
        <>
            {/* 1. Botão de Toggle (Apenas em telas pequenas) */}
            <div className="md:hidden p-4 fixed top-0 left-0 z-40">
                <button onClick={toggleSidebar} className="text-white">
                    {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* 2. Sidebar Principal */}
            <aside 
                className={`fixed inset-y-0 left-0 z-30 transform ${isSidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full w-20 md:translate-x-0'} 
                bg-gray-900 border-r border-gray-700 transition-width duration-300 ease-in-out md:static md:flex-shrink-0 md:h-screen`}
            >
                <div className="flex flex-col h-full p-4">
                    
                    {/* --- Logo e Toggle --- */}
                    <div className={`flex items-center justify-between h-16 ${isSidebarOpen ? 'mb-8' : 'mb-8 justify-center'}`}>
                        <h1 className={`text-xl font-extrabold text-primary-brand-400 ${isSidebarOpen ? 'block' : 'hidden'}`}>
                            AMANDA AI
                        </h1>
                        <button onClick={toggleSidebar} className="text-gray-400 hover:text-white hidden md:block transition duration-150">
                            {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                        </button>
                    </div>

                    {/* --- Navegação Principal --- */}
                    <nav className="flex-1 overflow-y-auto">
                        <ul className="space-y-2">
                            <NavItem icon={PlusSquare} label="Nova Negociação" path="/chat/new" />
                            <NavItem icon={MessageSquare} label="Histórico de Chats" path="/chat/history" />
                            
                            {/* Linha Divisória */}
                            <li className="py-2"><hr className="border-gray-700" /></li>
                            
                            {/* Painéis Dinâmicos */}
                            <NavItem icon={Briefcase} label="Painel da Empresa" path="/company-panel" requiresCompany={true} />
                            <NavItem icon={Layers} label="Painel ZIPBUM (Admin)" path="/admin-panel" requiresAdmin={true} />
                        </ul>
                    </nav>

                    {/* --- Área de Perfil e Menu do Usuário (Rodapé) --- */}
                    <div className="mt-auto pt-4 border-t border-gray-700 relative">
                        
                        {/* 👤 Info do Usuário */}
                        <div 
                            className={`flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-800 transition duration-150 ${isSidebarOpen ? 'justify-between' : 'justify-center'}`}
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >
                            <div className="flex items-center">
                                <img 
                                    src={user.foto_url} 
                                    alt={user.nome_completo} 
                                    className={`w-8 h-8 rounded-full ${isSidebarOpen ? 'mr-3' : 'hidden md:block'}`}
                                />
                                <div className={`${isSidebarOpen ? 'block' : 'hidden'}`}>
                                    <p className="text-sm font-semibold text-white">{user.nome_completo.split(' ')[0]}</p>
                                    <p className="text-xs text-primary-brand-300">{user.nome_cargo}</p>
                                </div>
                            </div>
                            
                            <div className={`text-gray-400 ${isSidebarOpen ? 'block' : 'hidden'}`}>
                                {isMenuOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            </div>
                        </div>

                        {/* --- Mini-Menu de Ações (Abre ao clicar na foto/nome) --- */}
                        {isMenuOpen && (
                            <div className="absolute bottom-full left-0 mb-2 w-full bg-gray-800 rounded-xl shadow-2xl p-3 border border-gray-700 z-40">
                                <p className="text-xs font-bold text-gray-500 mb-2 border-b border-gray-700 pb-1">
                                    {user.nome_completo}
                                </p>
                                
                                <ul className="space-y-1 text-sm">
                                    {/* Mudar Localização */}
                                    <li 
                                        className="py-1 px-2 flex justify-between items-center text-gray-300 hover:bg-gray-700 rounded-md cursor-pointer transition duration-150"
                                        onClick={() => setIsSubMenuOpen(!isSubMenuOpen)}
                                    >
                                        <span className='flex items-center'><User size={16} className="mr-2" />Mudar Localização</span>
                                        {isSubMenuOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                    </li>

                                    {/* Sub-Menu de Localização (Abre e fecha com a div) */}
                                    {isSubMenuOpen && (
                                        <div className="pl-4 pt-1 pb-1 text-xs space-y-1 bg-gray-700 rounded-md">
                                            <a href="#" className="block text-gray-400 hover:text-white">Gerenciar Endereço</a>
                                            <a href="#" className="block text-gray-400 hover:text-white">Selecionar UF</a>
                                        </div>
                                    )}

                                    {/* Gerenciar Plano */}
                                    <li 
                                        className="py-1 px-2 flex items-center text-gray-300 hover:bg-gray-700 rounded-md cursor-pointer transition duration-150"
                                        onClick={() => alert('Gerenciar plano: Indisponível - contate vendas')}
                                    >
                                        <Clock size={16} className="mr-2" />
                                        Gerenciar Plano
                                    </li>

                                    {/* Acessar Painéis (Se não for link direto no nav) */}
                                    {isCompanyUser && (
                                        <li 
                                            className="py-1 px-2 flex items-center text-gray-300 hover:bg-gray-700 rounded-md cursor-pointer transition duration-150"
                                            onClick={() => handleNavigation('/company-panel')}
                                        >
                                            <Briefcase size={16} className="mr-2" />
                                            Meu Painel
                                        </li>
                                    )}

                                    {/* Logout */}
                                    <li 
                                        className="py-1 px-2 flex items-center text-red-400 hover:bg-red-900/50 rounded-md cursor-pointer transition duration-150 mt-2"
                                        onClick={handleLogout}
                                    >
                                        <LogOut size={16} className="mr-2" />
                                        Sair da Conta
                                    </li>
                                </ul>
                            </div>
                        )}
                        
                    </div>
                </div>
            </aside>
            
            {/* 3. Overlay (Fecha sidebar ao clicar fora em telas pequenas) */}
            {isSidebarOpen && (
                <div className="fixed inset-0 bg-black opacity-50 z-20 md:hidden" onClick={toggleSidebar}></div>
            )}
        </>
    );
};

export default Sidebar;