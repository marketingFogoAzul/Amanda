import React, { useState } from 'react';
import { X, Star, Loader } from 'react-feather';
import api from '../utils/api'; // Serviço de API

/**
 * Componente Modal para Avaliação do Chat.
 * Exibido após o cliente fechar uma negociação.
 * * Baseado no modelo Avaliacao: nota, comentario, atendimento_rapido, proposta_justa, etc.
 */
const EvaluationModal = ({ chatId, onClose, onComplete }) => {
    // 🔑 Estados do Formulário
    const [rating, setRating] = useState(0); // Nota de 1 a 5
    const [comment, setComment] = useState('');
    const [categories, setCategories] = useState({
        atendimento_rapido: false,
        proposta_justa: false,
        comunicacao_clara: false,
        resolucao_eficaz: false,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [submitted, setSubmitted] = useState(false);

    // 🏷️ Categorias de Avaliação (visíveis na UI)
    const categoryOptions = [
        { key: 'atendimento_rapido', label: 'Atendimento Rápido' },
        { key: 'proposta_justa', label: 'Proposta Justa' },
        { key: 'comunicacao_clara', label: 'Comunicação Clara' },
        { key: 'resolucao_eficaz', label: 'Resolução Eficaz' },
    ];

    // 📝 Altera o estado de uma categoria
    const handleCategoryChange = (key) => {
        setCategories(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    // 🚀 Lógica de submissão
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (rating === 0) {
            setError('Por favor, atribua uma nota de 1 a 5 estrelas.');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Chamada à API para registrar a avaliação
            const payload = {
                rating: rating,
                comment: comment,
                categories: categories,
            };
            
            const response = await api.post(`/chat/${chatId}/evaluate`, payload);
            
            if (response.data.success) {
                setSubmitted(true);
                // Chama a função onComplete após 1.5s para dar tempo de exibir a mensagem
                setTimeout(() => {
                    onComplete(); 
                    onClose();
                }, 1500); 
            } else {
                setError(response.data.error || 'Erro ao registrar avaliação.');
            }

        } catch (err) {
            console.error('Erro ao enviar avaliação:', err);
            setError(err.message || 'Falha de conexão. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <ModalWrapper onClose={onClose}>
                <div className="text-center p-8">
                    <Star size={48} className="text-yellow-400 mx-auto mb-4" />
                    <h3 className="text-2xl font-bold text-white mb-2">Avaliação Registrada!</h3>
                    <p className="text-gray-400">Obrigado pelo seu feedback. Sua opinião é crucial para aprimorarmos a Amanda AI e a ZIPBUM.</p>
                </div>
            </ModalWrapper>
        );
    }

    return (
        <ModalWrapper onClose={onClose}>
            <div className="p-6">
                <h3 className="text-xl font-bold text-white mb-2 border-b border-gray-700 pb-2">
                    Avalie Sua Negociação
                </h3>
                <p className="text-gray-400 text-sm mb-4">
                    Ajude-nos a melhorar a Amanda AI. Sua nota deve ser sobre a experiência de negociação.
                </p>

                <form onSubmit={handleSubmit}>
                    {/* --- 1. Seleção de Nota (Estrelas) --- */}
                    <div className="mb-6">
                        <label className="block text-gray-300 font-semibold mb-2">Sua Nota (1 a 5)</label>
                        <div className="flex justify-center space-x-2">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <Star
                                    key={star}
                                    size={32}
                                    className={`cursor-pointer transition duration-150 ${
                                        rating >= star ? 'text-yellow-400 fill-current' : 'text-gray-600 hover:text-yellow-300'
                                    }`}
                                    onClick={() => setRating(star)}
                                />
                            ))}
                        </div>
                    </div>

                    {/* --- 2. Categorias de Satisfação --- */}
                    <div className="mb-6">
                        <label className="block text-gray-300 font-semibold mb-2">O que você mais gostou?</label>
                        <div className="flex flex-wrap gap-2">
                            {categoryOptions.map(option => (
                                <button
                                    key={option.key}
                                    type="button"
                                    onClick={() => handleCategoryChange(option.key)}
                                    className={`px-3 py-1.5 text-sm rounded-full transition duration-150 ${
                                        categories[option.key]
                                            ? 'bg-purple-600 text-white border-purple-400'
                                            : 'bg-gray-800 text-gray-400 border border-gray-600 hover:bg-gray-700'
                                    }`}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>
                    
                    {/* --- 3. Comentário Opcional --- */}
                    <div className="mb-6">
                        <label className="block text-gray-300 font-semibold mb-2" htmlFor="comment">
                            Comentário (Opcional)
                        </label>
                        <textarea
                            id="comment"
                            rows="3"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            className="w-full p-3 bg-gray-800 border border-gray-700 rounded text-white focus:ring-purple-500 focus:border-purple-500 transition duration-150"
                            placeholder="Sinta-se à vontade para detalhar sua experiência..."
                        />
                    </div>

                    {/* Mensagem de Erro */}
                    {error && (
                        <div className="bg-red-500/20 text-red-400 p-3 rounded mb-4 text-sm text-center">
                            {error}
                        </div>
                    )}

                    {/* --- Botões de Ação --- */}
                    <div className="flex justify-end space-x-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-semibold rounded-lg bg-gray-600 text-white hover:bg-gray-700 transition duration-150"
                            disabled={loading}
                        >
                            Fechar / Deixar para Depois
                        </button>
                        <button
                            type="submit"
                            className={`px-4 py-2 text-sm font-semibold rounded-lg text-white transition duration-150 flex items-center ${
                                loading ? 'bg-purple-800 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'
                            }`}
                            disabled={loading || rating === 0}
                        >
                            {loading && <Loader size={16} className="animate-spin mr-2" />}
                            {loading ? 'Enviando...' : 'Enviar Avaliação'}
                        </button>
                    </div>
                </form>
            </div>
        </ModalWrapper>
    );
};

// --- Wrapper para o Modal ---
const ModalWrapper = ({ children, onClose }) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm transition-opacity">
        <div className="relative bg-gray-900 rounded-xl shadow-2xl w-full max-w-lg mx-4 border border-purple-800/50 transform transition-all duration-300 scale-100 opacity-100">
            {/* Botão de Fechar */}
            <button
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-white transition duration-150"
            >
                <X size={24} />
            </button>
            {children}
        </div>
    </div>
);

export default EvaluationModal;