<template>
    <v-container class="py-6">
        <!-- Cabeçalho fixo (rótulos) -->
        <v-row class="header-row" no-gutters>
            <v-col cols="6" class="header-label">Título</v-col>
            <v-col cols="3" class="header-label">Qtd. Letras</v-col>
            <v-col cols="3" class="header-label">Copiar</v-col>
        </v-row>

        <!-- Linhas de conteúdo (v-for) -->
        <v-row v-for="(item, index) in dados" :key="index" class="data-row" align="center" no-gutters>
            <!-- Coluna 1: título -->
            <v-col cols="6">
                <v-card class="pa-3 text-display" variant="outlined">
                    <div v-html="item.titulo"></div>
                </v-card>
            </v-col>

            <!-- Coluna 2: quantidade de letras -->
            <v-col cols="3" class="text-center">
                <v-card class="pa-3" variant="outlined">
                    {{ item.qtd }}
                </v-card>
            </v-col>

            <!-- Coluna 3: botão copiar -->
            <v-col cols="3" class="text-center">
                <v-btn color="primary" @click="copiarTexto(item.titulo)">
                    Copiar
                </v-btn>
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const dados = ref([
    { titulo: '<b>Exemplo 1</b> com <i>HTML</i>', qtd: 15 },
    { titulo: 'Outro texto com <strong>formatação</strong>', qtd: 28 },
    { titulo: '<u>Mais um</u> exemplo', qtd: 10 }
])

function copiarTexto(textoHtml: string) {
    // Remover tags HTML para copiar texto puro
    const textoPuro = textoHtml.replace(/<[^>]*>/g, '')
    navigator.clipboard.writeText(textoPuro)
    alert(`Copiado: "${textoPuro}"`)
}
</script>

<style scoped>
/* Cabeçalho fixo */
.header-row {
    border-bottom: 2px solid #1976d2;
    margin-bottom: 8px;
}

.header-label {
    font-weight: 600;
    color: #1976d2;
    font-size: 0.9rem;
    text-transform: uppercase;
    padding: 4px 8px;
}

/* Cada linha de conteúdo */
.data-row {
    margin-bottom: 8px;
}

.text-display {
    background-color: #fff;
    min-height: 48px;
    display: flex;
    align-items: center;
    font-size: 1rem;
    color: #333;
}

/* Botão */
.v-btn {
    text-transform: none;
}
</style>