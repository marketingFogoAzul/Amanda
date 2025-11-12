/** @type {import('tailwindcss').Config} */
module.exports = {
  // 🔍 Configura quais arquivos o Tailwind deve escanear para classes CSS
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  
  // 🌙 Define a estratégia de modo escuro. 'class' permite alternância via classe.
  // Como o projeto é "fundo escuro", 'media' pode ser usado, mas 'class' dá mais controle.
  darkMode: 'class', 
  
  theme: {
    extend: {
      // 🎨 Customização das Cores para o tema do projeto
      colors: {
        // Cores Primárias (Roxo/Purple da Amanda AI/ZIPBUM)
        // Usado para botões principais, links e foco
        'primary-brand': {
          '50': '#f8f4ff',
          '100': '#f3e8ff',
          '200': '#e9d5ff',
          '300': '#d8b4fe',
          '400': '#c084fc',
          '500': '#a855f7', // Roxo principal
          '600': '#9333ea',
          '700': '#7e22ce',
          '800': '#6b21a8',
          '900': '#581c87',
          '950': '#3b0b6d',
        },
        
        // Fundo Escuro Global (Consistente com o fundo do app.py e index.html)
        'dark-bg': '#111827', // Gray-900 ou mais escuro
        
        // Elementos de UI (para o fundo escuro)
        'dark-card': '#1f2937', // Gray-800
        'dark-border': '#374151', // Gray-700
        'dark-text': '#d1d5db', // Gray-300
      },
      
      // 📐 Customização de Fontes
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // Exemplo de fonte moderna
      },
      
      // 💨 Transições e Animações (Opcional, mas útil para o layout)
      transitionDuration: {
        '250': '250ms',
      },
    },
  },
  
  plugins: [
    // Plugins recomendados para React/Formulários
    require('@tailwindcss/forms'),
  ],
}