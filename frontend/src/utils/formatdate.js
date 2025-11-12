/**
 * Utilitário de formatação de data para garantir o padrão global do projeto ZIPBUM:
 * DD/MM/YYYY HH:MM:SS.
 */

/**
 * Adiciona um zero à esquerda se o número for menor que 10.
 * @param {number} value O valor numérico (dia, mês, hora, minuto, segundo).
 * @returns {string} O valor com zero à esquerda, se necessário.
 */
const padZero = (value) => {
    return value < 10 ? `0${value}` : value;
};

/**
 * Converte uma string de data, objeto Date ou timestamp ISO para o formato:
 * DD/MM/YYYY HH:MM:SS.
 * * * A função assume que o timestamp vindo da API já está em América/São Paulo,
 * * pois o backend (timezone_service.py) é responsável pela conversão do fuso.
 * * @param {string | Date | number} dateInput A data ou string de data a ser formatada.
 * @returns {string} A data formatada ou 'Data indisponível' em caso de erro.
 */
export const formatDateToBRStandard = (dateInput) => {
    if (!dateInput) {
        return 'Data indisponível';
    }

    // Se a entrada for uma string que JÁ ESTÁ no formato BR ('DD/MM/YYYY HH:MM:SS'), 
    // retorna para evitar conversões desnecessárias ou erros de fuso horário.
    if (typeof dateInput === 'string' && dateInput.match(/\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}/)) {
        return dateInput;
    }

    let date;

    try {
        date = new Date(dateInput);

        // Tentativa de correção para strings de data no formato DD/MM/YYYY (comum em JS/Browser)
        if (isNaN(date.getTime()) && typeof dateInput === 'string') {
            // Se for uma string de data sem hora (ex: '15/06/2025')
            const parts = dateInput.split('/');
            if (parts.length === 3) {
                // Tenta forçar o parse como YYYY-MM-DD para evitar inversão Mês/Dia
                date = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
            }
        }
        
        if (isNaN(date.getTime())) {
            return 'Data inválida';
        }
        
    } catch (error) {
        console.error("Erro ao parsear data:", error);
        return 'Erro de formatação';
    }

    // 🔨 Extrai componentes da data (usando métodos locais do objeto Date)
    const day = padZero(date.getDate());
    const month = padZero(date.getMonth() + 1); // Mês é 0-indexado
    const year = date.getFullYear();
    
    const hours = padZero(date.getHours());
    const minutes = padZero(date.getMinutes());
    const seconds = padZero(date.getSeconds());

    return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
};

/**
 * Retorna apenas o tempo decorrido (Ex: '5 minutos atrás').
 * * Nota: Esta função é um placeholder. No seu projeto, o tempo decorrido
 * * deve ser calculado no backend (ex: modelos/reports.py, evaluations.py) para
 * * garantir precisão de fuso horário, e enviado como um campo extra (tempo_decorrido).
 * @param {string | Date | number} dateInput 
 * @returns {string} Tempo decorrido (Ex: '2 horas atrás').
 */
export const timeAgo = (dateInput) => {
    return 'Tempo decorrido...'; 
};