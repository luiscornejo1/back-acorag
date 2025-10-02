#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('=== VERIFICANDO TABLAS ===')
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print('Tablas disponibles:', [t[0] for t in tables])

    print('\n=== CONTANDO REGISTROS ===')
    for table_name, in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f'{table_name}: {count:,} registros')
        except Exception as e:
            print(f'{table_name}: Error - {str(e)[:50]}...')

    print('\n=== VERIFICANDO ESTRUCTURA ===')
    for table_name, in tables:
        if 'chunk' in table_name.lower() or 'email' in table_name.lower():
            try:
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
                columns = cur.fetchall()
                print(f'\n{table_name}:')
                for col_name, col_type in columns:
                    print(f'  - {col_name}: {col_type}')
            except Exception as e:
                print(f'  Error: {e}')

    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error conectando a la base de datos: {e}")