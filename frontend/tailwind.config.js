/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Arch-Tech Precision 主题色彩
        // Action: Zinc 900
        action: {
          DEFAULT: '#18181B',
        },
        // Highlight: Orange 600
        highlight: {
          DEFAULT: '#EA580C',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

