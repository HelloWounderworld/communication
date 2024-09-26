<template>
    <div id="app">
      <div class="drop-zone" @dragover.prevent @drop.prevent="handleDrop">
        Arraste e solte seu arquivo CSV aqui ou clique para selecionar
        <input type="file" @change="handleFileChange" accept=".csv" style="display: none;" ref="fileInput" />
        <button @click="selectFile">Selecionar Arquivo</button>
      </div>
      <button v-if="file" @click="uploadFile">Enviar Arquivo</button>
      <div v-if="message">{{ message }}</div>
      
      <table v-if="csvData.length">
        <thead>
          <tr>
            <th v-for="(header, index) in headers" :key="index">{{ header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in csvData" :key="rowIndex">
            <td v-for="(cell, cellIndex) in row" :key="cellIndex">{{ cell }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import Papa from 'papaparse'; // Biblioteca para parsear CSV
  
  export default {
    data() {
      return {
        file: null,
        message: '',
        csvData: [],
        headers: []
      };
    },
    methods: {
      handleDrop(event) {
        this.file = event.dataTransfer.files[0];
        this.readCSV(this.file);
      },
      handleFileChange(event) {
        this.file = event.target.files[0];
        this.readCSV(this.file);
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
      },
      readCSV(file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const text = event.target.result;
          Papa.parse(text, {
            complete: (results) => {
              this.headers = results.data[0]; // Primeira linha como cabeçalhos
              this.csvData = results.data.slice(1); // Dados sem cabeçalhos
            },
            header: false
          });
        };
        reader.readAsText(file);
      }
    }
  };
  </script>