from collections import defaultdict


def auditar_deduplicacao(lista, nome="lista"):

    # ---- Oráculo independente: sem hash, sem dict. Só __eq__ e listas. ----
    # Deliberadamente O(n^2). O papel dele é ser óbvio, não rápido.
    def dedup_referencia(seq):
        vistos, saida = [], []
        for s in seq:
            if not any(s == v for v in vistos):
                vistos.append(s)
                saida.append(s)
        return saida

    # ---- 1) Existe repetição? ----
    ocorrencias = defaultdict(list)              # string -> [todos os índices]
    for i, s in enumerate(lista):
        ocorrencias[s].append(i)

    repetidas = {s: idx for s, idx in ocorrencias.items() if len(idx) > 1}

    print(f"=== {nome} | n = {len(lista)} | distintas = {len(ocorrencias)} ===")

    if repetidas:
        print(f"[REPETIÇÃO] {len(repetidas)} string(s) distinta(s) com múltiplas ocorrências:")
        for s, idx in sorted(repetidas.items(), key=lambda kv: kv[1][0]):
            print(f"   {s!r:>12}  índices={idx}  ->  mantém {idx[0]}  |  descarta {idx[1:]}")
    else:
        print("[REPETIÇÃO] nenhuma. A deduplicação é a identidade.")

    # ---- 2) A operação sob teste ----
    resultado = list(dict.fromkeys(lista))

    # ---- 3) Verificação ----
    posicoes = [lista.index(s) for s in resultado]   # list.index devolve a 1ª ocorrência

    p1 = set(resultado) == set(lista)                                    # nada perdido
    p2 = len(resultado) == len(set(resultado))                           # nada duplicado
    p3 = resultado == dedup_referencia(lista)                            # bate com o oráculo
    p4 = all(posicoes[k] < posicoes[k+1] for k in range(len(posicoes)-1))# ordem preservada
    p5 = posicoes == sorted(min(idx) for idx in ocorrencias.values())    # menor índice venceu
    p6 = list(dict.fromkeys(resultado)) == resultado                     # idempotente

    print("\n[RESULTADO]        ", resultado)
    print("[ÍNDICE DE ORIGEM] ", posicoes)
    print("\n[VERIFICAÇÃO]")
    for descricao, ok in [
        ("P1  nenhum elemento perdido:  set(R) == set(L)",              p1),
        ("P2  nenhuma duplicata remanescente",                          p2),
        ("P3  idêntico ao oráculo O(n^2) que não usa dict",             p3),
        ("P4  ordem preservada: índices de origem estrit. crescentes",  p4),
        ("P5  sobreviveu sempre a PRIMEIRA ocorrência (menor índice)",  p5),
        ("P6  idempotente: dedup(dedup(L)) == dedup(L)",                p6),
    ]:
        print(f"   {'OK   ' if ok else 'FALHA'} {descricao}")

    ok_geral = p1 and p2 and p3 and p4 and p5 and p6
    print(f"\n[VEREDITO] {'CONFIRMADO' if ok_geral else 'REFUTADO'}\n")
    return resultado, ok_geral


lista = ["ótima", "boa", "ótima", "regular", "regular", "ótima", "ruim", "boa"]
auditar_deduplicacao(lista, "lista de exemplo")
