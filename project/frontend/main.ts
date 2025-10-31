// frontend/src/main.ts
import { createApp } from 'vue'
import MainView from './components/MainView.vue'

// (Opcional) — Importar estilos globais
import './style.css'

const app = createApp(MainView)
app.mount('#app')
