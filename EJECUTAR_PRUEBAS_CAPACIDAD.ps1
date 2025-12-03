# Guía de Ejecución - Pruebas de Capacidad
# ==========================================

# IMPORTANTE: Ejecutar estos comandos desde backend-acorag/

# ==============================================================================
# PASO 1: INSTALAR DEPENDENCIAS
# ==============================================================================

pip install locust pytest-benchmark

# O agregar a requirements-test.txt:
echo "locust==2.20.0" >> requirements-test.txt
echo "pytest-benchmark==4.0.0" >> requirements-test.txt
pip install -r requirements-test.txt


# ==============================================================================
# PASO 2: INICIAR EL SERVIDOR
# ==============================================================================

# Terminal 1: Iniciar servidor FastAPI
cd backend-acorag
python -m uvicorn server:app --reload --port 8000

# Verificar que funciona:
curl http://localhost:8000/health


# ==============================================================================
# PASO 3: EJECUTAR PRUEBAS DE BENCHMARK
# ==============================================================================

# Benchmarks básicos
pytest tests/test_performance.py -v --benchmark-only

# Con estadísticas detalladas
pytest tests/test_performance.py --benchmark-only --benchmark-verbose

# Solo benchmarks de búsqueda
pytest tests/test_performance.py -k "search" --benchmark-only

# Solo benchmarks de ingesta
pytest tests/test_performance.py -k "ingest" --benchmark-only

# Guardar resultados como baseline
pytest tests/test_performance.py --benchmark-only --benchmark-save=baseline_v1

# Comparar con baseline anterior
pytest tests/test_performance.py --benchmark-only --benchmark-compare=baseline_v1

# Generar histograma visual
pytest tests/test_performance.py --benchmark-only --benchmark-histogram


# ==============================================================================
# PASO 4: EJECUTAR PRUEBAS DE CARGA CON LOCUST (MODO UI)
# ==============================================================================

# Terminal 2: Iniciar Locust con interfaz web
locust -f locustfile.py --host=http://localhost:8000

# Luego abrir en navegador: http://localhost:8089

# En la UI configurar:
# - Number of users: 50
# - Spawn rate: 5 (usuarios por segundo)
# - Host: http://localhost:8000
# - Click "Start swarming"

# Dejar correr por 5-10 minutos y observar:
# - RPS (requests per second)
# - Response times (p50, p95, p99)
# - Failure rate


# ==============================================================================
# PASO 5: PRUEBAS DE CARGA HEADLESS (SIN UI)
# ==============================================================================

# Prueba básica: 50 usuarios por 5 minutos
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000

# Prueba con más usuarios: 100 usuarios por 10 minutos
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 10m --host=http://localhost:8000

# Generar reporte HTML
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000 --html reporte_carga.html

# Ver reporte
start reporte_carga.html  # Windows


# ==============================================================================
# PASO 6: PRUEBAS DE ESTRÉS PROGRESIVAS
# ==============================================================================

# Crear stress_test.py con StepLoadShape (ya incluido en locustfile.py)
# Ejecutar con carga escalonada:
locust -f locustfile.py --host=http://localhost:8000

# Esto ejecutará automáticamente la carga por pasos:
# 10 → 25 → 50 → 75 → 100 usuarios


# ==============================================================================
# PASO 7: PRUEBAS DE PICOS (SPIKE TESTING)
# ==============================================================================

# Usar SpikeLoadShape del locustfile.py
# Comentar/descomentar la clase shape deseada en locustfile.py
locust -f locustfile.py --host=http://localhost:8000


# ==============================================================================
# PASO 8: MONITOREO DURANTE PRUEBAS
# ==============================================================================

# Terminal 3: Monitorear recursos del sistema
# Windows PowerShell:
while ($true) {
    Clear-Host
    Write-Host "=== MONITOREO DE RECURSOS ===" -ForegroundColor Cyan
    Get-Process python | Format-Table Name, CPU, PM, WS -AutoSize
    Start-Sleep -Seconds 5
}

