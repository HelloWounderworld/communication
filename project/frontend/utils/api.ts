// frontend/src/utils/api.ts
import axios from "axios";

// ==========================
// ⚙️ Configuração base
// ==========================

// 👉 Altere se o backend estiver em outro endereço
const API_BASE = "http://127.0.0.1:8000/api";

// ==========================
// 🧩 Tipos auxiliares
// ==========================

export interface Par {
  txt: string;
  p: { t: string; l: number; c: string };
  idx: number;
  s?: number;
  c?: string;
}

export interface ParesResponse {
  ok: boolean;
  u: string;
  pairs: { l1: Par[]; l2: Par[]; l3: Par[]; all: Par[] };
  next: number;
}

export interface UserSession {
  user: string;
  pass: string;
  nextIndex: number;
}

// ==========================
// 💾 Sessão local
// ==========================

export function saveSession(session: UserSession) {
  localStorage.setItem("session", JSON.stringify(session));
  updateLastActivity();
}

export function loadSession(): UserSession | null {
  const s = localStorage.getItem("session");
  return s ? JSON.parse(s) : null;
}

export function clearSession() {
  localStorage.removeItem("session");
  localStorage.removeItem("lastActivity");
}

export function updateLastActivity() {
  localStorage.setItem("lastActivity", String(Date.now()));
}

export function isSessionValid(timeoutMinutes = 20): boolean {
  const last = localStorage.getItem("lastActivity");
  if (!last) return false;
  const diff = (Date.now() - Number(last)) / 1000 / 60;
  return diff < timeoutMinutes;
}

export function logoutUser() {
  clearSession();
}

// ==========================
// 🚀 Requisições HTTP
// ==========================

/**
 * Login / criação de usuário.
 * Se o usuário existir, retorna progresso atual.
 */
export async function loginUser(u: string, pw: string) {
  const { data } = await axios.post(`${API_BASE}/user`, { u, p: pw });
  if (!data.ok) throw new Error(data.detail || "Falha ao autenticar usuário.");
  return data;
}

/**
 * Busca os pares embaralhados do usuário.
 */
export async function fetchPairs(u: string) {
  const { data } = await axios.post(`${API_BASE}/pairs`, { u });
  if (!data.ok) throw new Error(data.detail || "Falha ao carregar pares.");
  return data as ParesResponse;
}

/**
 * Envia score + comentário obrigatório.
 */
export async function sendScore(body: {
  u: string;
  pw: string;
  idx: number;
  p_idx: number;
  s: number;
  c: string;
}) {
  const { data } = await axios.post(`${API_BASE}/score`, body);
  if (!data.ok) throw new Error(data.detail || "Erro ao salvar score.");
  return data;
}
