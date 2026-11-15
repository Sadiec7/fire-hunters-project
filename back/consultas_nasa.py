import pandas as pd
from sqlalchemy import create_engine

# Ajusta el ancho automáticamente al tamaño real de tu ventana de VS Code
pd.set_option('display.max_columns', 6)
pd.set_option('display.width', 110)
pd.set_option('display.max_colwidth', 28)

DB_URI = "postgresql://postgres.jhcegurjiqutptenqmxs:HackathonUAQ2026@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DB_URI)

tablas = pd.read_sql("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""", engine)['table_name'].tolist()

for t in tablas:
    print("\n" + "=" * 75)
    print(f"TABLA: {t.upper()}")
    print("=" * 75)
    
    df = pd.read_sql(f"SELECT * FROM public.{t} LIMIT 5;", engine).dropna(axis=1, how='all')
    
    # Oculta las columnas binarias encriptadas (BYTEA) para que no salgan caracteres raros
    cols_legibles = [c for c in df.columns if not c.endswith('_enc')]
    df = df[cols_legibles]
    
    if df.empty:
        print("(Tabla vacía)")
    else:
        print(df.to_string(index=False))
