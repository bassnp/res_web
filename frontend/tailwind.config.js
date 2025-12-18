/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
      './pages/**/*.{js,jsx}',
      './components/**/*.{js,jsx}',
      './app/**/*.{js,jsx}',
      './src/**/*.{js,jsx}',
    ],
    /**
     * Safelist for dynamically constructed class names in Experience Timeline.
     * Tailwind cannot detect classes built with template literals at build time.
     */
    safelist: [
      // Timeline node backgrounds
      'bg-burnt-peach', 'bg-muted-teal', 'bg-apricot',
      // Timeline badge backgrounds with opacity
      'bg-burnt-peach/90', 'bg-muted-teal/90', 'bg-apricot/90',
      // Timeline connecting line gradients
      'from-burnt-peach', 'from-muted-teal', 'from-apricot',
      'to-burnt-peach', 'to-muted-teal', 'to-apricot',
      'from-burnt-peach/60', 'from-muted-teal/60', 'from-apricot/60',
      'to-burnt-peach/60', 'to-muted-teal/60', 'to-apricot/60',
      // Timeline text colors
      'text-burnt-peach', 'text-muted-teal', 'text-apricot',
      // Timeline hover colors
      'hover:bg-burnt-peach', 'hover:bg-muted-teal', 'hover:bg-apricot',
      'group-hover:text-burnt-peach', 'group-hover:text-muted-teal', 'group-hover:text-apricot',
      'hover:border-burnt-peach/50', 'hover:border-muted-teal/50', 'hover:border-apricot/50',
      'border-burnt-peach/20', 'border-muted-teal/20', 'border-apricot/20',
    ],
    prefix: "",
    theme: {
        container: {
            center: true,
            padding: '2rem',
            screens: {
                '2xl': '1400px'
            }
        },
        extend: {
            colors: {
                'eggshell': '#f4f1de',
                'burnt-peach': '#e07a5f',
                'twilight': '#3d405b',
                'muted-teal': '#81b29a',
                'apricot': '#f2cc8f',
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' }
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' }
                },
                'fade-in': {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' }
                },
                'fade-in-left': {
                    '0%': { opacity: '0', transform: 'translateX(-30px)' },
                    '100%': { opacity: '1', transform: 'translateX(0)' }
                },
                'fade-in-right': {
                    '0%': { opacity: '0', transform: 'translateX(30px)' },
                    '100%': { opacity: '1', transform: 'translateX(0)' }
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
                    '50%': { transform: 'translateY(-20px) rotate(5deg)' }
                },
                'float-delayed': {
                    '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
                    '50%': { transform: 'translateY(-15px) rotate(-5deg)' }
                },
                'pulse-glow': {
                    '0%, 100%': { boxShadow: '0 0 20px rgba(224, 122, 95, 0.3)' },
                    '50%': { boxShadow: '0 0 40px rgba(224, 122, 95, 0.6)' }
                },
                'gradient-shift': {
                    '0%, 100%': { backgroundPosition: '0% 50%' },
                    '50%': { backgroundPosition: '100% 50%' }
                },
                'typing': {
                    '0%': { width: '0' },
                    '100%': { width: '100%' }
                },
                'blink': {
                    '0%, 100%': { borderColor: 'transparent' },
                    '50%': { borderColor: '#e07a5f' }
                },
                'scale-in': {
                    '0%': { opacity: '0', transform: 'scale(0.9)' },
                    '100%': { opacity: '1', transform: 'scale(1)' }
                },
                'scale-in-no-transform': {
                    '0%': { opacity: '0', transform: 'scale(0.9)' },
                    '100%': { opacity: '1' }
                },
                'slide-up': {
                    '0%': { opacity: '0', transform: 'translateY(100px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' }
                },
                'rotate-slow': {
                    '0%': { transform: 'rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg)' }
                },
                'morph': {
                    '0%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%', transform: 'rotate(0deg) scale(1)' },
                    '5%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%', transform: 'rotate(0deg) scale(1)' },
                    '25%': { borderRadius: '40% 60% 50% 50% / 30% 70% 30% 70%', transform: 'rotate(5deg) scale(1.05)' },
                    '30%': { borderRadius: '40% 60% 50% 50% / 30% 70% 30% 70%', transform: 'rotate(5deg) scale(1.05)' },
                    '50%': { borderRadius: '30% 60% 70% 40% / 50% 60% 30% 60%', transform: 'rotate(0deg) scale(1.1)' },
                    '55%': { borderRadius: '30% 60% 70% 40% / 50% 60% 30% 60%', transform: 'rotate(0deg) scale(1.1)' },
                    '75%': { borderRadius: '50% 50% 60% 40% / 70% 30% 70% 30%', transform: 'rotate(-5deg) scale(1.05)' },
                    '80%': { borderRadius: '50% 50% 60% 40% / 70% 30% 70% 30%', transform: 'rotate(-5deg) scale(1.05)' },
                    '100%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%', transform: 'rotate(0deg) scale(1)' }
                },
                'shimmer': {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' }
                },
                'bounce-soft': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-5px)' }
                },
                'bounce-slow': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-25%)' }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'fade-in': 'fade-in 0.6s ease-out forwards',
                'fade-in-left': 'fade-in-left 0.6s ease-out forwards',
                'fade-in-right': 'fade-in-right 0.6s ease-out forwards',
                'float': 'float 6s ease-in-out infinite',
                'float-delayed': 'float-delayed 8s ease-in-out infinite',
                'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
                'gradient-shift': 'gradient-shift 4s ease infinite',
                'typing': 'typing 2s steps(20) forwards',
                'blink': 'blink 1s step-end infinite',
                'scale-in': 'scale-in 0.5s ease-out forwards',
                'scale-in-no-transform': 'scale-in-no-transform 0.5s ease-out forwards',
                'slide-up': 'slide-up 0.8s ease-out forwards',
                'rotate-slow': 'rotate-slow 20s linear infinite',
                'morph': 'morph 10s ease-in-out infinite',
                'morph-fast': 'morph 3.75s ease-in-out infinite',
                'shimmer': 'shimmer 2s linear infinite',
                'bounce-soft': 'bounce-soft 2s ease-in-out infinite',
                'bounce-slow': 'bounce-slow 1.2s ease-in-out infinite'
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
}
