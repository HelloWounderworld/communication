<template>
    <div class="toggle-container">
        <label class="toggle-check" :class="{ ativo: ativo === 'a' }" @click="alternar('a')">
            <input type="checkbox" value="a" v-model="ativo" hidden />
            <span>チェック A</span>
        </label>

        <label class="toggle-check" :class="{ ativo: ativo === 'b' }" @click="alternar('b')">
            <input type="checkbox" value="b" v-model="ativo" hidden />
            <span>チェック B</span>
        </label>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Estado — controla qual opção está ativa
const ativo = ref<'a' | 'b'>('a') // por padrão, o A começa ativo

// Alterna entre as opções
function alternar(opcao: 'a' | 'b') {
    ativo.value = opcao
}
</script>

<style scoped>
.toggle-container {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
}

/* Estilo dos checkboxes como botões */
.toggle-check {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 8px;
    border: 2px solid #ccc;
    background: #f8f8f8;
    cursor: pointer;
    transition: all 0.25s ease;
    user-select: none;
}

.toggle-check:hover {
    background: #eaeaea;
}

.toggle-check.ativo {
    background: #2196f3;
    color: white;
    border-color: #1976d2;
}
</style>