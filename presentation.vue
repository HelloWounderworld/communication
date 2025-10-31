<template>
    <div class="wrapper">
        <div class="box">
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
            <div></div>
        </div>
        <div class="app-container">
            <header>
                <div class="two alt-two">
                    <h1>Alternate
                        <span>Example Tagline Text</span>
                    </h1>
                </div>
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
                        <li v-for="(title, index) in titles" :key="index" class="title-item">{{ title }}</li>
                    </ul>
                </div>
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
            // Limpa os títulos antes de gerar novos
            this.titles = [];
            // Gera títulos e os adiciona com um pequeno atraso para a animação
            const newTitles = this.generateTitles(this.inputText);
            newTitles.forEach((title, index) => {
                setTimeout(() => {
                    this.titles.push(title);
                }, index * 100); // Atraso de 100ms entre cada título
            });
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

<style scoped>
.two h1 {
    text-transform: capitalize;
}

.two h1:before {
    position: absolute;
    left: 0;
    bottom: 0;
    width: 60px;
    height: 2px;
    content: "";
    background-color: #c50000;
}

.two h1 span {
    font-size: 13px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 4px;
    line-height: 3em;
    padding-left: 0.25em;
    color: rgba(0, 0, 0, 0.4);
    padding-bottom: 10px;
}

.alt-two h1 {
    text-align: center;
}

.alt-two h1:before {
    left: 50%;
    margin-left: -30px;
}

.app-container {
    max-width: 800px;
    margin: auto;
}

.container {
    display: grid;
    grid-template-columns: 1fr 200px 1fr;
    gap: 20px;
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
    resize: none;
}

button {
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
}

ul {
    list-style-type: none;
    padding: 0;
}

.title-item {
    margin: 10px 0;
    padding: 10px;
    background-color: #f0f0f0;
    border-radius: 5px;
    opacity: 0;
    transform: translateX(100%);
    animation: slideIn 0.5s forwards;
}

.wrapper {
    position: absolute;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #24C6DC;
    background: -webkit-linear-gradient(to bottom, #514A9D, #24C6DC);
    background: linear-gradient(to bottom, #514A9D, #24C6DC);
}

.box div {
    position: absolute;
    width: 60px;
    height: 60px;
    background-color: transparent;
    border: 6px solid rgba(255, 255, 255, 0.8);
}

.box div:nth-child(1) {
    top: 12%;
    left: 42%;
    animation: animate 10s linear infinite;
}

.box div:nth-child(2) {
    top: 70%;
    left: 50%;
    animation: animate 7s linear infinite;
}

.box div:nth-child(3) {
    top: 17%;
    left: 6%;
    animation: animate 9s linear infinite;
}

.box div:nth-child(4) {
    top: 20%;
    left: 60%;
    animation: animate 10s linear infinite;
}

.box div:nth-child(5) {
    top: 67%;
    left: 10%;
    animation: animate 6s linear infinite;
}

.box div:nth-child(6) {
    top: 80%;
    left: 70%;
    animation: animate 12s linear infinite;
}

.box div:nth-child(7) {
    top: 60%;
    left: 80%;
    animation: animate 15s linear infinite;
}

.box div:nth-child(8) {
    top: 32%;
    left: 25%;
    animation: animate 16s linear infinite;
}

.box div:nth-child(9) {
    top: 90%;
    left: 25%;
    animation: animate 9s linear infinite;
}

.box div:nth-child(10) {
    top: 20%;
    left: 80%;
    animation: animate 5s linear infinite;
}

@keyframes animate {
    0% {
        transform: scale(0) translateY(-90px) rotate(360deg);
        opacity: 1;
    }

    100% {
        transform: scale(1.3) translateY(-90px) rotate(-180deg);
        border-radius: 50%;
        opacity: 0;
    }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(100%);
    }

    to {
        opacity: 1;
        transform: translateX(0);
    }
}
</style>