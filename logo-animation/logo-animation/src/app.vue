<template>
    <div>
        <a href="https://dribbble.com/shots/3541884-Logo-Animation" target="_blank">
            https://dribbble.com/shots/3541884-Logo-Animation
        </a>
        <div class="wrapper">
            <div class="outer"></div>
            <div class="inner"></div>
            <div class="content"></div>
            <h4>GISION</h4>
        </div>
    </div>
</template>

<script>
import { onMounted } from 'vue';
import { gsap } from 'gsap';

export default {
    name: 'LogoAnimation',
    setup() {
        onMounted(() => {
            // Animações usando GSAP
            gsap.to('.outer', { rotation: 360, duration: 5, ease: 'linear', repeat: -1 });
            gsap.to('.inner', { rotation: -360, duration: 5, delay: 1, ease: 'linear', repeat: -1 });
            gsap.to('.content', { rotation: 360, duration: 5, delay: 2, ease: 'linear', repeat: -1 });
        });
    },
};
</script>

<style lang="scss" scoped>
// @import url('https://fonts.googleapis.com/css?family=Roboto');

@mixin gradient-horizontal($start-color: #555, $end-color: #333, $start-percent: 0%, $end-percent: 100%) {
    background-image: -webkit-linear-gradient(left, $start-color $start-percent, $end-color $end-percent);
    background-image: -o-linear-gradient(left, $start-color $start-percent, $end-color $end-percent);
    background-image: linear-gradient(to right, $start-color $start-percent, $end-color $end-percent);
    background-repeat: repeat-x;
    filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#{ie-hex-str($start-color)}', endColorstr='#{ie-hex-str($end-color)}', GradientType=1);
}

.center {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
}

.wrapper {
    @extend .center;
}

.outer {
    height: 200px;
    width: 200px;
    border-radius: 45%;
    @include gradient-horizontal(#795DEF, #EB3CF9, 25%, 100%);
    @extend .center;
}

.inner {
    height: 175px;
    width: 175px;
    border-radius: 45%;
    @include gradient-horizontal(#795DEF, #EB3CF9, 25%, 100%);
    @extend .center;
}

.content {
    @extend .center;
    height: 150px;
    width: 150px;
    background-color: #260E36;
    border-radius: 45%;
}

h4 {
    @extend .center;
    text-align: center;
    vertical-align: middle;
    color: white;
    font-size: 24px;
    padding-bottom: 65px;
    font-family: 'Roboto', sans-serif;
    font-weight: 300;
}
</style>