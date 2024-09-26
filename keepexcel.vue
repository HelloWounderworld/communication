<template>
    <div id="app">
      <div class="drop-zone" @dragover.prevent @drop.prevent="handleDrop">
        Arraste e solte seu arquivo Excel aqui ou clique para selecionar
        <input type="file" @change="handleFileChange" accept=".xlsx, .xls" style="display: none;" ref="fileInput" />
        <button @click="selectFile">Selecionar Arquivo</button>
      </div>
      <button v-if="file" @click="uploadFile">Enviar Arquivo</button>
      <div v-if="message">{{ message }}</div>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        file: null,
        message: ''
      };
    },
    methods: {
      handleDrop(event) {
        this.file = event.dataTransfer.files[0];
      },
      handleFileChange(event) {
        this.file = event.target.files[0];
      },
      selectFile() {
        this.$refs.fileInput.click();
      },
      async uploadFile() {
        if (!this.file) {
          alert('Por favor, selecione um arquivo.');
          return;
        }
  
        const formData = new FormData();
        formData.append('file', this.file);
  
        try {
          const response = await fetch('http://localhost:8080/upload', {
            method: 'POST',
            body: formData
          });
  
          if (!response.ok) {
            throw new Error('Erro na requisição: ' + response.status);
          }
  
          this.message = 'Arquivo enviado com sucesso!';
        } catch (error) {
          this.message = 'Erro ao enviar o arquivo: ' + error.message;
        }
      }
    }
  };
  </script>
  
  <style>
  .drop-zone {
    border: 2px dashed #ccc;
    padding: 20px;
    text-align: center;
    margin: 20px;
  }
  .drop-zone:hover {
    background-color: #f0f0f0;
  }
  </style>