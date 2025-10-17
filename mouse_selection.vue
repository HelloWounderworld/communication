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
