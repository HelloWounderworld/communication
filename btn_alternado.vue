<template>
    <div class="toggle-container">
        <button :class="['toggle-btn', ativo === 'a' ? 'ativo' : '']" @click="alternar('a')">
            Botão A
        </button>

        <button :class="['toggle-btn', ativo === 'b' ? 'ativo' : '']" @click="alternar('b')">
            Botão B
        </button>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Estado — controla qual botão está ativo
const ativo = ref<'a' | 'b'>('a') // por padrão o botão A começa ativo

// Função que alterna o estado ativo
function alternar(botao: 'a' | 'b') {
    ativo.value = botao
}
</script>

<style scoped>
.toggle-container {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
}

.toggle-btn {
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 8px;
    border: 2px solid #ccc;
    background: #f8f8f8;
    cursor: pointer;
    transition: all 0.25s ease;
}

.toggle-btn:hover {
    background: #eaeaea;
}

.toggle-btn.ativo {
    background: #2196f3;
    color: white;
    border-color: #1976d2;
}
</style>