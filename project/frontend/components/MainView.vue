<template>
    <div id="main-view">
        <!-- 🔒 Tela de Login -->
        <transition name="slide">
            <div v-if="showLogin" class="login-overlay">
                <div class="login-box">
                    <h2>🔑 Login do Usuário</h2>
                    <input v-model="user" placeholder="Usuário" class="login-input" @keyup.enter="focusPassword" />
                    <input v-model="pass" placeholder="Senha" type="password" class="login-input" ref="passInput"
                        @keyup.enter="doLogin" />
                    <button @click="doLogin" class="login-btn">Entrar</button>
                    <p v-if="loginError" class="login-error">{{ loginError }}</p>
                </div>
            </div>
        </transition>

        <!-- 📊 Tela Principal -->
        <div v-else class="content" @mousemove="resetTimer" @keydown="resetTimer">
            <div class="header">
                <h1>📘 Avaliação de Textos</h1>
                <div class="progress">
                    <div class="progress-bar" :style="{ width: progressPercent + '%' }"></div>
                </div>
                <div class="progress-info">
                    <span>{{ currentIndex + 1 }} / {{ totalPairs }}</span>
                    <button @click="logout" class="logout-btn">Sair</button>
                </div>
            </div>

            <div v-if="currentPair" class="card">
                <div class="text-box">
                    <p v-html="currentPair.txt"></p>
                </div>
                <div class="title-box">
                    <h2>{{ currentPair.p.t }}</h2>
                </div>

                <div class="score-buttons">
                    <button v-for="n in 4" :key="n" class="score-btn" @click="submitScore(n)">
                        {{ n }}
                    </button>
                </div>
            </div>

            <div v-else class="done">
                <h2>🎉 Parabéns!</h2>
                <p>Você completou todas as avaliações!</p>
                <button @click="logout" class="logout-btn">Sair</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue"
import {
    loginUser,
    fetchPairs,
    sendScore,
    loadSession,
    isSessionValid,
    updateLastActivity,
    logoutUser,
    type ParesData,
} from "@/utils/api"

// ===============================
// 🔧 Estados principais
// ===============================
const showLogin = ref(true)
const user = ref("")
const pass = ref("")
const loginError = ref("")
const pairs = ref<ParesData | null>(null)
const currentIndex = ref(0)
const totalPairs = ref(0)
const inactivityTimer = ref<number | null>(null)
const passInput = ref<HTMLInputElement | null>(null)

// ===============================
// 🧠 Computed
// ===============================
const currentPair = computed(() => pairs.value?.all[currentIndex.value])
const progressPercent = computed(() =>
    totalPairs.value ? ((currentIndex.value + 1) / totalPairs.value) * 100 : 0
)

// ===============================
// ⚙️ Login & Sessão
// ===============================
async function doLogin() {
    try {
        loginError.value = ""
        const res = await loginUser(user.value.trim(), pass.value.trim())
        console.log("🔑 Login:", res)
        await loadUserPairs()
        showLogin.value = false
        startInactivityTimer()
    } catch (err: any) {
        loginError.value = err.message || "Erro no login."
    }
}

async function loadUserPairs() {
    const res = await fetchPairs(user.value)
    pairs.value = res.pairs
    totalPairs.value = res.pairs.all.length
    currentIndex.value = res.next || 0
    updateLastActivity()
}

function logout() {
    logoutUser()
    showLogin.value = true
    user.value = ""
    pass.value = ""
    pairs.value = null
    totalPairs.value = 0
    currentIndex.value = 0
    stopInactivityTimer()
}

// ===============================
// ⏱️ Timer de Inatividade
// ===============================
function startInactivityTimer() {
    stopInactivityTimer()
    inactivityTimer.value = window.setInterval(() => {
        if (!isSessionValid(20)) {
            alert("Sessão expirada! Faça login novamente.")
            logout()
        }
    }, 60000) // checa a cada 1 min
}

function stopInactivityTimer() {
    if (inactivityTimer.value) {
        clearInterval(inactivityTimer.value)
        inactivityTimer.value = null
    }
}

function resetTimer() {
    updateLastActivity()
}

// ===============================
// 🧩 Pontuação
// ===============================
async function submitScore(score: number) {
    if (!currentPair.value || !pairs.value) return
    try {
        const idx = currentPair.value.idx
        const p_idx = currentIndex.value
        await sendScore(user.value, idx, p_idx, score)

        if (currentIndex.value + 1 < totalPairs.value) {
            currentIndex.value++
            updateLastActivity()
        } else {
            alert("Você concluiu todas as avaliações! 🎉")
        }
    } catch (err) {
        console.error("Erro ao enviar score:", err)
    }
}

function focusPassword() {
    nextTick(() => passInput.value?.focus())
}

// ===============================
// 🚀 Inicialização
// ===============================
onMounted(async () => {
    const session = loadSession()
    if (session && isSessionValid()) {
        user.value = session.user
        pass.value = session.pass
        await loadUserPairs()
        showLogin.value = false
        startInactivityTimer()
    }
})

onBeforeUnmount(() => {
    stopInactivityTimer()
})
</script>

<style scoped>
/* ==============================
  🔹 Layout geral
  ============================== */
#main-view {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    min-height: 100vh;
    overflow: hidden;
    position: relative;
}

/* ==============================
  🔹 Tela de Login
  ============================== */
.login-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(30, 30, 30, 0.95);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
}

.login-box {
    background: #fff;
    color: #222;
    padding: 2rem 3rem;
    border-radius: 12px;
    text-align: center;
    width: 360px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
}

.login-input {
    width: 100%;
    padding: 0.75rem;
    margin-top: 1rem;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 1rem;
}

.login-btn {
    margin-top: 1.5rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    border-radius: 8px;
    cursor: pointer;
    width: 100%;
}

.login-error {
    margin-top: 1rem;
    color: red;
    font-size: 0.9rem;
}

/* Animação de slide */
.slide-enter-active,
.slide-leave-active {
    transition: transform 0.5s ease;
}

.slide-enter-from,
.slide-leave-to {
    transform: translateY(-100%);
}

/* ==============================
  🔹 Conteúdo principal
  ============================== */
.content {
    padding: 2rem;
    text-align: center;
}

.header h1 {
    margin-bottom: 1rem;
}

/* Barra de progresso */
.progress {
    background: rgba(255, 255, 255, 0.3);
    height: 10px;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-bar {
    height: 100%;
    background: #00ffcc;
    transition: width 0.3s ease;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
}

/* Caixa de texto e título */
.card {
    background: #fff;
    color: #222;
    margin: 2rem auto;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    max-width: 700px;
}

.text-box {
    background: #f9f9f9;
    padding: 1rem;
    border-radius: 6px;
    min-height: 150px;
}

.title-box h2 {
    margin-top: 1.5rem;
    color: #444;
}

/* Botões de score */
.score-buttons {
    display: flex;
    justify-content: space-around;
    margin-top: 2rem;
}

.score-btn {
    background: #667eea;
    color: #fff;
    font-size: 1.2rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    cursor: pointer;
    border: none;
    transition: transform 0.2s, background 0.3s;
}

.score-btn:hover {
    transform: scale(1.1);
    background: #5a6fdc;
}

/* ==============================
  🔹 Logout & Fim
  ============================== */
.logout-btn {
    background: #e74c3c;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s;
}

.logout-btn:hover {
    background: #c0392b;
}

.done {
    text-align: center;
    margin-top: 4rem;
}
</style>