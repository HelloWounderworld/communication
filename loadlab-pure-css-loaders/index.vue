<template>
    <div class="flexbox">
      <div>
        <div class="cm-spinner"></div>
      </div>
    </div>
  </template>
  
  <style>
  body {
    -webkit-box-sizing: border-box;
    box-sizing: border-box;
    background-color: #263238;
    height: 100vh;
    padding: 0;
    margin: 0;
    font-family: Arial;
  }
  
  .flexbox {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -ms-flex-wrap: wrap;
    flex-wrap: wrap;
    height: 100vh;
    justify-content: center;
    align-items: center;
  }
  
  .flexbox > div {
    width: 300px;
    height: 300px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .cm-spinner {
    height: 150px;
    width: 150px;
    border: 3px solid transparent;
    border-radius: 50%;
    border-top: 4px solid #f15e41;
    animation: spin 4s linear infinite;
    position: relative;
  }
  
  .cm-spinner::before,
  .cm-spinner::after {
    content: "";
    position: absolute;
    top: 6px;
    bottom: 6px;
    left: 6px;
    right: 6px;
    border-radius: 50%;
    border: 4px solid transparent;
  }
  
  .cm-spinner::before {
    border-top-color: #bad375;
    animation: spin 3s linear infinite;
  }
  
  .cm-spinner::after {
    border-top-color: #26a9e0;
    animation: spin 1.5s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  </style>