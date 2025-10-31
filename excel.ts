import * as XLSX from "xlsx"
import * as fs from "fs"

interface LinhaExcel {
  [coluna: string]: string | number
}

interface Par {
  base: string | number
  combinado: string | number
}

/**
 * Embaralha um array (Fisher–Yates)
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
 * Lê o Excel e retorna o conteúdo da aba "Sheet1" no formato JSON
 */
function lerExcelComoJson(caminho: string): LinhaExcel[] {
  const workbook = XLSX.readFile(caminho)

  const sheetName = "Sheet1"

  // Verifica se a aba existe
  if (!workbook.Sheets[sheetName]) {
    throw new Error(`❌ A aba "${sheetName}" não foi encontrada no arquivo Excel.`)
  }

  const worksheet = workbook.Sheets[sheetName]
  return XLSX.utils.sheet_to_json<LinhaExcel>(worksheet)
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
 * Função principal
 */
function main() {
  const caminhoArquivo = "./dados.xlsx"

  // 1️⃣ Lê o Excel (somente a aba "Sheet1")
  const dados = lerExcelComoJson(caminhoArquivo)

  // 2️⃣ Guarda formato original
  const backupOriginal = JSON.parse(JSON.stringify(dados))
  fs.writeFileSync("./backup_original.json", JSON.stringify(backupOriginal, null, 2))

  // 3️⃣ Gera pares embaralhados
  const paresGerados = gerarPares(dados)

  // 4️⃣ Salva resultado
  fs.writeFileSync("./pares_gerados.json", JSON.stringify(paresGerados, null, 2))

  console.log("✅ Processo concluído!")
  console.log(`📄 Total de pares gerados: ${paresGerados.length}`)
}

main()
