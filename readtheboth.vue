<template>
    <div id="app">
      <h2>Upload de Arquivo Excel ou CSV</h2>
  
      <div class="drop-zone" @dragover.prevent @drop.prevent="handleDrop">
        Arraste e solte seu arquivo Excel (.xlsx, .xls) ou CSV aqui ou clique para selecionar
        <input type="file" @change="handleFileChange" accept=".xlsx, .xls, .csv" style="display: none;" ref="fileInput" />
        <button @click="selectFile">Selecionar Arquivo</button>
      </div>
      <button v-if="file" @click="uploadFile">Enviar Arquivo</button>
      <div v-if="message">{{ message }}</div>
  
      <div v-if="csvData.length">
        <h3>Conteúdo do CSV:</h3>
        <table>
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
  
      <div v-if="excelData.length">
        <h3>Conteúdo do Excel:</h3>
        <table>
          <thead>
            <tr>
              <th v-for="(header, index) in excelHeaders" :key="index">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in excelData" :key="rowIndex">
              <td v-for="(cell, cellIndex) in row" :key="cellIndex">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script>
  import Papa from 'papaparse'; // Biblioteca para parsear CSV
  import * as XLSX from 'xlsx'; // Biblioteca para manipular Excel
  
  export default {
    data() {
      return {
        file: null,
        message: '',
        csvData: [],
        headers: [],
        excelData: [],
        excelHeaders: []
      };
    },
    methods: {
      handleDrop(event) {
        this.file = event.dataTransfer.files[0];
        this.processFile(this.file);
      },
      handleFileChange(event) {
        this.file = event.target.files[0];
        this.processFile(this.file);
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
      processFile(file) {
        const fileType = file.type;
  
        if (fileType.includes('csv')) {
          this.readCSV(file);
        } else if (fileType.includes('sheet') || fileType.includes('excel')) {
          this.readExcel(file);
        } else {
          alert('Formato de arquivo não suportado. Selecione um arquivo CSV ou Excel.');
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
              this.excelData = []; // Limpa dados do Excel
              this.excelHeaders = []; // Limpa cabeçalhos do Excel
            },
            header: false
          });
        };
        reader.readAsText(file);
      },
      readExcel(file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const data = new Uint8Array(event.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
  
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
  
          this.excelHeaders = jsonData[0]; // Primeira linha como cabeçalhos
          this.excelData = jsonData.slice(1); // Dados sem cabeçalhos
          this.csvData = []; // Limpa dados do CSV
          this.headers = []; // Limpa cabeçalhos do CSV
        };
        reader.readAsArrayBuffer(file);
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
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
  }
  th, td {
    border: 1px solid #ccc;
    padding: 8px;
    text-align: left;
  }
  </style>