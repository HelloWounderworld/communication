import sqlite3
import os

def inspecionar_banco(caminho_db):
    """
    Diagnóstico completo de um banco SQLite.
    """
    if not os.path.exists(caminho_db):
        print(f"❌ Arquivo não encontrado: {caminho_db}")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 INSPEÇÃO DO BANCO: {caminho_db}")
    print(f"{'='*60}")
    print(f"📁 Tamanho do arquivo: {os.path.getsize(caminho_db) / 1024:.2f} KB")
    
    try:
        conn = sqlite3.connect(caminho_db)
        cursor = conn.cursor()
        
        # 1. Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        
        print(f"\n📊 TABELAS ENCONTRADAS: {len(tabelas)}")
        
        for (tabela,) in tabelas:
            print(f"\n{'-'*40}")
            print(f"📋 Tabela: {tabela}")
            
            # Contagem de registros
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            total = cursor.fetchone()[0]
            print(f"   Registros: {total}")
            
            # Estrutura (schema)
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = cursor.fetchall()
            print(f"   Colunas:")
            for col in colunas:
                # col = (id, name, type, notnull, default_value, pk)
                pk = " [PK]" if col[5] else ""
                nn = " NOT NULL" if col[3] else ""
                print(f"      - {col[1]}: {col[2]}{pk}{nn}")
            
            # Amostra de dados (primeiros 3 registros)
            if total > 0:
                cursor.execute(f"SELECT * FROM {tabela} LIMIT 3")
                amostra = cursor.fetchall()
                print(f"   Amostra (3 primeiros):")
                for i, row in enumerate(amostra):
                    # Trunca valores muito longos para não poluir
                    row_str = str(row)
                    if len(row_str) > 100:
                        row_str = row_str[:100] + "..."
                    print(f"      [{i}]: {row_str}")
            
            # Índices
            cursor.execute(f"PRAGMA index_list({tabela})")
            indices = cursor.fetchall()
            if indices:
                print(f"   Índices: {len(indices)}")
                for idx in indices:
                    print(f"      - {idx[1]} ({'UNIQUE' if idx[2] else 'normal'})")
        
        conn.close()
        print(f"\n{'='*60}")
        print("✅ Inspeção concluída")
        
    except sqlite3.Error as e:
        print(f"\n💥 ERRO SQLite: {e}")
        import traceback
        traceback.print_exc()

# Uso:
inspecionar_banco("seu_arquivo.db")