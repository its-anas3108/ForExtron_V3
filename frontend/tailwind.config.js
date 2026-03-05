/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            colors: {
                bg: {
                    primary: '#F8FAFC',
                    secondary: '#F1F5F9',
                    card: '#FFFFFF',
                    hover: '#E2E8F0',
                },
                accent: {
                    green: '#059669',
                    red: '#DC2626',
                    blue: '#2563EB',
                    gold: '#D97706',
                    purple: '#7C3AED',
                },
                text: {
                    primary: '#0F172A',
                    secondary: '#475569',
                    muted: '#94A3B8',
                },
                regime: {
                    accumulation: '#D97706',
                    expansion: '#059669',
                    exhaustion: '#DC2626',
                    anomaly: '#7C3AED',
                },
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.4s ease-out',
                'glow': 'glow 2s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
                slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
                glow: { '0%, 100%': { boxShadow: '0 0 5px rgba(5, 150, 105, 0.2)' }, '50%': { boxShadow: '0 0 20px rgba(5, 150, 105, 0.4)' } },
            },
            backdropBlur: { xs: '2px' },
        },
    },
    plugins: [],
}
