// src/utils/excelProcessor.ts
import * as XLSX from "xlsx"

export interface LinhaExcel {
  [coluna: string]: string | number
}

export interface Par {
  base: string | number
  combinado: string | number
}

/**
 * Embaralha um array (Fisher–Yates)
 */
export function embaralhar<T>(array: T[]): T[] {
  const arr = [...array]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

/**
 * Converte um ArrayBuffer de Excel em JSON
 */
export function lerExcelComoJson(arrayBuffer: ArrayBuffer): LinhaExcel[] {
  const bytes = new Uint8Array(arrayBuffer)
  const workbook = XLSX.read(bytes, { type: "array" })
  const sheet = workbook.Sheets["Sheet1"]

  if (!sheet) {
    throw new Error('❌ A aba "Sheet1" não foi encontrada.')
  }

  return XLSX.utils.sheet_to_json<LinhaExcel>(sheet)
}

/**
 * Gera pares embaralhados a partir das linhas do Excel
 */
export function gerarPares(dados: LinhaExcel[]): Par[] {
  const todosPares: Par[] = []

  dados.slice(1).forEach((linha) => {
    const valores = Object.values(linha)
    const base = valores[0]
    const outros = valores.slice(1)
    const pares = outros.map((v) => ({ base, combinado: v }))
    todosPares.push(...embaralhar(pares))
  })

  return embaralhar(todosPares)
}

/**
 * Cria e baixa um arquivo JSON no navegador
 */
export function baixarJSON(dados: unknown, nome: string) {
  const blob = new Blob([JSON.stringify(dados, null, 2)], {
    type: "application/json",
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = nome
  link.click()
  URL.revokeObjectURL(url)
}
