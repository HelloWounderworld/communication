<!-- src/App.vue -->
<template>
    <div id="app">
        <div v-if="carregando" class="loading">
            <div class="spinner"></div>
            <p>⏳ Processando Excel automaticamente...</p>
            <p class="loading-detail">{{ etapaAtual }}</p>
        </div>

        <div v-else-if="erro" class="error">
            <h2>❌ Erro</h2>
            <p>{{ erro }}</p>
            <div class="error-details">
                <p><strong>Certifique-se de que:</strong></p>
                <ul>
                    <li>O arquivo <code>dados.xlsx</code> está na pasta <code>public/</code></li>
                    <li>O arquivo possui uma aba chamada "Sheet1"</li>
                    <li>O servidor de desenvolvimento está rodando</li>
                </ul>
            </div>
            <button @click="reprocessar" class="btn-retry">🔄 Tentar Novamente</button>
        </div>

        <div v-else-if="dados" class="content">
            <h1>✅ Processamento Automático Concluído!</h1>

            <div class="success-message">
                <p>✨ Os arquivos foram processados com sucesso:</p>
                <ul>
                    <li>📄 <strong>dados-original.json</strong> - {{ dados.original.length }} linhas</li>
                    <li>📄 <strong>pares-embaralhados.json</strong> - {{ dados.pares.length }} pares</li>
                </ul>
                <p class="info-text">
                    💡 Os JSONs foram salvos no <strong>localStorage</strong> e também disponíveis para download.
                </p>
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
                    <p class="preview-note">Mostrando 5 de {{ dados.original.length }} linhas</p>
                </div>

                <div v-else class="tab-content">
                    <div class="pares-grid">
                        <div v-for="(par, index) in dados.pares.slice(0, 12)" :key="index" class="par-card">
                            <span class="base">{{ par.base }}</span>
                            <span class="arrow">→</span>
                            <span class="combinado">{{ par.combinado }}</span>
                        </div>
                    </div>
                    <p class="preview-note">Mostrando 12 de {{ dados.pares.length }} pares</p>
                </div>
            </div>

            <div class="actions">
                <button @click="baixarArquivos" class="btn-download">
                    💾 Baixar JSONs Novamente
                </button>
                <button @click="reprocessar" class="btn-reset">
                    🔄 Reprocessar
                </button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
    processarExcelAutomaticamente,
    baixarJSON,
    type DadosProcessados
} from './utils/excelProcessor';

const dados = ref<DadosProcessados | null>(null);
const carregando = ref(true);
const erro = ref<string | null>(null);
const tabAtiva = ref<'original' | 'pares'>('original');
const etapaAtual = ref('Iniciando...');

async function processar() {
    try {
        carregando.value = true;
        erro.value = null;

        etapaAtual.value = 'Buscando arquivo Excel...';
        await new Promise(resolve => setTimeout(resolve, 300));

        etapaAtual.value = 'Lendo dados...';
        await new Promise(resolve => setTimeout(resolve, 300));

        // Processa o Excel que está em public/dados.xlsx
        dados.value = await processarExcelAutomaticamente('/dados.xlsx');

        etapaAtual.value = 'Concluído!';
    } catch (err) {
        erro.value = err instanceof Error ? err.message : 'Erro desconhecido ao processar';
        console.error('❌ Erro:', err);
    } finally {
        carregando.value = false;
    }
}

function baixarArquivos() {
    if (!dados.value) return;

    baixarJSON(dados.value.original, 'dados-original.json');
    setTimeout(() => {
        baixarJSON(dados.value!.pares, 'pares-embaralhados.json');
    }, 500);
}

function reprocessar() {
    processar();
}

// Processa automaticamente quando a página carrega
onMounted(() => {
    console.log('🚀 Aplicação iniciada - processando Excel automaticamente...');
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
    width: 60px;
    height: 60px;
    animation: spin 1s linear infinite;
    margin: 0 auto 1.5rem;
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
    font-size: 1.2rem;
    margin: 0.5rem 0;
}

.loading-detail {
    color: #667eea;
    font-weight: 600;
    font-size: 1rem;
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

.error-details {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: left;
}

.error-details p {
    margin: 0 0 0.5rem 0;
    color: #856404;
}

.error-details ul {
    margin: 0.5rem 0 0 1.5rem;
    color: #856404;
}

.error-details code {
    background: #ffeaa7;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
}

.btn-retry {
    background: #e74c3c;
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: transform 0.2s;
    box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
}

.btn-retry:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(231, 76, 60, 0.4);
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
    font-size: 2rem;
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
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}

.success-message li {
    margin: 0.25rem 0;
}

.info-text {
    margin-top: 1rem;
    font-size: 0.95rem;
    font-weight: normal;
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
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    text-align: center;
}

.stat-card h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    opacity: 0.95;
    font-weight: 600;
}

.number {
    font-size: 3.5rem;
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
    font-size: 1.5rem;
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
    line-height: 1.5;
}

.preview-note {
    text-align: center;
    color: #666;
    font-style: italic;
    margin-top: 1rem;
    font-size: 0.9rem;
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
    font-size: 1.3rem;
    font-weight: bold;
}

.actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

.btn-download,
.btn-reset {
    padding: 1rem 2rem;
    font-size: 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    border: none;
    font-weight: 600;
}

.btn-download {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-download:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-reset {
    background: #6c757d;
    color: white;
    box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

.btn-reset:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(108, 117, 125, 0.4);
}

.btn-download:active,
.btn-reset:active {
    transform: translateY(0);
}
</style>
```

## Estrutura do Projeto:
```
projeto/
└── frontend/
├── public/
│ └── dados.xlsx ← COLOQUE SEU EXCEL AQUI!
├── src/
│ ├── utils/
│ │ └── excelProcessor.ts
│ ├── App.vue
│ └── main.ts
├── package.json
└── vite.config.ts