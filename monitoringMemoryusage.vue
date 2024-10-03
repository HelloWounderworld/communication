<template>
    <div>
        <h1>Monitoramento de Memória</h1>
        <p>Uso de memória: {{ memoryUsage }} MB</p>
        <button @click="startRecursiveFunction">Iniciar Função Recursiva</button>
        <button @click="stopMonitoring">Parar Monitoramento</button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            memoryUsage: 0,
            intervalId: null,
            recursionDepth: 0,
        };
    },
    methods: {
        updateMemoryUsage() {
            if (window.performance.memory) {
                this.memoryUsage = (window.performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(2);
            } else {
                console.warn("A API de memória não está disponível neste navegador.");
            }
        },
        startMonitoring() {
            this.updateMemoryUsage(); // Atualiza imediatamente
            this.intervalId = setInterval(this.updateMemoryUsage, 1000); // Atualiza a cada segundo
        },
        stopMonitoring() {
            clearInterval(this.intervalId);
        },
        recursiveFunction(n) {
            if (n <= 0) return;
            this.recursionDepth++;
            this.recursiveFunction(n - 1);
        },
        startRecursiveFunction() {
            this.recursionDepth = 0; // Reseta a profundidade antes de iniciar
            this.startMonitoring(); // Inicia o monitoramento
            this.recursiveFunction(10000); // Chama a função recursiva
            this.stopMonitoring(); // Para o monitoramento após a execução
        },
    },
};
</script>

<style>
/* Estilos opcionais */
</style>