<template>
    <div>
        <h1>衆議院選挙2024 ボートマッチ</h1>
        <h2>テーマ</h2>
        <p>選択してください (選択可)</p>
        <div>
            <label><input type="checkbox" v-model="themes" value="取り組ん"> 取り組ん</label>
            <label><input type="checkbox" v-model="themes" value="モニタリング"> モニタリング</label>
            <label><input type="checkbox" v-model="themes" value="教育"> 教育</label>
            <label><input type="checkbox" v-model="themes" value="だまされた大賞"> だまされた大賞</label>
            <label><input type="checkbox" v-model="themes" value="エネルギー"> エネルギー</label>
            <label><input type="checkbox" v-model="themes" value="カネ"> カネ</label>
            <label><input type="checkbox" v-model="themes" value="いってQ"> いってQ</label>
            <label><input type="checkbox" v-model="themes" value="プロジェクト"> プロジェクト</label>
            <label><input type="checkbox" v-model="themes" value="世界丸見え"> 世界丸見え</label>
            <label><input type="checkbox" v-model="themes" value="ジェンダー"> ジェンダー</label>
        </div>
        <button @click="selectAllThemes">すべてのテーマを選択</button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            themes: []
        };
    },
    methods: {
        selectAllThemes() {
            this.themes = ["取り組ん", "モニタリング", "教育", "だまされた大賞", "エネルギー", "カネ", "いってQ", "プロジェクト", "世界丸見え", "ジェンダー"];
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