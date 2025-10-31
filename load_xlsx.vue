<template>
    <div>
        <h2>📘 Dados carregados e processados do Excel</h2>

        <h3>🧾 Dados originais (Sheet1)</h3>
        <pre>{{ dadosOriginais }}</pre>

        <h3>🎲 Pares gerados (embaralhados)</h3>
        <pre>{{ paresGerados }}</pre>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as XLSX from 'xlsx'

interface LinhaExcel {
    [coluna: string]: string | number
}

interface Par {
    base: string | number
    combinado: string | number
}

// refs para exibir os dados na tela
const dadosOriginais = ref<LinhaExcel[]>([])
const paresGerados = ref<Par[]>([])

/**
 * Função utilitária: embaralha um array (Fisher–Yates)
 */
function embaralhar<T>(array: T[]): T[] {
    const arr = [...array]
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
            ;[arr[i], arr[j]] = [arr[j], arr[i]]
    }
    return arr
}

/**
 * Gera pares (0,1), (0,2), (0,3) embaralhados para cada linha do Excel
 */
function gerarPares(dados: LinhaExcel[]): Par[] {
    const todosPares: Par[] = []

    // Ignora a primeira linha (cabeçalho)
    dados.slice(1).forEach((linha) => {
        const valores = Object.values(linha)
        const base = valores[0]
        const outros = valores.slice(1)

        // Cria pares (0,1), (0,2), (0,3)
        const pares = outros.map((v) => ({ base, combinado: v }))

        // Embaralha os pares dessa linha
        const paresEmbaralhados = embaralhar(pares)
        todosPares.push(...paresEmbaralhados)
    })

    // Embaralha todos os pares finais
    return embaralhar(todosPares)
}

/**
 * Função principal executada quando o componente monta
 */
onMounted(async () => {
    try {
        console.log('🔄 Carregando dados do Excel...')
        const resposta = await fetch('/dados.xlsx') // lê do /public
        const arrayBuffer = await resposta.arrayBuffer()
        const bytes = new Uint8Array(arrayBuffer)

        // Lê o arquivo Excel
        const workbook = XLSX.read(bytes, { type: 'array' })
        const sheet = workbook.Sheets['Sheet1']

        if (!sheet) {
            console.error('❌ A aba "Sheet1" não foi encontrada!')
            return
        }

        // Converte para JSON
        const json = XLSX.utils.sheet_to_json<LinhaExcel>(sheet)

        // Guarda o formato original
        dadosOriginais.value = json

        // Gera pares embaralhados
        const pares = gerarPares(json)
        paresGerados.value = pares

        console.log('✅ Dados originais:', json)
        console.log('🎲 Pares gerados:', pares)
    } catch (error) {
        console.error('⚠️ Erro ao carregar Excel:', error)
    }
})
</script>

<style scoped>
pre {
    background: #1e1e1e;
    color: #00ff00;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
    white-space: pre-wrap;
}

h3 {
    margin-top: 20px;
    color: #00bcd4;
}
</style>