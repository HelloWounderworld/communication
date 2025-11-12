<template>
    <div class="q-pa-md">
        <div class="q-gutter-md flex justify-center">
            <q-checkbox v-model="ativo" val="a" label="チェック A" color="teal" keep-color @update:model-value="alternar" />
            <q-checkbox v-model="ativo" val="b" label="チェック B" color="orange" keep-color
                @update:model-value="alternar" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Estado — controla qual checkbox está ativo
const ativo = ref<'a' | 'b'>('a') // A começa ativo por padrão

function alternar(v: 'a' | 'b') {
    ativo.value = v // alterna o ativo (só um fica ligado)
}
</script>

<style scoped>
.q-pa-md {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    margin-top: 2rem;
}
</style>