<template>
    <div class="question-wrapper">
        <h3 class="question">You regularly make new friends.</h3>

        <div class="scale">
            <span class="label agree">Agree</span>

            <div class="options">
                <div v-for="(option, index) in options" :key="index" class="circle" :class="[
                    option.type,
                    { selected: selected === index }
                ]" :style="{ width: option.size + 'px', height: option.size + 'px' }" @click="selected = index"></div>
            </div>

            <span class="label disagree">Disagree</span>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// opções do "Likert scale"
const options = [
    { size: 60, type: 'agree' },
    { size: 48, type: 'agree' },
    { size: 40, type: 'agree' },
    { size: 32, type: 'neutral' },
    { size: 40, type: 'disagree' },
    { size: 48, type: 'disagree' },
    { size: 60, type: 'disagree' }
]

// índice selecionado (null se nada selecionado)
const selected = ref<number | null>(null)
</script>

<style scoped>
.question-wrapper {
    text-align: center;
    font-family: 'Inter', sans-serif;
    margin-top: 2rem;
}

.question {
    font-weight: 600;
    margin-bottom: 1.5rem;
    color: #1e1e1e;
}

.scale {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
}

.label {
    font-weight: 500;
    font-size: 0.95rem;
}

.label.agree {
    color: #2e7d32;
    /* verde */
}

.label.disagree {
    color: #6a1b9a;
    /* roxo */
}

.options {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
}

/* círculo base */
.circle {
    border-radius: 50%;
    border: 2px solid #ccc;
    cursor: pointer;
    transition: transform 0.2s, border-color 0.2s, background 0.2s;
}

/* tons */
.circle.agree {
    border-color: #2e7d32;
}

.circle.disagree {
    border-color: #6a1b9a;
}

.circle.neutral {
    border-color: #999;
}

/* seleção */
.circle.selected.agree {
    background: #2e7d32;
}

.circle.selected.disagree {
    background: #6a1b9a;
}

.circle.selected.neutral {
    background: #999;
}

/* efeito hover */
.circle:hover {
    transform: scale(1.1);
}
</style>