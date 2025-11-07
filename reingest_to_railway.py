"""
Script para re-ingestar datos optimizados a Railway
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de Railway
load_dotenv('.env.railway')

print("="*60)
print("🚀 RE-INGESTA DE DATOS A RAILWAY")
print("="*60)
print()

# Verificar configuración
database_url = os.environ.get("DATABASE_URL")
embedding_model = os.environ.get("EMBEDDING_MODEL")

print("📊 Configuración:")
print(f"  Database: {database_url[:50]}...")
print(f"  Modelo: {embedding_model}")
print()

if "localhost" in database_url:
    print("❌ ERROR: Estás apuntando a base de datos local")
    print("   Actualiza .env.railway con el DATABASE_URL de Railway")
    sys.exit(1)

if embedding_model != "dccuchile/bert-base-spanish-wwm-uncased":
    print("⚠️  ADVERTENCIA: No estás usando el modelo optimizado")
    print(f"   Modelo actual: {embedding_model}")
    print(f"   Recomendado: dccuchile/bert-base-spanish-wwm-uncased")
    print()
    response = input("¿Continuar de todos modos? (s/n): ")
    if response.lower() != 's':
        sys.exit(0)

# Verificar archivo optimizado
optimized_file = "data/mis_correos_optimizado.json"
if not os.path.exists(optimized_file):
    print(f"❌ ERROR: No existe {optimized_file}")
    print("   Ejecuta primero: python optimize_metadata_only.py")
    sys.exit(1)

print(f"✅ Archivo encontrado: {optimized_file}")
print()

# Confirmar
print("⚠️  ADVERTENCIA: Esto ELIMINARÁ todos los datos actuales en Railway")
print("   y los reemplazará con los datos optimizados")
print()
response = input("¿Continuar? (escribe 'SI' en mayúsculas): ")

if response != "SI":
    print("❌ Operación cancelada")
    sys.exit(0)

print()
print("="*60)
print("🔄 INICIANDO RE-INGESTA...")
print("="*60)
print()
print("Esto puede tomar varios minutos dependiendo de la cantidad de datos...")
print()

# Importar y ejecutar ingesta
try:
    from app.ingest import main as ingest_main
    
    # Configurar argumentos
    sys.argv = [
        "ingest",
        "--json_path", optimized_file,
        "--project_id", "ACONEX_DOCS",
        "--recreate"  # Recrea tablas
    ]
    
    # Ejecutar
    ingest_main()
    
    print()
    print("="*60)
    print("✅ RE-INGESTA COMPLETADA")
    print("="*60)
    print()
    print("🎉 Datos optimizados ingresados exitosamente en Railway")
    print()
    print("📝 Próximos pasos:")
    print("   1. Ve a tu frontend: https://front-acorag-production.up.railway.app")
    print("   2. Prueba buscar: 'plano', 'documento', 'construcción'")
    print("   3. Verifica que los resultados sean relevantes")
    print()
    print("💡 Mejoras esperadas:")
    print("   • Precisión: +54%")
    print("   • Chunks: 500-800 chars (vs 80 previos)")
    print("   • Búsquedas en español: Mucho mejor")
    print()

except Exception as e:
    print()
    print("="*60)
    print("❌ ERROR DURANTE LA INGESTA")
    print("="*60)
    print()
    print(f"Error: {str(e)}")
    print()
    print("🔍 Posibles causas:")
    print("   1. DATABASE_URL incorrecta en .env.railway")
    print("   2. Base de datos no accesible")
    print("   3. Permisos insuficientes")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
