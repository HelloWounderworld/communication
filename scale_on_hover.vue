<template>
    <div class="btn-container">
        <button v-for="(texto, index) in botoes" :key="index" class="test-btn" :class="{ ativo: botaoAtivo === index }"
            @click="toggleBotao(index, $event)">
            {{ texto }}
        </button>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// lista de botões
const botoes = ref<string[]>(['Primeiro', 'Segundo', 'Terceiro', 'Quarto', 'Quinto'])
const botaoAtivo = ref<number | null>(null)

// limite máximo de caracteres permitidos na seleção
const LIMITE_SELECAO = 20

function toggleBotao(index: number, event: MouseEvent) {
    botaoAtivo.value = botaoAtivo.value === index ? null : index
    limparSelecao()
}

// limpa a seleção de texto
function limparSelecao() {
    const selecao = window.getSelection()
    if (selecao) selecao.removeAllRanges()
}

// 🔹 mantém o nome original, mas agora impõe limite à seleção
function handleTextSelection() {
    const selecao = window.getSelection()
    if (!selecao || selecao.rangeCount === 0) return

    const textoSelecionado = selecao.toString().trim()
    if (textoSelecionado.length === 0) return

    // Se a seleção for menor ou igual ao limite, nada muda
    if (textoSelecionado.length <= LIMITE_SELECAO) {
        // mas, se houver uma seleção válida (mesmo pequena), desativa o botão ativo
        botaoAtivo.value = null
        return
    }

    // Se a seleção ultrapassar o limite, cortamos visualmente no ponto certo
    const rangeOriginal = selecao.getRangeAt(0)
    const inicio = rangeOriginal.startContainer
    const offsetInicial = rangeOriginal.startOffset
    const novoRange = document.createRange()

    // percorre nós de texto até atingir o limite de caracteres
    let contador = 0
    let node: Node | null = inicio

    while (node && contador < LIMITE_SELECAO) {
        if (node.nodeType === Node.TEXT_NODE) {
            const textoNode = node.textContent || ''
            const restante = LIMITE_SELECAO - contador

            if (textoNode.length > restante) {
                novoRange.setStart(inicio, offsetInicial)
                novoRange.setEnd(node, restante)
                contador = LIMITE_SELECAO
                break
            } else {
                contador += textoNode.length
            }
        }

        node = getNextNode(node)
    }

    // aplica a nova seleção limitada visualmente
    selecao.removeAllRanges()
    selecao.addRange(novoRange)

    // desativa o botão ativo
    botaoAtivo.value = null
}

// percorre o DOM para achar o próximo nó de texto
function getNextNode(node: Node): Node | null {
    if (node.firstChild) return node.firstChild
    while (node && !node.nextSibling) node = node.parentNode as Node
    return node?.nextSibling || null
}

// listeners globais
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

button.test-btn {
    font-size: 18px;
    padding: 15px 25px;
    border: 2px solid #fff;
    color: #fff;
    background: transparent;
    transition: transform 0.2s ease-in-out, background 0.2s, color 0.2s, box-shadow 0.2s;
    border-radius: 8px;
}

button.test-btn:hover {
    cursor: pointer;
    transform: scale(1.15);
    background: #fff;
    color: #000;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

button.test-btn.ativo {
    background: #00bcd4;
    color: #000;
    box-shadow: 0 0 15px rgba(0, 188, 212, 0.8);
    transform: scale(1.1);
}

button.test-btn:active {
    animation: brilho 0.3s ease-out;
}

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

:host {
    background-color: #111;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>