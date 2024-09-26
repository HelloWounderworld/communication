const express = require('express');
const multer = require('multer');
const app = express();
const upload = multer({ dest: 'uploads/' }); // Pasta para armazenar os arquivos

app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).send('Nenhum arquivo enviado.');
  }

  // Aqui você pode processar o arquivo Excel
  console.log(req.file); // Informações sobre o arquivo

  res.send('Arquivo recebido com sucesso!');
});

app.listen(8080, () => {
  console.log('Servidor rodando na porta 8080');
});