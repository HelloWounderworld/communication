function recursiveFunction(n) {
    if (n <= 0) return;
    recursiveFunction(n - 1);
}

// Função para monitorar memória
function monitorMemory() {
    const memory = process.memoryUsage();
    console.log(`Memória utilizada: ${memory.heapUsed / 1024 / 1024} MB`);
}

// Chama a função recursiva e monitora a memória
function runWithMonitoring() {
    const interval = setInterval(monitorMemory, 1000); // Monitora a cada segundo
    recursiveFunction(10000); // Exemplo de chamada recursiva
    clearInterval(interval); // Para o monitoramento após a execução
}

runWithMonitoring();

async function someAsyncFunction(item) {
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log(`Processando: ${item}`);
            resolve(item);
        }, 1000);
    });
}

async function processArraySequentially(arr) {
    for (const item of arr) {
        await someAsyncFunction(item);
        monitorMemory(); // Monitora a memória após cada item
    }
    console.log("Todos os itens processados.");
}

// Função para monitorar memória
function monitorMemory() {
    const memory = process.memoryUsage();
    console.log(`Memória utilizada: ${memory.heapUsed / 1024 / 1024} MB`);
}

// Executa a função com monitoramento
async function runWithMonitoring() {
    const items = [1, 2, 3, 4, 5];
    await processArraySequentially(items);
}

runWithMonitoring();