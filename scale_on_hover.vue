<template>
  <div class="btn-container">
    <button
      v-for="(texto, index) in botoes"
      :key="index"
      class="test-btn"
      :class="{ ativo: botaoAtivo === index }"
      @click="toggleBotao(index, $event)"
    >
      {{ texto }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// lista de botões
const botoes = ref<string[]>(['Primeiro', 'Segundo', 'Terceiro', 'Quarto', 'Quinto'])

// índice do botão ativo (ou null se nenhum estiver ativo)
const botaoAtivo = ref<number | null>(null)

// alterna o estado do botão clicado
function toggleBotao(index: number, event: MouseEvent) {
  if (botaoAtivo.value === index) {
    // se clicar no mesmo botão → desliga
    botaoAtivo.value = null
  } else {
    // se clicar em outro botão → ativa o novo e desativa o anterior
    botaoAtivo.value = index
  }

  // limpa qualquer seleção de texto ativa
  limparSelecao()
}

// função que limpa seleção de texto (caso o usuário selecione algo)
function limparSelecao() {
  const selecao = window.getSelection()
  if (selecao) selecao.removeAllRanges()
}

// quando o usuário seleciona texto → desativa o botão ativo
function handleTextSelection() {
  const selecao = window.getSelection()
  if (selecao && selecao.toString().trim().length > 0) {
    botaoAtivo.value = null
  }
}

// adiciona e remove o listener global
onMounted(() => {
  document.addEventListener('mouseup', handleTextSelection)
})
onBeforeUnmount(() => {
  document.removeEventListener('mouseup', handleTextSelection)
})
</script>

<style scoped>
.btn-container {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
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

/* hover */
button.test-btn:hover {
  cursor: pointer;
  transform: scale(1.15);
  background: #fff;
  color: #000;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

/* estado ativo (ON) */
button.test-btn.ativo {
  background: #00bcd4;
  color: #000;
  box-shadow: 0 0 15px rgba(0, 188, 212, 0.8);
  transform: scale(1.1);
}

/* efeito de clique (brilho momentâneo) */
button.test-btn:active {
  animation: brilho 0.3s ease-out;
}

/* animação de brilho */
@keyframes brilho {
  0% {
    box-shadow: 0 0 0px rgba(255, 255, 255, 0);
    transform: scale(1.05);
  }
  50% {
    box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  }
  100% {
    box-shadow: 0 0 0px rgba(255, 255, 255, 0);
    transform: scale(1);
  }
}

/* fundo escuro */
:host {
  background-color: #111;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
