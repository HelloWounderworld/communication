const express = require('express');
const multer = require('multer');
const fs = require('fs');
const app = express();
const upload = multer({ dest: 'uploads/' }); // Pasta para armazenar os arquivos

app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).send('Nenhum arquivo enviado.');
  }

  // Aqui você pode processar o arquivo CSV
  console.log(req.file); // Informações sobre o arquivo

  // Exemplo de leitura do arquivo CSV
  fs.readFile(req.file.path, 'utf8', (err, data) => {
    if (err) {
      return res.status(500).send('Erro ao ler o arquivo.');
    }
    // Aqui você pode processar o conteúdo do CSV
    console.log(data); // Exibir o conteúdo do CSV
    res.send('Arquivo recebido e lido com sucesso!');
  });
});

app.listen(8080, () => {
  console.log('Servidor rodando na porta 8080');
});