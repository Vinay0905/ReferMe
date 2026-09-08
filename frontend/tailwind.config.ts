import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0A0518",          // Deep cyber cosmic dark base
          card: "#3E0F8D",        // Royal purple base from palette rgb(62, 15, 141)
          neon: "#9564DD",        // Electric lavender border & aura rgb(149, 100, 221)
          yellow: "#E4DA72",      // Cyber warm gold accent rgb(228, 218, 114)
          grey: "#EEEEEE",        // Soft crisp off-white text rgb(238, 238, 238)
        },
      },
      boxShadow: {
        "neon-purple": "0 0 25px -5px rgba(149, 100, 221, 0.45)",
        "neon-gold": "0 0 25px -5px rgba(228, 218, 114, 0.45)",
        "3d-lift": "0 25px 50px -12px rgba(62, 15, 141, 0.65)",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
export default config;
