<template>
    <div class="scene">
        <ul :class="systemClass">
            <li :class="orbitClass('top-most-orbit')">
                <div v-html="orbitTemplate(solarSystemData())"></div>
            </li>
        </ul>
    </div>
</template>

<script>
export default {
    data() {
        return {
            maxPlanets: 10,
        };
    },
    computed: {
        systemClass() {
            return `system`;
        },
        orbitClass() {
            return (extraClass) => `orbit ${extraClass || ''}`;
        },
    },
    methods: {
        orbitTemplate(object, depth = 1) {
            const heading = `h${depth}`;
            const list = depth % 2 ? 'ul' : 'ol';
            const style = `color: ${object[0].color || '#BDC5C7'}`;
            return `
          <${heading} style="${style}" class="sphere">${object[0].name}</${heading}>
          ${object[1] ? `
            <${list} class="${this.systemClass}">
              ${object[1].reduce((a, child) => a + `
                <li class="${this.orbitClass()}">${this.orbitTemplate(child, depth + 1)}</li>
              `, '')}
            </${list}>
          ` : ''}
        `;
        },
        solarSystemData() {
            return [
                { name: 'Sun', color: '#FDE528' }, [
                    [{ name: 'Mercury', color: '#C1B4AC' }],
                    [{ name: 'Venus', color: '#F2D299' }],
                    [{ name: 'Earth', color: '#05f' }, [
                        [{ name: 'Moon', color: '' }]
                    ]],
                    [{ name: 'Mars', color: '#E67E5A' }, [
                        [{ name: 'Phobos', color: '' }],
                        [{ name: 'Deimos', color: '' }]
                    ]],
                    [{ name: 'Jupiter', color: '#C5AA96' }, [
                        [{ name: 'Io', color: '' }],
                        [{ name: 'Europa', color: '' }],
                        [{ name: 'Ganymede', color: '' }],
                        [{ name: 'Callisto', color: '' }]
                    ]],
                    [{ name: 'Saturn', color: '#AF9D8E' }, [
                        [{ name: 'Mimas', color: '' }],
                        [{ name: 'Enceladus', color: '' }],
                        [{ name: 'Tethys', color: '' }],
                        [{ name: 'Dione', color: '' }],
                        [{ name: 'Rhea', color: '' }],
                        [{ name: 'Titan', color: '' }],
                        [{ name: 'Iapetus', color: '' }]
                    ]],
                    [{ name: 'Uranus', color: '#C2E8EA' }, [
                        [{ name: 'Miranda', color: '' }],
                        [{ name: 'Ariel', color: '' }],
                        [{ name: 'Umbriel', color: '' }],
                        [{ name: 'Titania', color: '' }],
                        [{ name: 'Oberon', color: '' }]
                    ]],
                    [{ name: 'Neptune', color: '#5C92F0' }, [
                        [{ name: 'Triton', color: '' }]
                    ]]
                ]
            ];
        },
    },
};
</script>

<style scoped>
html,
body {
    height: 100%;
    overflow: hidden;
}

body {
    font-size: 5.5vmin;
}

.scene {
    height: 100%;
    background: #10151a;
    perspective: 350px;
}

.system {
    position: absolute;
    width: 100%;
    height: 100%;
    font-size: .25em;
    border-radius: 100%;
}

.orbit {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border: 1px solid rgba(127, 255, 255, .1);
    box-shadow: 0 0 75em rgba(cyan, .05);
    border-radius: 100%;
    transform-style: preserve-3d;
}

.sphere {
    position: absolute;
    top: 50%;
    left: 0;
    width: 3em;
    height: 3em;
    transform: translate(-50%, -50%);
    background: currentColor;
    border-radius: 100%;
    text-indent: -99999px;
}

/* Efeito de animação */
.top-most-orbit {
    width: 0 !important;
    height: 0 !important;
    animation: none !important;
}

@keyframes orbit {
    from {
        transform: translate(-50%, -50%) rotate(0deg) rotateX(0deg);
    }

    to {
        transform: translate(-50%, -50%) rotate(1440deg) rotateX(360deg);
    }
}

@keyframes counter-rotation {
    from {
        transform: translate(-50%, -50%) rotateX(0deg);
    }

    to {
        transform: translate(-50%, -50%) rotateX(-360deg);
    }
}
</style>