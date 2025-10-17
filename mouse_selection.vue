<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Cria uma variável reativa para armazenar o texto selecionado
const textoSelecionado = ref<string>('')

// Ao montar o componente, escutamos o evento de seleção de texto
onMounted(() => {
    document.addEventListener('mouseup', () => {
        const texto = window.getSelection()?.toString().trim()
        if (texto) {
            textoSelecionado.value = texto // Atualiza o valor
        }
    })
})
</script>

<template>
    <div class="layout">
        <!-- Aba 1: Texto para selecionar -->
        <div class="aba aba-esquerda">
            <h2>Selecione um texto abaixo:</h2>
            <p>
                Este é um exemplo simples feito com Nuxt 3 e TypeScript.
                Quando você selecionar qualquer parte deste texto e soltar o mouse,
                o trecho selecionado será mostrado automaticamente na aba ao lado.
            </p>
            <p>
                Pode selecionar uma nova parte do texto sempre que quiser —
                a seleção anterior será substituída pela nova.
            </p>
        </div>

        <!-- Aba 2: Mostra o texto capturado -->
        <div class="aba aba-direita">
            <h2>Texto capturado:</h2>
            <p v-if="textoSelecionado">{{ textoSelecionado }}</p>
            <p v-else><em>Nenhum texto selecionado ainda.</em></p>
        </div>
    </div>
</template>

<style scoped>
.layout {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
    padding: 2rem;
}

.aba {
    flex: 1;
    border: 2px solid #ccc;
    padding: 1rem;
    border-radius: 8px;
    background: #fafafa;
}

.aba-esquerda {
    user-select: text;
    /* permite seleção de texto */
}

.aba-direita {
    background: #fff3cd;
    border-color: #ffecb5;
}
</style>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// Variável do v-model do textarea
const refNewsArea = ref<string>('')

// Texto capturado da seleção
const textoSelecionado = ref<string>('')

// Função que captura a seleção dentro do textarea
function capturarSelecao(e: Event) {
  const el = e.target as HTMLTextAreaElement
  const start = el.selectionStart
  const end = el.selectionEnd

  if (start !== end) {
    textoSelecionado.value = el.value.substring(start, end)
  }
}

onMounted(() => {
  // Você pode ouvir o evento mouseup, keyup ou selectionchange
  const textarea = document.querySelector('textarea')
  if (textarea) {
    textarea.addEventListener('mouseup', capturarSelecao)
    textarea.addEventListener('keyup', capturarSelecao)
  }
})

onBeforeUnmount(() => {
  const textarea = document.querySelector('textarea')
  if (textarea) {
    textarea.removeEventListener('mouseup', capturarSelecao)
    textarea.removeEventListener('keyup', capturarSelecao)
  }
})
</script>

<template>
  <div class="layout">
    <div class="aba aba-esquerda">
      <h2>Digite e selecione algo:</h2>
      <v-textarea
        v-model="refNewsArea"
        label="Área de texto"
        auto-grow
        outlined
        rows="6"
      />
    </div>

    <div class="aba aba-direita">
      <h2>Texto selecionado:</h2>
      <p v-if="textoSelecionado">{{ textoSelecionado }}</p>
      <p v-else><em>Nada selecionado ainda.</em></p>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  gap: 2rem;
  padding: 2rem;
}

.aba {
  flex: 1;
  border: 2px solid #ccc;
  padding: 1rem;
  border-radius: 8px;
  background: #fafafa;
}

.aba-direita {
  background: #fff3cd;
  border-color: #ffecb5;
}
</style>

