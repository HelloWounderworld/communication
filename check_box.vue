<template>
    <div class="check-container">
        <!-- Checkbox A -->
        <label class="check-item" :class="{ ativo: ativo === 'a', teal: ativo === 'a' }" @click="alternar('a')">
            <input type="checkbox" hidden />
            <span class="box"></span>
            <span class="label-text">Teal</span>
        </label>

        <!-- Checkbox B -->
        <label class="check-item" :class="{ ativo: ativo === 'b', red: ativo === 'b' }" @click="alternar('b')">
            <input type="checkbox" hidden />
            <span class="box"></span>
            <span class="label-text">Red</span>
        </label>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// controla qual checkbox está ativo
const ativo = ref<'a' | 'b'>('a')

// alterna entre os checkboxes
function alternar(opcao: 'a' | 'b') {
    ativo.value = opcao
}
</script>

<style scoped>
.check-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem;
    background: #333;
}

/* estilo geral do checkbox */
.check-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    cursor: pointer;
    color: #fff;
    font-size: 1.1rem;
    user-select: none;
}

/* caixa do checkbox */
.check-item .box {
    width: 26px;
    height: 26px;
    border-radius: 4px;
    border: 2px solid #ccc;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.25s ease;
}

/* ícone do check (✓) */
.check-item.ativo .box::after {
    content: "✓";
    font-size: 18px;
    color: white;
}

/* cor teal */
.check-item.teal.ativo .box {
    background: #009688;
    border-color: #00796b;
}

/* cor red */
.check-item.red.ativo .box {
    background: #f44336;
    border-color: #c62828;
}

/* hover suave */
.check-item:hover .box {
    border-color: #aaa;
}
</style>