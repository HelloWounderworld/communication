<template>
    <div class="wrapper">
        <div class="check-container">

            <!-- Checkbox Teal -->
            <label class="check-item" :class="{ ativo: ativo === 'a', teal: ativo === 'a' }" @click="alternar('a')">
                <input type="checkbox" hidden />
                <span class="box"></span>
                <span class="label-text">Teal</span>
            </label>

            <!-- Checkbox Red — só aparece quando permitido -->
            <label v-if="mostrarRed" class="check-item" :class="{ ativo: ativo === 'b', red: ativo === 'b' }"
                @click="alternar('b')">
                <input type="checkbox" hidden />
                <span class="box"></span>
                <span class="label-text">Red</span>
            </label>
        </div>

        <!-- Botão que faz a requisição -->
        <button class="action-btn" @click="fazerRequisicao">
            Enviar Requisição
        </button>

    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Checkbox ativo: 'a', 'b', ou null
const ativo = ref<'a' | 'b' | null>(null)

// Controle de visibilidade do Red
const mostrarRed = ref(false)

// Alternância dos checkboxes
function alternar(opcao: 'a' | 'b') {
    if (ativo.value === opcao) {
        ativo.value = null
    } else {
        ativo.value = opcao
    }
}

// ------- Função que faz a requisição à API -------
async function fazerRequisicao() {
    try {
        console.log("📡 Enviando requisição...")

        // Corpo básico
        let payload: any = {
            base: true
        }

        // Se TEAL está ativo → inclui no payload
        if (ativo.value === 'a') {
            payload.teal = true
        }

        // Faz a requisição
        const res = await fetch("http://localhost:8000/api/teste", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })

        const data = await res.json()
        console.log("🔍 Resposta:", data)

        // Se API retornou algo diferente de false → mostra o checkbox Red
        if (data.show_red === true) {
            mostrarRed.value = true
        }

    } catch (err) {
        console.error("❌ Erro na requisição:", err)
    }
}
</script>

<style scoped>
.wrapper {
    background: #222;
    padding: 2rem;
}

.check-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 2rem;
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

/* Caixa visual */
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

/* Check ✓ */
.check-item.ativo .box::after {
    content: "✓";
    font-size: 18px;
    color: white;
}

/* Teal */
.check-item.teal.ativo .box {
    background: #009688;
    border-color: #00796b;
}

/* Red */
.check-item.red.ativo .box {
    background: #f44336;
    border-color: #c62828;
}

/* Hover suave */
.check-item:hover .box {
    border-color: #aaa;
}

/* botão da requisição */
.action-btn {
    margin-top: 2rem;
    display: block;
    padding: 12px 24px;
    font-size: 1rem;
    border-radius: 8px;
    cursor: pointer;
    border: none;
    background: #2196f3;
    color: #fff;
    transition: background 0.25s ease;
}

.action-btn:hover {
    background: #1976d2;
}
</style>