<template>
    <div class="text-center py-5 bg-light">
        <!-- Header Section -->
        <div class="d-flex justify-content-between align-items-center px-4">
            <img src="path-to-nhk-logo.png" alt="NHK Logo" class="img-fluid" style="height: 40px;" />
        </div>

        <!-- Main Content -->
        <div class="mt-4">
            <!-- Election Logo -->
            <img src="path-to-election-logo.png" alt="Election 2024" class="img-fluid mb-3" style="height: 80px;" />
            <h2 class="h5">衆議院選挙2024 ボートマッチ</h2>
            <img src="path-to-vote-icon.png" alt="Vote Icon" class="img-fluid my-4"
                style="width: 150px; height: auto;" />
            <p>あなたと候補者の考え方の一致度がわかります。</p>
        </div>

        <!-- Start Button -->
        <button class="btn btn-danger btn-lg rounded-pill mt-4">
            スタートする
        </button>

        <!-- Footer Button -->
        <div class="mt-4">
            <button class="btn btn-outline-secondary rounded-pill px-4">
                仕組み
            </button>
        </div>
    </div>
</template>

<script>
export default {
    name: "VoteMatchApp",
};
</script>

<style scoped>
/* Add custom styles here if needed */
</style>

<!-- 
Steps to Customize:
Replace the placeholders (path-to-nhk-logo.png, path-to-election-logo.png, path-to-vote-icon.png) with the actual paths for the images.
Add Bootstrap to your project by including its CSS and JS files in the index.html or installing it via npm/yarn.
This code is structured to match the design while staying responsive using Bootstrap.
 -->