<template>
    <svg :viewBox="viewBox" :width="sizePx" :height="sizePx" class="pl">
        <g stroke="currentColor" stroke-linecap="round" stroke-width="1" stroke-dasharray="5 8">
            <g v-for="sector in sectors" :key="sector" :transform="getRotation(sector)">
                <g class="pl__lines">
                    <g class="pl__line-wobble" v-for="ln in lines" :key="ln" :style="getLineWobbleStyle(ln)">
                        <line class="pl__line" x1="16" y1="16" x2="16" y2="23" />
                    </g>
                </g>
            </g>
        </g>
    </svg>
</template>

<script>
export default {
    data() {
        return {
            sectors: 24,
            lines: 4,
            size: 32,
        };
    },
    computed: {
        viewBox() {
            return `0 0 ${this.size} ${this.size}`;
        },
        sizePx() {
            return `${this.size}px`;
        },
    },
    methods: {
        getRotation(sector) {
            const angle = (-360 / this.sectors) * sector;
            const center = this.size / 2;
            return `rotate(${angle}, ${center}, ${center})`;
        },
        getLineWobbleStyle(ln) {
            const delayWobbleBy = -0.015 * (this.lines - ln);
            return {
                animationDelay: `calc(var(--dur) * ${delayWobbleBy})`,
            };
        },
    },
};
</script>

<style scoped>
:root {
    --hue: 223;
    --bg: hsl(var(--hue), 90%, 90%);
    --fg: hsl(var(--hue), 90%, 10%);
    --line1: hsl(193, 90%, 35%);
    --line2: hsl(203, 90%, 40%);
    --line3: hsl(213, 90%, 45%);
    --line4: hsl(var(--hue), 90%, 50%);
    --trans-dur: 0.3s;
    --dur: 4s;
}

body {
    background-color: var(--bg);
    color: var(--fg);
    display: flex;
    font: 1em/1.5 sans-serif;
    height: 100vh;
    transition: background-color var(--trans-dur), color var(--trans-dur);
}

.pl {
    display: block;
    margin: auto;
    width: 15em;
    height: auto;
}

.pl__line,
.pl__line-wobble {
    animation: line-move var(--dur) infinite;
    animation-timing-function: cubic-bezier(0.65, 0, 0.35, 1);
}

.pl__line {
    animation-name: line-move;
    stroke: var(--line1);
    transition: stroke var(--trans-dur);
}

.pl__line:nth-child(2) {
    stroke: var(--line2);
}

.pl__line:nth-child(3) {
    stroke: var(--line3);
}

.pl__line:nth-child(4) {
    stroke: var(--line4);
}

@keyframes line-move {

    from,
    35%,
    to {
        stroke-dashoffset: -6.99px;
    }

    50%,
    85% {
        stroke-dashoffset: 4.99px;
    }
}

.pl__line-wobble {
    animation-name: line-wobble;
}

@keyframes line-wobble {

    from,
    to {
        stroke-width: 1px;
        transform: translate(0, 6.5px);
    }

    25% {
        stroke-width: 1.5px;
        transform: translate(0, 6.5px);
    }

    50% {
        stroke-width: 1px;
        transform: translate(0, 6.5px);
    }

    75% {
        stroke-width: 1.5px;
        transform: translate(0, 6.5px);
    }
}

/* Dark theme */
@media (prefers-color-scheme: dark) {
    :root {
        --bg: hsl(var(--hue), 90%, 10%);
        --fg: hsl(var(--hue), 90%, 90%);
    }
}
</style>