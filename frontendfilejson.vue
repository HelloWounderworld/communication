<template>
    <div id="app">
        <h2>Upload de Arquivo Excel ou CSV</h2>

        <div class="drop-zone" @dragover.prevent @drop.prevent="handleDrop">
            Arraste e solte seu arquivo Excel (.xlsx, .xls) ou CSV aqui ou clique para selecionar
            <input type="file" @change="handleFileChange" accept=".xlsx, .xls, .csv" style="display: none;"
                ref="fileInput" />
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

        <button v-if="downloadUrl" @click="downloadFile">Baixar Arquivo</button>
        <button v-if="jsonData" @click="exportToExcel">Exportar JSON para Excel</button>
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
            excelHeaders: [],
            jsonData: null, // Armazena os dados convertidos para JSON
            downloadUrl: null // URL para download do arquivo
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
        async processFile(file) {
            const fileExtension = file.name.split('.').pop().toLowerCase();
            const reader = new FileReader();

            reader.onload = (e) => {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });

                if (fileExtension === 'csv') {
                    const csvData = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]], { header: 1 });
                    this.csvData = csvData;
                    this.headers = csvData[0];
                    this.jsonData = csvData.slice(1).map(row => {
                        return this.headers.reduce((acc, header, index) => {
                            acc[header] = row[index];
                            return acc;
                        }, {});
                    });
                } else {
                    const excelData = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]]);
                    this.excelData = excelData;
                    this.excelHeaders = Object.keys(excelData[0]);
                    this.jsonData = excelData; // Armazena o JSON do Excel
                }
            };

            reader.readAsArrayBuffer(file);
        },
        async uploadFile() {
            if (!this.jsonData) {
                alert('Por favor, carregue um arquivo válido primeiro.');
                return;
            }

            try {
                const response = await fetch('http://localhost:8080/upload', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.jsonData) // Envia o JSON convertido
                });

                if (!response.ok) {
                    throw new Error('Erro na requisição: ' + response.status);
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                this.downloadUrl = url; // Armazena a URL do blob para download

                this.message = 'Arquivo enviado com sucesso!';
            } catch (error) {
                this.message = 'Erro ao enviar o arquivo: ' + error.message;
            }
        },
        downloadFile() {
            if (this.downloadUrl) {
                const link = document.createElement('a');
                link.href = this.downloadUrl;
                link.setAttribute('download', 'arquivo.xlsx'); // Nome do arquivo a ser baixado
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(this.downloadUrl); // Libera a URL do blob
            }
        },
        exportToExcel() {
            const worksheet = XLSX.utils.json_to_sheet(this.jsonData);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Dados');

            // Gera um arquivo Excel e inicia o download
            XLSX.writeFile(workbook, 'dados.xlsx');
        }
    }
};
</script>

<style>
.drop-zone {
    border: 2px dashed #ccc;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
}
</style>