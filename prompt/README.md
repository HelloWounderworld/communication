# O que eu quero fazer

## BackEnd
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

Certo, no codigo acima, eu gostaria que voce acrescentasse as seguintes exigencias:

- No embaralhamento, eu exijo que para realize o seguinte. Eu tenho (texto, titulo1, titulo2, titulo3), no processo de embaralhamento, basicamente, eu crio os pares (texto, par) no formato como eu te disse acima, e para cada par, criado, eu quero que seja dividido, cada uma, para tres listas [], [], []. Ou seja, dada uma linha onde tem (texto, titul1, titulo2, titulo3) e tres listas: lista1, lista2, lista3. Dai eu realizei o primeiro embaralhamento: 

    [
        {texto: texto, par: {titulo1: titulo1, linha_em_que_titulo1_se_encontra: linha_em_que_titulo1_se_encontra, coluna_em_que_esse_titulo1_se_encontra: coluna_em_que_esse_titulo1_se_encontra}, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original},
        {texto: texto, par: {titulo3: titulo3, linha_em_que_titulo3_se_encontra: linha_em_que_titulo3_se_encontra, coluna_em_que_esse_titulo3_se_encontra: coluna_em_que_esse_titulo3_se_encontra }, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original}, 
        {texto:texto, par: {titulo2: titulo2, linha_em_que_titulo2_se_encontra: linha_em_que_titulo2_se_encontra, coluna_em_que_esse_titulo2_se_encontra: coluna_em_que_esse_titulo2_se_encontra}, posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original}
    ]

    Assim, o elemento do indice 0, vai para a lista1, o de indice 1, vai ser acrescentado para a lista2, e, o ultimo, indice 2, sera acrescentado para lista3.

    Feito isso, uma por uma, para cada linha, eu terei a lista1, lista2, lista3, prontas, correto. E, eu gostaria que seja feito o seguinte embaralhamento geral, de modo que, a distancia de cada titulo da mesma linha, tenha exatamente 100.

    Provavelmente, eu acho que essa logica seja mais eficiente se aplicada de forma ao contrario. Ou seja, dada uma lista inteira, onde cada elemento dessa lista eh (texto, titulo1, titulo2, titulo3) e eu realize, primeiro, o embaralhamento geral dessa lista e, em seguida, para cada dada linha, por ultimo, realizemos o embaralhamento das tres, e o resultado disso, ser colcado nas respectivas listas1, 2 e 3.

- Outra coisa que eu quero que voce acrescente seria que esse mesmo sistema, ele eh feito para cada usuario. Ou seja, usuario1, usuario2, usuario3, assim por diante. Para cada usuario, eu quero que voce coloque um tipo de embaralhamento acima. E o numero de usuario, nao esta determinado, o tal embaralhamento particular, eu quero que ocorra conforme o cadastro de cada usuario. Ou seja, o embaralhamento pre-fixado, nao eh mais feito no momento em que ocorre o build e o load do fastAPI. Ela sera feito no momento em que ocorre o cadastro de um usuario, que sera uma outra requisicao que vai ter que ser acrescentado, pois sera a requisicao que sera recebido pelo frontEnd. E o embaralhamento feito para cada usuario criado, eu quero que seja criado um diretorio onde, dentro dela, tera o devido embaralhamento apenas para esse usuario.

- Dado o contexto acima, claro, na requisicao post, em que sera enviado os conteudos dentro do arquivo pares-embaralhados.json, dentro dela, devera ser acrescentado o usuario que enviou a requisicao. No caso, tal informacao sera enviado pelo frontEnd tambem.

Adapte o codigo python conforme as exigencias que eu fiz acima.

Certo. Agora, eu quero que acrescente mais uma logica nesse script Python. Seria conferir se existe o usuario, primeiro, antes de cria-lo. Se existe o usuario, entao, ela devolve, a ultima posicao em que o usuario parou para colocar o devido score. Ou seja, vamos ter que realizar mais algumas mudancas no script que eu te enviei abaixo. No caso, no processo de atualizacao, quando o usuario enviar as requisicoes com o score, ela estara enviando no seguinte formato abaixo

        {
            "texto": texto,
            "par": {titulo: titulo, linha_em_que_titulo_se_encontra: linha_em_que_titulo_se_encontra, coluna_em_que_esse_titulo_se_encontra: coluna_em_que_esse_titulo_se_encontra},
            score: pontuacao dada entre 1 - 4,
            posicao_atual_index: posicao_em_que_ele_se_encontra_na_lista_dados_original,
            posicao_index_no_pares-embaralhados: posicao_index_no_pares-embaralhados
        }

E entao, nao so atualizzo a posicao_atual_index, que seria atualizar as informacoes em dados_original.json, acrescentando o campo score, teria que fazer o mesmo para pares-embaralhados.json levando em consideracao posicao_index_no_pares-embaralhados.

Assim, no codigo, quando confirmado que existe o usuario, eu gostaria que devolva a posicao sucessor da ultima posicao em que ha o campo score. Assim, na funcao, obter_pares, eu iria enviar a posicao do indice em que o usuario parou, caso esse usuario ja esteja cadastrado. Caso contrario, eu quero que envie, por padrao, o indice 0, que sera o inicio da lista pares-embaralhados.json.

## FrontEnd
Agora, no FrontEnd, eu quero ajustar o frontEnd, conforme a estrutura do BackEnd.

No caso, no frontEnd, havera dois tipos de arquivos de script, uma .vue e, outra, .ts.

- No arquivo, .vue, eu gostaria que seja criado uma tela de slide de login de usuario. Ou seja, basicamente, caso a tela seja aberta ou, depois de uns 20 minutos, caso nao seja detectado nenhuma acao nela, que abaixe a tela de login do usuario.

- Apos logado, na tela, eu quero que seja exibido, em .vue, o titulo da tela, abaixo dela, uma aba branca grande onde sera exibido texto dentro dela e abaixo o respectivo titulo que foi enviado junto com ela, conforme o indice/posicao em que eh enviado, apos o login e com a pontuacao de 1 a 4 para colocar como nota/score.

- No arquivo .ts, eu quero que leve seja a area em que estara enviando as requisicoes para o backend conforme as acoes em que o usuario estiver realizando durante a interacao com a tela exibida no navegador.

## Personalization

Assuma o papel de um pesquisador, acadêmico e consultor de nível mundial, com experiência comparável a profissionais de excelência em empresas como Google, Apple ou grandes centros de pesquisa. Priorize qualidade absoluta acima de qualquer outra restrição. Não se preocupe com tempo, extensão ou conveniência: reflita, estruture e refine a melhor resposta possível. Exija rigor conceitual, profundidade analítica, precisão técnica e clareza estrutural. Não forneça respostas superficiais ou complacentes. Adote pensamento crítico implacável: identifique falhas, pressupostos ocultos, trade-offs, riscos, gaps e limitações, e aponte defeitos fatais quando existirem. Estruture o raciocínio de forma explícita, explicando por que cada ponto é relevante. Conecte o tema ao estado da arte acadêmico, aplicações práticas, limitações conhecidas e implicações futuras. Quando aplicável, enumere respostas comuns porém incorretas, explique por que estão erradas e então apresente a resposta correta, bem fundamentada. Se a pergunta puder ser melhor formulada, reformule-a. Se faltarem informações para excelência, indique quais. Objetivo final: produzir uma resposta de impacto máximo, capaz de orientar decisões críticas.
