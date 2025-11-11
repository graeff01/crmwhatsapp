import sqlite3

conn = sqlite3.connect("crm_whatsapp.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(leads)")
columns = [col[1] for col in cursor.fetchall()]

# Adiciona coluna 'origin' se não existir
if "origin" not in columns:
    cursor.execute("ALTER TABLE leads ADD COLUMN origin TEXT;")
    print("✅ Coluna 'origin' adicionada com sucesso!")
else:
    print("ℹ️ A coluna 'origin' já existe.")

conn.commit()
conn.close()
