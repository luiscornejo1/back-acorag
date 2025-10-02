#!/usr/bin/env python3
"""
Script para verificar las columnas de la tabla documents
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('=== ESTRUCTURA DE DOCUMENTS ===')
    cur.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'documents' 
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    for col_name, col_type, nullable in columns:
        print(f'{col_name}: {col_type} (nullable: {nullable})')

    print('\n=== SAMPLE DE DATOS ===')
    cur.execute("SELECT * FROM documents LIMIT 3")
    rows = cur.fetchall()
    
    # Obtener nombres de columnas
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'documents' 
        ORDER BY ordinal_position
    """)
    col_names = [row[0] for row in cur.fetchall()]
    
    for i, row in enumerate(rows):
        print(f'\nDocumento {i+1}:')
        for j, value in enumerate(row):
            if j < len(col_names):
                print(f'  {col_names[j]}: {value}')

    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")