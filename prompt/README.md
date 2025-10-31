# O que eu quero fazer

Eu gostaria que voce pegue o arquivo .py e adapte para a seguinte exigencia minha:

- Eu quero somente duas requisicoes, ambas post, que retorna objetos:
  - O primeiro seria funcoes em que pega o arquivo dados.xlsx, e, pulando a primeira linha, a partir da segunda linha tera o seguinte 4 elementos (texto, titulo1, titulo2, titulo3). Assim, sera criado um arquivo, dados-original.json, que sera uma lista gigantesca em que cada indice sera guardado os seguintes valores: { texto: texto, par1: {titulo1: titulo1, linha_em_que_titulo1_se_encontra: linha_em_que_titulo1_se_encontra, coluna_em_que_esse_titulo1_se_encontra: coluna_em_que_esse_titulo1_se_encontra}, par2: {titulo2: titulo2, linha_em_que_titulo2_se_encontra: linha_em_que_titulo2_se_encontra, coluna_em_que_esse_titulo2_se_encontra: coluna_em_que_esse_titulo2_se_encontra}, par3: {titulo3: titulo3, linha_em_que_titulo3_se_encontra: linha_em_que_titulo3_se_encontra, coluna_em_que_esse_titulo3_se_encontra: coluna_em_que_esse_titulo3_se_encontra }, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original }. Alem disso, crie uma funcao em que primeiro embaralhe e crie um par do seguinte elemento, (texto, titulo1, titulo2, titulo3), da seguinte forma, por exemplo, ((texto, titulo1), (texto, titulo3), (texto, titulo2)) e a partir desse embaralhamento vai acrescentando, para cada elemento desses tres, apos embaralhado o seguinte
    [
        {texto: texto, par: {titulo1: titulo1, linha_em_que_titulo1_se_encontra: linha_em_que_titulo1_se_encontra, coluna_em_que_esse_titulo1_se_encontra: coluna_em_que_esse_titulo1_se_encontra}, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original},
        {texto: texto, par: {titulo3: titulo3, linha_em_que_titulo3_se_encontra: linha_em_que_titulo3_se_encontra, coluna_em_que_esse_titulo3_se_encontra: coluna_em_que_esse_titulo3_se_encontra }, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original}, 
        {texto:texto, par: {titulo2: titulo2, linha_em_que_titulo2_se_encontra: linha_em_que_titulo2_se_encontra, coluna_em_que_esse_titulo2_se_encontra: coluna_em_que_esse_titulo2_se_encontra}, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original}
    ],
        
    no caso, cada um desses elemento, sera guaradado como uma linha no arquivo, pares-embaralhados.json. Depois que fizer isso para cada linha do excel, no final, voce pega a lista inteira criado no pares-embaralhados.json e realize um embaralhamento geral.
  - O segundo post ela serve para devolver os dados que seriam salvo no pares-embaralhados.json.
  - O terceiro post seria o seguinte. Ele ira receber um objeto do tipo

        {
            "texto": texto,
            "par": {titulo: titulo, linha_em_que_titulo_se_encontra: linha_em_que_titulo_se_encontra, coluna_em_que_esse_titulo_se_encontra: coluna_em_que_esse_titulo_se_encontra},
            score: pontuacao dada entre 1 - 4,
            posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original
        }
    Ele leva em consideracao a infomacao da posicao_atual_index, e pega o arquivo, dados_original.json, e identifica o essa posicao em o texto e o titulo se encontra e, nela, acrescenta o valor da pontuacao como objeto

        {texto: texto, par: {titulo1: titulo1, linha_em_que_titulo1_se_encontra: linha_em_que_titulo1_se_encontra, coluna_em_que_esse_titulo1_se_encontra: coluna_em_que_esse_titulo1_se_encontra}, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original, score: entre 1 - 4}

