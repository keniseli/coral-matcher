import colors from "tailwindcss/colors"
module.exports = {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        coral: {
          bg: "#071116",
          input: "#071116",

          surface: "#0b181e",
          "surface-border": colors.slate[700],

          raised: "#071116",
          "raised-border": colors.slate[500],

          overlay: "#13262D",

          primary: "#2bd4bd",
          "primary-bg": "rgba(43, 212, 189, 0.1)",
          "primary-button-text": "#062126",
          "primary-hover": "#5EEAD4",
          "primary-text": colors.slate[100],
          
          "secondary-text": colors.slate[500],


          border: "#1C3037",
          "border-strong": "#29434B",

          muted: "#64748B",
        },
      },
    }
  },
  plugins: [],
}
