<template>
    <div id="app">
      <div
        class="drop-zone"
        @dragover.prevent
        @drop.prevent="handleDrop"
      >
        Arraste e solte seu arquivo Excel aqui
      </div>
      <div v-if="data.length">
        <h3>Dados do Arquivo:</h3>
        <table>
          <thead>
            <tr>
              <th v-for="(header, index) in headers" :key="index">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in data" :key="rowIndex">
              <td v-for="(cell, cellIndex) in row" :key="cellIndex">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script>
  import * as XLSX from 'xlsx';
  
  export default {
    data() {
      return {
        data: [],
        headers: []
      };
    },
    methods: {
      handleDrop(event) {
        const file = event.dataTransfer.files[0];
        if (file && file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
          this.readExcel(file);
        } else {
          alert('Por favor, envie um arquivo Excel válido.');
        }
      },
      readExcel(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          this.data = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
          this.headers = this.data[0]; // Primeira linha como cabeçalhos
          this.data = this.data.slice(1); // Remove a primeira linha dos dados
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
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
  }
  </style>