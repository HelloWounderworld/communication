<template>
    <div v-if="loading" class="smart-glass">
        <h1>Smart Glass</h1>
        <div class="logo">
            <div class="circle">
                <div class="circle">
                    <div class="circle"></div>
                </div>
            </div>
            <div class="hold-x">
                <div class="xbox"></div>
            </div>
        </div>
        <div class="loading-text">
            Loading...
        </div>
    </div>
</template>

<script>
export default {
    props: {
        loading: {
            type: Boolean,
            required: true,
        }
    }
}
</script>

<style scoped>
@import url(https://fonts.googleapis.com/css?family=Play:400,700);

$xbox-green: #bf57ff;
$dark: #222;
$light: #FFF;

* {
    box-sizing: border-box;
}

body {
    background-color: $dark;
    font-family: 'Play', sans-serif;
}

h1 {
    font-size: 2rem;
    color: $light;
    text-align: center;
    text-transform: uppercase;
}

.smart-glass {
    position: absolute;
    margin: auto;
    left: 0;
    top: 0;
    right: 0;
    bottom: 0;
    width: 288px;
    height: 388px;
}

.logo {
    width: 288px;
    height: 288px;
    position: relative;
}

.circle {
    padding: 20px;
    border: 6px solid transparent;
    border-top-color: $xbox-green;
    border-radius: 50%;
    width: 100%;
    height: 100%;
    animation: connect 2.5s linear infinite;
}

.xbox {
    background: $light;
    width: 80px;
    height: 80px;
    border-radius: 100%;
    overflow: hidden;
    position: absolute;
    top: 0;
    right: 0;
    left: 0;
    bottom: 0;
    margin: auto;
}

.xbox:after,
.xbox:before {
    content: '';
    display: block;
    border-top: 10px solid $dark;
    border-radius: 50%;
    height: 90%;
    width: 120%;
    transform: rotate(-45deg);
    position: absolute;
    right: -30%;
    top: 15%;
}

.xbox:before {
    left: -30%;
    transform: rotate(45deg);
}

.loading-text {
    text-transform: uppercase;
    color: $light;
    text-align: center;
    margin: 10px 0;
    font-size: 1.4rem;
}

@keyframes connect {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(-360deg);
    }
}
</style>