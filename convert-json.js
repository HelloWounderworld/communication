const headers = data[0]; // Cabeçalhos
const rows = data.slice(1); // Dados sem cabeçalhos

const result = rows.map(row => {
  return headers.reduce((acc, header, index) => {
    acc[header] = row[index];
    return acc;
  }, {});
});

// `result` agora terá a forma de:
[
  { Nome: "João", Idade: 30, Cidade: "São Paulo" },
  { Nome: "Maria", Idade: 25, Cidade: "Rio de Janeiro" }
]