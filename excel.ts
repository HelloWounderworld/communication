// src/utils/excelProcessor.ts
import * as XLSX from 'xlsx';

export interface LinhaExcel {
  [coluna: string]: string | number;
}

export interface Par {
  base: string | number;
  combinado: string | number;
}

export interface DadosProcessados {
  original: LinhaExcel[];
  pares: Par[];
}

/**
 * Embaralha um array (Fisher–Yates)
 */
export function embaralhar<T>(array: T[]): T[] {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

/**
 * Lê o Excel do sistema de arquivos (usando window.fs)
 */
export async function lerExcelDoSistema(caminhoArquivo: string): Promise<LinhaExcel[]> {
  try {
    // Lê o arquivo usando a API window.fs
    const dados = await window.fs.readFile(caminhoArquivo);
    
    // Converte para workbook
    const workbook = XLSX.read(dados, { type: 'array' });
    const sheet = workbook.Sheets['Sheet1'];

    if (!sheet) {
      throw new Error('❌ A aba "Sheet1" não foi encontrada.');
    }

    return XLSX.utils.sheet_to_json<LinhaExcel>(sheet);
  } catch (erro) {
    console.error('❌ Erro ao ler Excel:', erro);
    throw erro;
  }
}

/**
 * Gera pares embaralhados a partir das linhas do Excel
 */
export function gerarPares(dados: LinhaExcel[]): Par[] {
  const todosPares: Par[] = [];

  dados.slice(1).forEach((linha) => {
    const valores = Object.values(linha);
    const base = valores[0];
    const outros = valores.slice(1);
    const pares = outros.map((v) => ({ base, combinado: v }));
    todosPares.push(...embaralhar(pares));
  });

  return embaralhar(todosPares);
}

/**
 * Baixa um arquivo JSON no navegador
 */
export function baixarJSON(dados: unknown, nomeArquivo: string): void {
  const blob = new Blob([JSON.stringify(dados, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeArquivo;
  link.click();
  URL.revokeObjectURL(url);
}

/**
 * Processa o Excel e gera os arquivos JSON automaticamente
 */
export async function processarExcelAutomaticamente(
  caminhoArquivo: string
): Promise<DadosProcessados> {
  try {
    console.log('📂 Lendo arquivo Excel...');
    const dados = await lerExcelDoSistema(caminhoArquivo);
    
    console.log('🔀 Gerando pares embaralhados...');
    const pares = gerarPares(dados);
    
    console.log('💾 Salvando JSONs...');
    
    // Salva JSON original
    baixarJSON(dados, 'dados-original.json');
    
    // Pequeno delay para não conflitar os downloads
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Salva pares embaralhados
    baixarJSON(pares, 'pares-embaralhados.json');
    
    console.log('✅ Processamento concluído!');
    
    return { original: dados, pares };
  } catch (erro) {
    console.error('❌ Erro no processamento:', erro);
    throw erro;
  }
}