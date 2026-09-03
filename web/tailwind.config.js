/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Palette sampled from naturebasedsolutions.org
        wb: {
          blue:   '#71AAD7',
          blueDk: '#3E7CAB',
          green:  '#7FA23A',
          greenDk:'#5C7A22',
          yellow: '#F5D108',
          slate:  '#4D5C69',
          slateDk:'#2E3944',
          muted:  '#8EA0AF',
          ink:    '#333333',
          line:   '#E2E8EC',
          wash:   '#F5F7F9',
        },
        act: {
          protect: '#2E7D5B',
          invest:  '#3E7CAB',
          adapt:   '#D99A2B',
          manage:  '#9B4B54',
        },
      },
      fontFamily: {
        sans: ['"Open Sans"', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      maxWidth: { content: '1240px' },
    },
  },
  plugins: [],
}
