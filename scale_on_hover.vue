<template>
    <div class="btn-container">
        <!-- gera 5 botões a partir da lista -->
        <button v-for="(texto, index) in botoes" :key="index" class="test-btn" @click="efeitoClique($event)">
            {{ texto }}
        </button>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// lista com 5 textos diferentes
const botoes = ref<string[]>([
    'Primeiro',
    'Segundo',
    'Terceiro',
    'Quarto',
    'Quinto'
])

// adiciona a classe "clicado" por um curto tempo para o efeito de brilho
function efeitoClique(event: MouseEvent) {
    const btn = event.currentTarget as HTMLButtonElement
    btn.classList.add('clicado')
    setTimeout(() => btn.classList.remove('clicado'), 300) // remove o brilho após 300ms
}

function limparSelecao() {
  const selecao = window.getSelection()
  if (selecao) {
    selecao.removeAllRanges() // ← remove qualquer seleção ativa
  }
}
</script>

<style scoped>
.btn-container {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    /* espaçamento entre os botões */
    margin-top: 50px;
    flex-wrap: wrap;
}

/* estilo base */
button.test-btn {
    font-size: 18px;
    padding: 15px 25px;
    border: 2px solid #fff;
    color: #fff;
    background: transparent;
    transition: transform 0.2s ease-in-out, background 0.2s, color 0.2s, box-shadow 0.2s;
    border-radius: 8px;
}

/* efeito de hover */
button.test-btn:hover {
    cursor: pointer;
    transform: scale(1.15);
    background: #fff;
    color: #000;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

/* efeito de clique — brilho momentâneo */
button.test-btn.clicado {
    animation: brilho 0.3s ease-out;
}

/* animação de brilho */
@keyframes brilho {
    0% {
        box-shadow: 0 0 0px rgba(255, 255, 255, 0);
        background: #fff;
        color: #000;
        transform: scale(1.1);
    }

    50% {
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
        background: #fff;
        color: #000;
    }

    100% {
        box-shadow: 0 0 0px rgba(255, 255, 255, 0);
        background: transparent;
        color: #fff;
        transform: scale(1);
    }
}

/* fundo da página escuro (para o contraste) */
:host {
    background-color: #111;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>