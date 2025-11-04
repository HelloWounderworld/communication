<template>
    <div id="app">
        <!-- TELA DE LOGIN -->
        <transition name="slide">
            <div v-if="!logado" class="login-container">
                <h2>🔐 Login</h2>
                <input v-model="usuario" type="text" placeholder="Usuário" />
                <input v-model="senha" type="password" placeholder="Senha" />
                <button @click="login">Entrar</button>
                <p v-if="erro" class="erro">{{ erro }}</p>
            </div>
        </transition>

        <!-- TELA PRINCIPAL -->
        <div v-else class="main-container" @mousemove="atualizarAtividade" @keydown="atualizarAtividade">
            <header>
                <h1>📘 Avaliação de Textos</h1>
                <button class="logout" @click="logout">Sair</button>
            </header>

            <!-- Barra de progresso -->
            <div class="progress-container">
                <div class="progress-bar" :style="{ width: progresso + '%' }"></div>
            </div>

            <section v-if="parAtual" class="avaliacao-section">
                <div class="texto-box">
                    <p class="texto">{{ parAtual.txt }}</p>
                </div>

                <div class="titulo-box">
                    <p class="titulo">➡ {{ parAtual.p.t }}</p>
                </div>

                <textarea v-model="comentario" class="comment-box"
                    placeholder="Digite o motivo da sua escolha (obrigatório)..."></textarea>

                <div class="botoes">
                    <button v-for="n in [1, 2, 3, 4]" :key="n" class="score-btn" @click="enviarScore(n)">
                        {{ n }}
                    </button>
                </div>
            </section>

            <section v-else class="final-section">
                <h2>🎉 Você concluiu todas as avaliações!</h2>
            </section>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { loginUser, fetchPairs, sendScore, logoutUser, updateLastActivity, isSessionValid, loadSession, saveSession } from "@/utils/api"

const usuario = ref("")
const senha = ref("")
const logado = ref(false)
const erro = ref("")
const pares = ref<any[]>([])
const indice = ref(0)
const comentario = ref("")

const parAtual = computed(() => pares.value[indice.value])
const progresso = computed(() =>
    pares.value.length ? (indice.value / pares.value.length) * 100 : 0
)

async function login() {
    erro.value = ""
    try {
        const data = await loginUser(usuario.value, senha.value)
        logado.value = true
        saveSession({ user: usuario.value, pass: senha.value, nextIndex: data.next || 0 })

        const paresData = await fetchPairs(usuario.value)
        pares.value = paresData.pairs.all
        indice.value = paresData.next || 0
        updateLastActivity()
    } catch (err: any) {
        erro.value = err.message || "Erro ao efetuar login."
    }
}

async function enviarScore(score: number) {
    if (!comentario.value.trim()) {
        alert("⚠️ É obrigatório justificar o motivo da sua pontuação.")
        return
    }

    try {
        const par = parAtual.value
        const body = {
            u: usuario.value,
            pw: senha.value,
            idx: par.idx,
            p_idx: indice.value,
            s: score,
            c: comentario.value,
        }
        await sendScore(body)

        comentario.value = ""
        indice.value++
        updateLastActivity()
    } catch (err: any) {
        alert(err.message || "Erro ao enviar score.")
    }
}

function logout() {
    logoutUser()
    logado.value = false
    usuario.value = ""
    senha.value = ""
    pares.value = []
    indice.value = 0
}

function atualizarAtividade() {
    updateLastActivity()
}

// Logout automático após 20 minutos de inatividade
onMounted(() => {
    const sessao = loadSession()
    if (sessao && isSessionValid()) {
        usuario.value = sessao.user
        senha.value = sessao.pass
        logado.value = true
        fetchPairs(sessao.user).then((res) => {
            pares.value = res.pairs.all
            indice.value = res.next || 0
        })
    }

    setInterval(() => {
        if (logado.value && !isSessionValid()) {
            alert("Sessão expirada por inatividade. Faça login novamente.")
            logout()
        }
    }, 60000) // checa a cada 1 min
})
</script>

<style scoped>
/* ===== Login ===== */
.login-container {
    position: absolute;
    inset: 0;
    background: #2d2f36;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    animation: slideDown 0.6s ease;
}

.login-container input {
    width: 250px;
    padding: 10px;
    border-radius: 6px;
    border: none;
    outline: none;
    font-size: 1rem;
}

.login-container button {
    background: #667eea;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    transition: 0.2s;
}

.login-container button:hover {
    background: #5563c1;
}

.erro {
    color: #ffb3b3;
    font-weight: bold;
}

/* ===== Main ===== */
.main-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logout {
    background: #e74c3c;
    color: white;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
}

.progress-container {
    height: 12px;
    background: #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    margin: 20px 0;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.3s ease;
}

/* ===== Texto e título ===== */
.texto-box {
    background: #fafafa;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    font-size: 1.1rem;
    margin-bottom: 1rem;
    line-height: 1.6;
}

.titulo-box {
    background: #fff;
    border-left: 4px solid #667eea;
    padding: 0.8rem;
    border-radius: 4px;
    font-weight: bold;
    margin-bottom: 1.5rem;
}

.comment-box {
    width: 100%;
    min-height: 100px;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 1.5rem;
    font-size: 1rem;
    resize: none;
}

.botoes {
    display: flex;
    justify-content: center;
    gap: 1rem;
}

.score-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 14px 24px;
    border-radius: 8px;
    font-size: 1.2rem;
    font-weight: bold;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.score-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
}

.final-section {
    text-align: center;
    padding: 3rem;
}

/* ===== Animations ===== */
@keyframes slideDown {
    from {
        transform: translateY(-100%);
    }

    to {
        transform: translateY(0);
    }
}
</style>