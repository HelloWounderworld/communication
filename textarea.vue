<template>
    <div class="text-area-container">
        <h2>Área de Texto</h2>
        <textarea v-model="inputText" rows="10" placeholder="Digite seu texto aqui..."></textarea>
        <button @click="sendText">Enviar</button>
        <div class="output">
            <h3>Texto Digitado:</h3>
            <p>{{ inputText }}</p>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            inputText: '',
        };
    },
    methods: {
        sendText() {
            if (this.inputText.trim()) {
                alert(`Texto enviado: ${this.inputText}`);
                this.inputText = ''; // Limpar a área de texto após enviar
            } else {
                alert('Por favor, digite algum texto antes de enviar.');
            }
        },
    },
};
</script>

<style scoped>
.text-area-container {
    max-width: 600px;
    margin: auto;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 5px;
    background-color: #f9f9f9;
}

textarea {
    width: 100%;
    margin-bottom: 20px;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    resize: none;
}

button {
    padding: 10px 15px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #0056b3;
}

.output {
    border-top: 1px solid #ccc;
    padding-top: 10px;
}

h3 {
    margin: 0;
}
</style>