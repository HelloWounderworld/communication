<template>
    <v-card class="pa-4 custom-card" max-width="500">
        <div class="html-display-wrapper">
            <!-- rótulo fixo -->
            <span class="floating-label">Rótulo Fixo</span>

            <!-- área de exibição do conteúdo HTML -->
            <div class="html-display" v-html="htmlContent"></div>
        </div>
    </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const htmlContent = ref(`
    <p style="margin: 0;">Este é um <b>conteúdo</b> com <i>HTML</i>.</p>
    <ul>
      <li>Indentação</li>
      <li>Listas</li>
    </ul>
  `)
</script>

<style scoped>
.custom-card {
    position: relative;
}

/* container geral */
.html-display-wrapper {
    position: relative;
    border: 1px solid #bdbdbd;
    border-radius: 8px;
    padding: 24px 12px 12px 12px;
    /* espaço pro label */
    min-height: 100px;
    background-color: white;
    overflow: auto;
}

/* rótulo flutuante fixo */
.floating-label {
    position: absolute;
    top: -8px;
    left: 14px;
    background-color: white;
    padding: 0 6px;
    font-size: 0.75rem;
    color: #1976d2;
    font-weight: 500;
}

/* área que exibe o HTML */
.html-display {
    font-family: Roboto, sans-serif;
    font-size: 1rem;
    color: #333;
    line-height: 1.5;
    white-space: normal;
    word-break: break-word;
}

.html-display ul {
    padding-left: 1.2rem;
}
</style>