<template>
    <div class="app-container">
        <header class="header">
            <h1>Título do Processador de Texto</h1>
        </header>
        <div class="container">
            <div class="left-column">
                <textarea v-model="inputText" placeholder="Digite seu texto aqui..."></textarea>
            </div>
            <div class="middle-column">
                <button @click="processText">Processar</button>
            </div>
            <div class="right-column">
                <ul>
                    <li v-for="(title, index) in titles" :key="index">{{ title }}</li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            inputText: '',
            titles: []
        };
    },
    methods: {
        processText() {
            // Aqui você pode adicionar lógica para gerar títulos a partir do texto
            this.titles = this.generateTitles(this.inputText);
        },
        generateTitles(text) {
            // Exemplo simples de geração de títulos
            return [
                `Título 1: ${text.substring(0, 10)}`,
                `Título 2: ${text.substring(0, 15)}`,
                `Título 3: ${text.substring(0, 20)}`,
                `Título 4: ${text.substring(0, 25)}`,
                `Título 5: ${text.substring(0, 30)}`,
                `Título 6: ${text.substring(0, 35)}`,
                `Título 7: ${text.substring(0, 40)}`,
                `Título 8: ${text.substring(0, 45)}`,
                `Título 9: ${text.substring(0, 50)}`,
                `Título 10: ${text.substring(0, 55)}`
            ];
        }
    }
};
</script>

<style>
.app-container {
    max-width: 800px;
    /* Largura máxima da aplicação */
    margin: auto;
    /* Centraliza a aplicação na tela */
}

.header {
    text-align: center;
    /* Centraliza o texto do cabeçalho */
    margin-bottom: 20px;
    /* Espaçamento abaixo do cabeçalho */
}

.container {
    display: grid;
    grid-template-columns: 1fr 200px 1fr;
    /* Três colunas */
    gap: 20px;
    /* Espaçamento entre colunas */
}

.left-column {
    grid-column: 1;
}

.middle-column {
    grid-column: 2;
    display: flex;
    justify-content: center;
    align-items: center;
}

.right-column {
    grid-column: 3;
}

textarea {
    width: 100%;
    height: 300px;
}

button {
    padding: 10px 20px;
    font-size: 16px;
}

ul {
    list-style-type: none;
    padding: 0;
}

li {
    margin: 10px 0;
    padding: 10px;
    background-color: #f0f0f0;
    border-radius: 5px;
}
</style>