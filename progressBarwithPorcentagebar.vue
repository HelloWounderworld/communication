<template>
    <div class="container">
        <div class="container__progressbars">
            <div class="progressbar" v-for="(progress, index) in progressBars" :key="index">
                <svg class="progressbar__svg">
                    <circle cx="80" cy="80" r="70"
                        :class="`progressbar__svg-circle circle-${progress.label.toLowerCase()} shadow-${progress.label.toLowerCase()}`"
                        :style="{
                            strokeDashoffset: strokeDashoffset(progress.percent),
                            stroke: progress.color
                        }"></circle>
                </svg>
                <span class="progressbar__text shadow-{{ progress.label.toLowerCase() }}">{{ progress.label }}</span>
            </div>
        </div>
        <button @click="updateProgress">Atualizar Progresso</button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            progressBars: [
                { label: 'Angular.js', percent: 5, color: 'hsl(0, 100%, 60%)' },
                { label: 'Vue.js', percent: 2, color: 'hsl(145, 100%, 60%)' },
            ],
        };
    },
    methods: {
        strokeDashoffset(num) {
            return 440 - (440 * num) / 100;
        },
        updateProgress() {
            // Atualiza as porcentagens com novos valores
            const newValues = [
                { label: 'Angular.js', percent: 50 },
                { label: 'Vue.js', percent: 80 },
            ];

            // Força a animação reiniciando as barras
            this.progressBars = [...newValues];

            // Espera um tempo para permitir a animação
            this.$nextTick(() => {
                setTimeout(() => {
                    this.progressBars = this.progressBars.map((progress) => ({
                        ...progress,
                        percent: progress.percent, // Atualiza para forçar a animação
                    }));
                }, 50); // Tempo para garantir que a animação ocorra
            });
        },
    },
};
</script>

<style lang="scss" scoped>
$color-black: hsl(0, 0%, 5%);
$color-white: hsl(0, 0%, 100%);
$color-angular: hsl(0, 100%, 60%);
$color-vue: hsl(145, 100%, 60%);

.container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: $color-black;
}

.container__progressbars {
    display: flex;
    justify-content: space-around;
    align-items: center;
    flex-wrap: wrap;
    min-width: 270px;
    width: 100%;
    min-height: 100%;
}

.progressbar {
    position: relative;
    width: 170px;
    height: 170px;
    margin: 1em;
    transform: rotate(-90deg);
}

.progressbar__svg {
    position: relative;
    width: 100%;
    height: 100%;
}

.progressbar__svg-circle {
    width: 100%;
    height: 100%;
    fill: none;
    stroke-width: 10;
    stroke-dasharray: 440;
    stroke-dashoffset: 440;
    stroke: $color-white;
    stroke-linecap: round;
    transform: translate(5px, 5px); // stroke-width / 2
}

.shadow {
    &-angular {
        filter: drop-shadow(0 0 5px $color-angular);
    }

    &-vue {
        filter: drop-shadow(0 0 5px $color-vue);
    }
}

.progressbar__text {
    position: absolute;
    top: 50%;
    left: 50%;
    padding: 0.25em 0.5em;
    color: $color-white;
    font-family: Arial, Helvetica, sans-serif;
    border-radius: 0.25em;
    transform: translate(-50%, -50%) rotate(90deg);
}
</style>