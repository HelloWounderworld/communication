<template>
    <div>
        <h2>📘 Dados carregados do Excel</h2>
        <pre>{{ dadosExcel }}</pre>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as XLSX from 'xlsx'

const dadosExcel = ref<any[]>([])

onMounted(async () => {
    try {
        console.log('🔄 Carregando dados do Excel...')
        const resposta = await fetch('/dados.xlsx') // lê o arquivo do /public
        const arrayBuffer = await resposta.arrayBuffer()
        const bytes = new Uint8Array(arrayBuffer)

        // Lê o workbook
        const workbook = XLSX.read(bytes, { type: 'array' })

        // Acessa a aba "Sheet1"
        const sheet = workbook.Sheets['Sheet1']

        if (!sheet) {
            console.error('❌ A aba "Sheet1" não foi encontrada!')
            return
        }

        // Converte a planilha em JSON
        const json = XLSX.utils.sheet_to_json(sheet)
        dadosExcel.value = json

        console.log('✅ Dados carregados:', json)
    } catch (error) {
        console.error('⚠️ Erro ao carregar Excel:', error)
    }
})
</script>

<style scoped>
pre {
    background: #222;
    color: #0f0;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
}
</style>