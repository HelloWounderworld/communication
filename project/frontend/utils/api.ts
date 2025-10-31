// frontend/src/utils/api.ts
import axios from "axios"

// ==========================
// ⚙️ Configuração base da API
// ==========================

// 👉 Ajuste conforme o endereço onde roda seu backend FastAPI
const API_BASE = "http://127.0.0.1:8000/api"

// ==========================
// 🧩 Tipos auxiliares
// ==========================

export interface Par {
  txt: string
  p: { t: string; l: number; c: string }
  idx: number
  s?: number
}

export interface ParesData {
  l1: Par[]
  l2: Par[]
  l3: Par[]
  all: Par[]
}

export interface UserSession {
  user: string
  pass: string
  nextIndex: number
}

// ==========================
// 📦 Armazenamento local
// ==========================
export function saveSession(session: UserSession) {
  localStorage.setItem("session", JSON.stringify(session))
}

export function loadSession(): UserSession | null {
  const data = localStorage.getItem("session")
  return data ? JSON.parse(data) : null
}

export function clearSession() {
  localStorage.removeItem("session")
}

// ==========================
// 🚀 Requisições HTTP
// ==========================

/**
 * Faz login ou cria usuário.
 * Se o usuário já existir, retorna o progresso atual.
 */
export async function loginUser(user: string, pass: string) {
  const { data } = await axios.post(`${API_BASE}/user`, { u: user, p: pass })
  if (!data.ok) throw new Error("Falha ao autenticar usuário.")
  saveSession({ user, pass, nextIndex: data.next || 0 })
  return data
}

/**
 * Busca pares embaralhados do usuário logado.
 */
export async function fetchPairs(user: string) {
  const { data } = await axios.post(`${API_BASE}/pairs`, { u: user })
  if (!data.ok) throw new Error("Falha ao carregar pares.")
  return data as { ok: boolean; u: string; pairs: ParesData; next: number }
}

/**
 * Envia a pontuação do usuário para o backend.
 */
export async function sendScore(
  user: string,
  idx: number,
  p_idx: number,
  score: number
) {
  const { data } = await axios.post(`${API_BASE}/score`, {
    u: user,
    idx,
    p_idx,
    s: score,
  })
  if (!data.ok) throw new Error("Falha ao salvar pontuação.")
  return data
}

/**
 * Realiza logout (apaga sessão local)
 */
export function logoutUser() {
  clearSession()
}

/**
 * Verifica se há sessão ativa e se não expirou
 */
export function isSessionValid(timeoutMinutes = 20): boolean {
  const lastActivity = localStorage.getItem("lastActivity")
  const now = Date.now()

  if (!lastActivity) return false

  const diffMinutes = (now - Number(lastActivity)) / 1000 / 60
  return diffMinutes < timeoutMinutes
}

export function updateLastActivity() {
  localStorage.setItem("lastActivity", String(Date.now()))
}
