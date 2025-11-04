from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Any
import pandas as pd
import random
import json
import os

app = FastAPI(title="Excel Processor API", version="6.0")

# ==========================
# ⚙️ Config
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = Path(__file__).parent
XLSX = BASE / "dados.xlsx"
USERS = BASE / "users"
USERS.mkdir(exist_ok=True)

# ==========================
# 🔧 Utils
# ==========================
def shuffle(lst: list) -> list:
    arr = lst[:]
    random.shuffle(arr)
    return arr

def save_json(data: Any, path: Path):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def read_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def read_excel() -> list[dict]:
    if not XLSX.exists():
        raise FileNotFoundError(f"Excel não encontrado em: {XLSX}")
    df = pd.read_excel(XLSX, sheet_name="Sheet1")
    cols = df.columns.tolist()
    data = []
    for i, row in df.iloc[1:].iterrows():
        txt = row[cols[0]]
        t1, t2, t3 = row[cols[1]], row[cols[2]], row[cols[3]]
        data.append({
            "txt": txt,
            "p1": {"t": t1, "l": int(i + 2), "c": cols[1]},
            "p2": {"t": t2, "l": int(i + 2), "c": cols[2]},
            "p3": {"t": t3, "l": int(i + 2), "c": cols[3]},
            "idx": len(data)
        })
    return data

def make_pairs(data: list[dict]) -> dict[str, list[dict]]:
    rows = shuffle(data)
    l1, l2, l3 = [], [], []
    for row in rows:
        txt = row["txt"]
        ps = [
            {"txt": txt, "p": row["p1"], "idx": row["idx"]},
            {"txt": txt, "p": row["p2"], "idx": row["idx"]},
            {"txt": txt, "p": row["p3"], "idx": row["idx"]},
        ]
        ps = shuffle(ps)
        l1.append(ps[0]); l2.append(ps[1]); l3.append(ps[2])
    all_pairs = l1 + l2 + l3
    return {"l1": l1, "l2": l2, "l3": l3, "all": all_pairs}

def last_scored(path: Path) -> int:
    js = read_json(path).get("all", [])
    last = -1
    for i, p in enumerate(js):
        if "s" in p:
            last = i
    return last + 1 if last + 1 < len(js) else len(js)

def check_pass(udir: Path, p: str):
    spath = udir / "senha.txt"
    if not spath.exists():
        raise HTTPException(status_code=401, detail="Senha não configurada.")
    saved = spath.read_text(encoding="utf-8").strip()
    if saved != p:
        raise HTTPException(status_code=403, detail="Senha incorreta.")

# ==========================
# 🚀 Endpoints
# ==========================
@app.post("/api/user")
def create_or_check_user(b: dict):
    """
    Cria novo usuário com senha, ou retorna progresso se já existir.
    body = { "u": "nome", "pw": "senha" }
    """
    try:
        u = b.get("u")
        pw = b.get("pw")
        if not u or not pw:
            raise ValueError("Campos 'u' (usuário) e 'pw' (senha) são obrigatórios.")

        udir = USERS / u
        udir.mkdir(exist_ok=True)
        orig = udir / "orig.json"
        pairs = udir / "pairs.json"
        spath = udir / "senha.txt"

        # Se já existir, verifica senha e retorna progresso
        if orig.exists() and pairs.exists() and spath.exists():
            check_pass(udir, pw)
            pos = last_scored(pairs)
            return {"ok": True, "msg": f"Usuário '{u}' já existe.", "next": pos}

        # Cria novo usuário
        spath.write_text(pw, encoding="utf-8")
        data = read_excel()
        save_json(data, orig)
        ps = make_pairs(data)
        save_json(ps, pairs)
        return {"ok": True, "msg": f"Usuário '{u}' criado.", "next": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pairs")
def get_pairs(b: dict):
    """
    Retorna pares do usuário autenticado.
    body = { "u": "nome", "pw": "senha" }
    """
    try:
        u = b.get("u")
        pw = b.get("pw")
        if not u or not pw:
            raise ValueError("Campos 'u' e 'pw' são obrigatórios.")
        udir = USERS / u
        pairs = udir / "pairs.json"
        check_pass(udir, pw)
        if not pairs.exists():
            raise FileNotFoundError(f"Pares do usuário '{u}' não encontrados.")
        js = read_json(pairs)
        pos = last_scored(pairs)
        return {"ok": True, "u": u, "pairs": js, "next": pos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/score")
def update_score(b: dict):
    """
    Atualiza score para o usuário autenticado.
    body = {
        "u": "nome",
        "pw": "senha",
        "idx": 2,
        "p_idx": 120,
        "s": 4,
        "c": "Comentário explicando a escolha"
    }
    """
    try:
        u = b.get("u")
        pw = b.get("pw")
        i_orig = b.get("idx")
        i_pair = b.get("p_idx")
        s = b.get("s")
        c = b.get("c")  # ← novo campo: comentário

        if not u or not pw:
            raise ValueError("Campos 'u' e 'pw' são obrigatórios.")
        if not isinstance(s, (int, float)) or not (1 <= s <= 4):
            raise ValueError("Score deve ser entre 1–4.")
        if not c or not c.strip():
            raise ValueError("Comentário ('c') é obrigatório.")

        udir = USERS / u
        check_pass(udir, pw)

        orig = udir / "orig.json"
        pairs = udir / "pairs.json"
        data = read_json(orig)
        ps = read_json(pairs)
        all_ps = ps.get("all", [])

        # Atualiza o original
        if 0 <= i_orig < len(data):
            data[i_orig]["s"] = s
            data[i_orig]["c"] = c

        # Atualiza o par correspondente
        if 0 <= i_pair < len(all_ps):
            all_ps[i_pair]["s"] = s
            all_ps[i_pair]["c"] = c

        save_json(data, orig)
        save_json(ps, pairs)

        return {
            "ok": True,
            "msg": f"Score salvo ({i_orig}, {i_pair})",
            "comment": c,
            "next": i_pair + 1 if i_pair + 1 < len(all_ps) else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
