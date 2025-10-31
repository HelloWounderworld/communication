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

<template>
    <div class="textarea-wrapper">
      <label class="textarea-label">Digite algo</label>
      <div
        class="custom-textarea"
        contenteditable="true"
        @focus="focado = true"
        @blur="focado = false"
        @input="refNewsArea = $event.target.innerHTML"
        v-html="refNewsArea"
      ></div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  const refNewsArea = ref<string>('')
  const focado = ref(false)
  </script>
  
  <style scoped>
  .textarea-wrapper {
    position: relative;
    font-family: Roboto, sans-serif;
    width: 100%;
    max-width: 600px;
  }
  
  /* label flutuante */
  .textarea-label {
    position: absolute;
    top: 10px;
    left: 14px;
    background: white;
    padding: 0 4px;
    color: #6b6b6b;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    pointer-events: none;
  }
  
  /* a área editável */
  .custom-textarea {
    width: 100%;
    min-height: 120px;
    padding: 24px 14px 8px 14px; /* espaço pra label flutuante */
    border: 1px solid #bdbdbd;
    border-radius: 8px;
    font-size: 1rem;
    line-height: 1.5;
    background-color: white;
    outline: none;
    resize: none;
    overflow-y: auto;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }
  
  /* quando focado */
  .custom-textarea:focus {
    border-color: #1976d2;
    box-shadow: 0 0 0 1px #1976d2;
  }
  
  /* label sobe quando há texto ou foco */
  .custom-textarea:focus + .textarea-label,
  .textarea-wrapper:has(.custom-textarea:not(:empty)) .textarea-label {
    top: -8px;
    left: 10px;
    font-size: 0.75rem;
    color: #1976d2;
  }
  </style>
 
 <template>
    <div class="textarea-wrapper">
      <label class="textarea-label">Digite algo</label>
      <div
        class="custom-textarea"
        contenteditable="true"
        @focus="focado = true"
        @blur="focado = false"
        @input="refNewsArea = $event.target.innerHTML"
        @paste="handlePaste"
        ref="editableDiv"
        v-html="refNewsArea"
      ></div>
  
      <!-- Botão para apagar -->
      <button class="clear-btn" @click="clearText">Apagar</button>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  
  const refNewsArea = ref<string>('')
  const focado = ref(false)
  const editableDiv = ref<HTMLElement | null>(null)
  
  // Função para apagar o texto
  function clearText() {
    refNewsArea.value = ''
    if (editableDiv.value) {
      editableDiv.value.innerHTML = ''
    }
  }
  
  // Função para colar texto puro mantendo quebras de linha
  function handlePaste(event: ClipboardEvent) {
    event.preventDefault()
    const text = event.clipboardData?.getData('text/plain') || ''
    const formattedText = text
      .replace(/\n/g, '<br>') // preserva quebras de linha
    insertHtmlAtCursor(formattedText)
  }
  
  // Função auxiliar para inserir HTML na posição do cursor
  function insertHtmlAtCursor(html: string) {
    const sel = window.getSelection()
    if (!sel || !sel.getRangeAt || !sel.rangeCount) return
    const range = sel.getRangeAt(0)
    range.deleteContents()
    const el = document.createElement('div')
    el.innerHTML = html
    const frag = document.createDocumentFragment()
    let node
    let lastNode
    while ((node = el.firstChild)) {
      lastNode = frag.appendChild(node)
    }
    range.insertNode(frag)
    // Move o cursor para o final do conteúdo inserido
    if (lastNode) {
      range.setStartAfter(lastNode)
      range.collapse(true)
      sel.removeAllRanges()
      sel.addRange(range)
    }
  }
  </script>
  
  <style scoped>
  .textarea-wrapper {
  position: relative;
  font-family: Roboto, sans-serif;
  width: 100%;
  max-width: 600px;
}

/* container do label + botão */
.label-row {
  position: absolute;
  top: 10px;
  left: 14px;
  right: 14px;
  display: flex;
  justify-content: space-between; /* label à esquerda, botão à direita */
  align-items: center;
  pointer-events: none; /* permite clicar no textarea por trás */
}

/* label flutuante */
.textarea-label {
  background: white;
  padding: 0 4px;
  color: #6b6b6b;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  pointer-events: auto; /* label clicável */
}

/* botão de apagar */
.clear-btn {
  pointer-events: auto; /* botão clicável */
  padding: 2px 8px;
  font-size: 0.8rem;
  border: none;
  background-color: #e53935;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.clear-btn:hover {
  background-color: #d32f2f;
}

/* textarea */
.custom-textarea {
  width: 100%;
  min-height: 120px;
  padding: 24px 14px 8px 14px;
  border: 1px solid #bdbdbd;
  border-radius: 8px;
  font-size: 1rem;
  line-height: 1.5;
  background-color: white;
  outline: none;
  resize: none;
  overflow-y: auto;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

/* quando focado */
.custom-textarea:focus {
  border-color: #1976d2;
  box-shadow: 0 0 0 1px #1976d2;
}

/* label sobe quando há foco ou texto */
.custom-textarea:focus + .label-row .textarea-label,
.textarea-wrapper:has(.custom-textarea:not(:empty)) .textarea-label {
  top: -8px;
  font-size: 0.75rem;
  color: #1976d2;
}

  </style>
  

