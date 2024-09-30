<template>
    <div v-if="carregando" class="loading-overlay">
        <div class="loading-spinner">Carregando...</div>
    </div>
</template>

<script>
export default {
    props: {
        carregando: {
            type: Boolean,
            required: true,
        },
    },
};
</script>

<style>
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    /* Fundo semi-transparente */
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-size: 24px;
}

.loading-spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}
</style>