# O usar Task Manager / Resource Monitor


# ==============================================================================
# PASO 9: ANÁLISIS DE BASE DE DATOS
# ==============================================================================

# Conectar a PostgreSQL y verificar queries lentas
# psql -h localhost -U usuario -d nombre_db

# Queries útiles:
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

# Ver conexiones activas
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';


# ==============================================================================
# PASO 10: PRUEBAS DE VOLUMEN (MANUAL)
# ==============================================================================

# Test de ingesta masiva (crear script)
python -c "
from app.ingest import ingest_document
import time

start = time.time()
for i in range(1000):
    doc = {
        'DocumentId': f'DOC-{i:05d}',
        'project_id': 'VOLUME-TEST',
        'metadata': {'Title': f'Doc {i}'},
        'full_text': f'Content {i}' * 100
    }
    ingest_document(doc)
    if i % 100 == 0:
        print(f'Ingested {i} docs...')

duration = time.time() - start
rate = 1000 / duration
print(f'Ingested 1000 docs in {duration:.2f}s ({rate:.2f} docs/s)')
"


# ==============================================================================
# EJEMPLOS DE RESULTADOS ESPERADOS
# ==============================================================================

# BENCHMARK RESULTS (pytest-benchmark):
# --------------------------------------------------------------------------------
# Name (time in ms)                    Min      Max     Mean   StdDev   Median
# --------------------------------------------------------------------------------
# test_search_performance_basic      234.56   567.89  312.45    45.67   298.12
# test_normalize_doc_performance       2.34     5.67    3.12     0.45     2.98
# test_chunking_large_text            45.23    89.12   56.78     8.90    54.32
# --------------------------------------------------------------------------------

# LOCUST RESULTS:
# Type     Name           # reqs  # fails  Avg     Min    Max    Median  req/s
# POST     /search        5234    12       387ms   45ms   2341ms 320ms   87.2
# POST     /chat          2145    8        1203ms  234ms  4567ms 1100ms  35.8
# GET      /health        428     2        156ms   23ms   891ms  140ms   7.1
# --------------------------------------------------------------------------------
# Aggregated              7807    22       541ms   23ms   4567ms 450ms   130.1


# ==============================================================================
# TROUBLESHOOTING
# ==============================================================================

# Problema: "Connection refused"
# Solución: Verificar que el servidor está corriendo en el puerto correcto
curl http://localhost:8000/health

# Problema: "Too many connections"
# Solución: Aumentar pool de conexiones de BD
# En DATABASE_URL: ?pool_size=20&max_overflow=40

# Problema: Tiempos de respuesta muy altos
# Solución 1: Verificar índices en BD
# Solución 2: Usar gunicorn con múltiples workers
gunicorn server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Problema: Memory leak
# Solución: Monitorear con memory_profiler
pip install memory-profiler
python -m memory_profiler script.py


# ==============================================================================
# CHECKLIST DE EJECUCIÓN
# ==============================================================================

# [ ] Servidor iniciado en http://localhost:8000
# [ ] Dependencias instaladas (locust, pytest-benchmark)
# [ ] Benchmarks ejecutados y guardados
# [ ] Prueba de carga básica (50 usuarios, 5 min)
# [ ] Prueba de estrés (escalamiento gradual)
# [ ] Prueba de picos (spike test)
# [ ] Reportes HTML generados
# [ ] Recursos monitoreados (CPU, memoria)
# [ ] Resultados documentados en PRUEBAS_CAPACIDAD.md


# ==============================================================================
# NEXT STEPS: DOCUMENTAR RESULTADOS
# ==============================================================================

# 1. Tomar screenshots de Locust UI
# 2. Copiar output de pytest-benchmark
# 3. Guardar reportes HTML
# 4. Actualizar PRUEBAS_CAPACIDAD.md con:
#    - Resultados reales obtenidos
#    - Gráficas de carga
#    - Conclusiones y recomendaciones
#    - Límites identificados del sistema
