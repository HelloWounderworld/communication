<template>
    <div>
        <h1>衆議院選挙2024 ポートマッチ</h1>
        <h2>結果</h2>
        <p>人気相関: あなたの好みに相関</p>
        <select v-model="selectedOption">
            <option>個別に</option>
        </select>
        <div v-for="(program, index) in programs" :key="index">
            <img :src="program.image" alt="Program Image">
            <p>{{ program.name }}</p>
            <p>{{ program.genre }}</p>
            <p>{{ program.match }}%</p>
        </div>
        <button @click="modifyAnswers">回答を修正する</button>
        <button @click="returnToTheme">テーマ選択に戻る</button>
        <button @click="selectOtherConstituency">他の選挙区を選ぶ</button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            selectedOption: '個別に',
            programs: [
                { image: '', name: 'モニタリング', genre: 'お笑い/バラエティ', match: 0 },
                { image: '', name: 'だまされた大賞', genre: 'お笑い', match: 0 },
                { image: '', name: 'いってQ', genre: 'バラエティ', match: 33 },
                { image: '', name: 'プロジェクトX', genre: 'ドキュメンタリー', match: 100 },
                { image: '', name: 'トリビアの泉', genre: 'お笑い/情報', match: 67 },
                { image: '', name: '日本語探', genre: 'お笑い', match: 100 },
                { image: '', name: '世界丸見え!', genre: 'お笑い/ドキュメンタリー', match: 0 },
            ]
        };
    },
    methods: {
        modifyAnswers() {
            // Lógica para modificar as respostas
        },
        returnToTheme() {
            // Lógica para retornar à seleção de temas
        },
        selectOtherConstituency() {
            // Lógica para selecionar outro distrito eleitoral
        }
    }
};
</script>

<style scoped>
h1 {
    font-size: 24px;
    font-weight: bold;
}

h2 {
    font-size: 20px;
    color: #00AEEF;
}

p {
    font-size: 16px;
}

label {
    display: block;
    margin: 5px 0;
}

button {
    margin-top: 20px;
    padding: 10px 20px;
    background-color: #00AEEF;
    color: white;
    border: none;
    cursor: pointer;
}

button:hover {
    background-color: #007B9E;
}
</style>