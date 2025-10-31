<template>
    <div class="editor-container">
        <label class="editor-label">
            Digite e selecione (limite: {{ LIMITE_SELECAO }} caracteres)
        </label>

        <div ref="editorRef" class="custom-editor" contenteditable="true" @input="handleInput"
            @mouseup="handleTextSelection"></div>

        <!-- só para mostrar o estado do botão ativo -->
        <div class="status">
            Botão ativo: <b>{{ botaoAtivo !== null ? botoes[botaoAtivo] : 'nenhum' }}</b>
        </div>

        <div class="btn-container">
            <button v-for="(texto, index) in botoes" :key="index" class="test-btn"
                :class="{ ativo: botaoAtivo === index }" @click="toggleBotao(index)">
                {{ texto }}
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// conteúdo e referência
const texto = ref<string>('Aqui você pode digitar e selecionar texto livremente.')
const editorRef = ref<HTMLDivElement | null>(null)

// lista de botões e controle de ativo
const botoes = ref<string[]>(['Primeiro', 'Segundo', 'Terceiro', 'Quarto', 'Quinto'])
const botaoAtivo = ref<number | null>(null)

// limite de caracteres
const LIMITE_SELECAO = 50

// alterna o estado do botão
function toggleBotao(index: number) {
    botaoAtivo.value = botaoAtivo.value === index ? null : index
}

// 🔹 desativa botão ativo se o usuário alterar o texto
function handleInput(event: Event) {
    const el = event.target as HTMLDivElement
    if (!el) return

    if (el.innerText.length > LIMITE_SELECAO) {
        el.innerText = el.innerText.slice(0, LIMITE_SELECAO)
    }

    texto.value = el.innerText

    // desativa o botão ativo
    botaoAtivo.value = null
}

// 🔹 limita a seleção de texto
function handleTextSelection() {
    const selecao = window.getSelection()
    if (!selecao || selecao.rangeCount === 0) return

    const textoSelecionado = selecao.toString()
    if (textoSelecionado.length === 0) return

    if (textoSelecionado.length > LIMITE_SELECAO) {
        const textoLimitado = textoSelecionado.slice(0, LIMITE_SELECAO)
        console.log('Texto selecionado limitado:', textoLimitado)
    }

    // também desativa o botão ativo ao selecionar algo
    botaoAtivo.value = null
}

// inicializa o texto no editor
onMounted(() => {
    if (editorRef.value) {
        editorRef.value.innerText = texto.value
    }
})
</script>

<style scoped>
.editor-container {
    font-family: 'Roboto', sans-serif;
    max-width: 600px;
    margin: 40px auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.editor-label {
    font-size: 0.9rem;
    color: #666;
}

.custom-editor {
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 12px;
    min-height: 100px;
    font-size: 1rem;
    line-height: 1.5;
    outline: none;
    background: white;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.custom-editor:focus {
    border-color: #1976d2;
    box-shadow: 0 0 0 1px #1976d2;
}

/* Botões */
.btn-container {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
}

button.test-btn {
    font-size: 16px;
    padding: 12px 20px;
    border: 2px solid #444;
    color: #444;
    background: transparent;
    border-radius: 6px;
    transition: all 0.2s ease-in-out;
}

button.test-btn:hover {
    background: #444;
    color: white;
    transform: scale(1.05);
}

button.test-btn.ativo {
    background: #00bcd4;
    color: #000;
    box-shadow: 0 0 10px rgba(0, 188, 212, 0.8);
}

.status {
    font-size: 0.9rem;
    text-align: center;
    color: #555;
}
</style>