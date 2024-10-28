<template>
    <div class="container">
        <div class="container__progressbars" ref="progressbarsContainer">
            <!-- As barras de progresso serão adicionadas aqui -->
        </div>
        <button @click="addProgressBar">Adicionar Barra de Progresso</button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            colorNode: 'hsl(110, 100%, 60%)',
            percentNode: 30,
        };
    },
    methods: {
        strokeDashoffset(num) {
            return 440 - (440 * num) / 100;
        },
        addProgressBar() {
            const progressBar = document.createElement('div');
            progressBar.className = 'progressbar';

            progressBar.innerHTML = `
          <svg class="progressbar__svg">
            <circle cx="80" cy="80" r="70" class="progressbar__svg-circle circle-node shadow-node" 
                    style="stroke-dashoffset: ${this.strokeDashoffset(this.percentNode)}; stroke: ${this.colorNode};">
            </circle>
          </svg>
          <span class="progressbar__text shadow-node">Node.js</span>
        `;

            this.$refs.progressbarsContainer.appendChild(progressBar);
        },
    },
};
</script>

<style lang="scss" scoped>
$color-node: hsl(110, 100%, 60%);
$porcent-node: 30;

.container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: hsl(0, 0%, 20%);
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
    stroke: hsl(0, 0%, 100%);
    stroke-linecap: round;
    transform: translate(5px, 5px);
}

.shadow {
    &-node {
        filter: drop-shadow(0 0 5px $color-node);
    }
}

.circle {
    &-node {
        animation: anim_circle-node 1s ease-in-out forwards;
    }
}

.progressbar__text {
    position: absolute;
    top: 50%;
    left: 50%;
    padding: 0.25em 0.5em;
    color: hsl(0, 0%, 100%);
    font-family: Arial, Helvetica, sans-serif;
    border-radius: 0.25em;
    transform: translate(-50%, -50%) rotate(90deg);
}

@keyframes anim_circle-node {
    to {
        stroke-dashoffset: strokeDashoffset($porcent-node);
    }
}
</style>