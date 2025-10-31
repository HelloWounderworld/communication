<template>
    <div class="excel-viewer">
        <h2>📘 Dados carregados e processados do Excel</h2>

        <div class="btns">
            <button @click="baixarBackup">💾 Baixar Backup Original</button>
            <button @click="baixarPares">🎲 Baixar Pares Gerados</button>
        </div>

        <div v-if="erro" class="erro">{{ erro }}</div>

        <div v-else>
            <h3>🧾 Dados originais</h3>
            <pre>{{ dadosOriginais }}</pre>

            <h3>🎲 Pares embaralhados</h3>
            <pre>{{ paresGerados }}</pre>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import {
    lerExcelComoJson,
    gerarPares,
    baixarJSON,
    LinhaExcel,
    Par,
} from "@/utils/excelProcessor"

const dadosOriginais = ref<LinhaExcel[]>([])
const paresGerados = ref<Par[]>([])
const erro = ref<string | null>(null)

onMounted(async () => {
    try {
        const resposta = await fetch("/dados.xlsx")
        if (!resposta.ok) throw new Error("Erro ao carregar arquivo Excel")

        const arrayBuffer = await resposta.arrayBuffer()

        // 1️⃣ Lê os dados originais
        const json = lerExcelComoJson(arrayBuffer)
        dadosOriginais.value = json

        // 2️⃣ Gera os pares embaralhados
        paresGerados.value = gerarPares(json)
    } catch (e: any) {
        erro.value = e.message || "Erro desconhecido ao ler Excel"
        console.error("⚠️ Erro:", e)
    }
})

// 3️⃣ Baixar os arquivos JSON
function baixarBackup() {
    baixarJSON(dadosOriginais.value, "backup_original.json")
}

function baixarPares() {
    baixarJSON(paresGerados.value, "pares_gerados.json")
}
</script>

<style scoped>
.excel-viewer {
    padding: 20px;
    background: #111;
    color: #fff;
    font-family: monospace;
}

pre {
    background: #1e1e1e;
    color: #00ff00;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
    white-space: pre-wrap;
}

.btns {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

button {
    background: #00bcd4;
    color: #000;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
}

button:hover {
    background: #00e5ff;
}

.erro {
    color: #ff4d4d;
    font-weight: bold;
    margin-top: 10px;
}
</style>