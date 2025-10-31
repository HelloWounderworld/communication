<!-- src/App.vue -->
<template>
    <div id="app">
        <div v-if="carregando" class="loading">
            <div class="spinner"></div>
            <p>⏳ Processando Excel e gerando JSONs...</p>
        </div>

        <div v-else-if="erro" class="error">
            <h2>❌ Erro</h2>
            <p>{{ erro }}</p>
            <button @click="reprocessar" class="btn-retry">🔄 Tentar Novamente</button>
        </div>

        <div v-else-if="dados" class="content">
            <h1>✅ Processamento Concluído!</h1>

            <div class="success-message">
                <p>Os arquivos JSON foram gerados e baixados automaticamente:</p>
                <ul>
                    <li>📄 <strong>dados-original.json</strong></li>
                    <li>📄 <strong>pares-embaralhados.json</strong></li>
                </ul>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <h3>📋 Linhas Originais</h3>
                    <p class="number">{{ dados.original.length }}</p>
                </div>
                <div class="stat-card">
                    <h3>🔀 Pares Gerados</h3>
                    <p class="number">{{ dados.pares.length }}</p>
                </div>
            </div>

            <div class="section">
                <h2>📊 Preview dos Dados</h2>
                <div class="tabs">
                    <button :class="{ active: tabAtiva === 'original' }" @click="tabAtiva = 'original'">
                        Dados Originais
                    </button>
                    <button :class="{ active: tabAtiva === 'pares' }" @click="tabAtiva = 'pares'">
                        Pares Embaralhados
                    </button>
                </div>

                <div v-if="tabAtiva === 'original'" class="tab-content">
                    <pre>{{ JSON.stringify(dados.original.slice(0, 5), null, 2) }}</pre>
                </div>

                <div v-else class="tab-content">
                    <div class="pares-grid">
                        <div v-for="(par, index) in dados.pares.slice(0, 12)" :key="index" class="par-card">
                            <span class="base">{{ par.base }}</span>
                            <span class="arrow">→</span>
                            <span class="combinado">{{ par.combinado }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <button @click="reprocessar" class="btn-reprocessar">
                🔄 Reprocessar e Baixar Novamente
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { processarExcelAutomaticamente, type DadosProcessados } from './utils/excelProcessor';

const dados = ref<DadosProcessados | null>(null);
const carregando = ref(true);
const erro = ref<string | null>(null);
const tabAtiva = ref<'original' | 'pares'>('original');

// Caminho do arquivo Excel (ajuste conforme necessário)
const CAMINHO_EXCEL = 'dados.xlsx';

async function processar() {
    try {
        carregando.value = true;
        erro.value = null;

        dados.value = await processarExcelAutomaticamente(CAMINHO_EXCEL);
    } catch (err) {
        erro.value = err instanceof Error ? err.message : 'Erro desconhecido ao processar';
        console.error('❌ Erro:', err);
    } finally {
        carregando.value = false;
    }
}

async function reprocessar() {
    await processar();
}

// Processa automaticamente quando a página carrega
onMounted(() => {
    processar();
});
</script>

<style scoped>
* {
    box-sizing: border-box;
}

#app {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.loading {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.loading p {
    color: #2c3e50;
    font-size: 1.1rem;
}

.error {
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.error h2 {
    color: #e74c3c;
    margin-bottom: 1rem;
}

.error p {
    color: #555;
    margin-bottom: 1.5rem;
}

.btn-retry {
    background: #e74c3c;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: transform 0.2s;
}

.btn-retry:hover {
    transform: translateY(-2px);
}

.content {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h1 {
    color: #2c3e50;
    margin: 0 0 1.5rem 0;
    text-align: center;
}

.success-message {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.success-message p {
    color: #155724;
    margin: 0 0 0.5rem 0;
    font-weight: 600;
}

.success-message ul {
    color: #155724;
    margin: 0.5rem 0 0 1.5rem;
}

.success-message li {
    margin: 0.25rem 0;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    text-align: center;
}

.stat-card h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.9rem;
    opacity: 0.95;
    font-weight: 600;
}

.number {
    font-size: 3rem;
    font-weight: bold;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.section {
    margin-bottom: 2rem;
}

.section h2 {
    color: #34495e;
    margin: 0 0 1rem 0;
    font-size: 1.3rem;
}

.tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #e0e0e0;
}

.tabs button {
    background: transparent;
    border: none;
    padding: 0.75rem 1.5rem;
    cursor: pointer;
    font-size: 1rem;
    color: #666;
    border-bottom: 3px solid transparent;
    transition: all 0.3s;
}

.tabs button.active {
    color: #667eea;
    border-bottom-color: #667eea;
    font-weight: 600;
}

.tabs button:hover {
    color: #667eea;
}

.tab-content {
    margin-top: 1rem;
}

pre {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 0.85rem;
    border: 1px solid #e0e0e0;
}

.pares-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
}

.par-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    transition: transform 0.2s, box-shadow 0.2s;
}

.par-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.base,
.combinado {
    font-weight: 600;
    color: #2c3e50;
    font-size: 0.95rem;
}

.arrow {
    color: #667eea;
    font-size: 1.2rem;
    font-weight: bold;
}

.btn-reprocessar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    display: block;
    margin: 0 auto;
}

.btn-reprocessar:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-reprocessar:active {
    transform: translateY(0);
}
</style>
```

## Estrutura Final:
```
frontend/
├── src/
│ ├── utils/
│ │ └── excelProcessor.ts ← Processamento do Excel
│ ├── App.vue ← Interface
│ └── main.ts
├── public/
│ └── dados.xlsx ← Coloque seu Excel aqui
├── package.json
└── vite.config.ts