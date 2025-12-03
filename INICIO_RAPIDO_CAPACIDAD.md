# 🚀 INICIO RÁPIDO - Pruebas de Capacidad

## ✅ Instalación Completada

Las herramientas están listas:
- ✅ Locust 2.42.6
- ✅ pytest-benchmark 5.2.3
- ✅ requests 2.32.4

---

## 📋 PASO A PASO PARA EJECUTAR

### **Opción 1: Ejecutar Suite Completa Automática** (Recomendado)

```powershell
# 1. Iniciar servidor en Terminal 1
cd C:\Users\luisc\Desktop\aconex_rag_starter\backend-acorag
python -m uvicorn server:app --reload --port 8000

# 2. En Terminal 2, ejecutar suite automática
python run_capacity_tests.py
```

Esto ejecutará automáticamente:
- ✅ Benchmarks con pytest
- ✅ Carga ligera (50 usuarios)
- ✅ Carga media (100 usuarios) 
- ✅ Prueba de estrés (200 usuarios)
- ✅ Generación de reportes HTML

---

### **Opción 2: Ejecutar Pruebas Manualmente**

#### **A. BENCHMARKS (Rápidos - 2 minutos)**

```powershell
# Benchmarks básicos
pytest tests/test_performance.py -v --benchmark-only

# Con estadísticas detalladas
pytest tests/test_performance.py --benchmark-only --benchmark-verbose

# Guardar como baseline
pytest tests/test_performance.py --benchmark-only --benchmark-save=baseline_v1
```

#### **B. LOCUST CON INTERFAZ WEB** (Interactivo - Recomendado para primera vez)

```powershell
# Iniciar Locust UI
locust -f locustfile.py --host=http://localhost:8000

# Abrir navegador en: http://localhost:8089
# Configurar:
#   - Number of users: 50
#   - Spawn rate: 5
#   - Click "Start swarming"
```

#### **C. LOCUST HEADLESS** (Automático)

```powershell
# Prueba ligera: 50 usuarios, 5 minutos
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000 --html reporte_50users.html

# Prueba media: 100 usuarios, 5 minutos
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --host=http://localhost:8000 --html reporte_100users.html

# Prueba de estrés: 200 usuarios, 3 minutos
locust -f locustfile.py --headless --users 200 --spawn-rate 20 --run-time 3m --host=http://localhost:8000 --html reporte_200users.html
```

---

## 📊 RESULTADOS ESPERADOS

### **Benchmarks (pytest)**

```
Name (time in ms)                    Min      Max     Mean   StdDev   Median
test_search_performance_basic      234.56   567.89  312.45    45.67   298.12
test_normalize_doc_performance       2.34     5.67    3.12     0.45     2.98
test_chunking_large_text            45.23    89.12   56.78     8.90    54.32
```

### **Locust (Carga)**

```
Type     Name           # reqs  # fails  Avg     Min    Max    Median  req/s
POST     /search        5234    12       387ms   45ms   2341ms 320ms   87.2
POST     /chat          2145    8        1203ms  234ms  4567ms 1100ms  35.8
GET      /health        428     2        156ms   23ms   891ms  140ms   7.1
```

---

## 🎯 OBJETIVOS DE PERFORMANCE

| Operación | Objetivo | Carga |
|-----------|----------|-------|
| Búsqueda semántica | < 500ms (p95) | 50 usuarios |
| Chat RAG | < 2s (p95) | 20 usuarios |
| Upload | < 5s | 10 concurrentes |

---

## 📝 DOCUMENTAR RESULTADOS

1. **Copiar resultados de benchmarks**
   - De la terminal, copiar tabla de resultados
   
2. **Tomar screenshots de Locust**
   - Gráfica de RPS
   - Tabla de response times
   - Charts

3. **Actualizar PRUEBAS_CAPACIDAD.md**
   - Sección "Resultados Obtenidos"
   - Agregar tablas con datos reales
   - Incluir conclusiones

4. **Guardar reportes HTML**
   - Los archivos `.html` generados
   - Abrirlos en navegador para análisis

---

## 🔍 TROUBLESHOOTING

### ❌ Error: "Connection refused"
**Solución**: Verificar que el servidor esté corriendo
```powershell
curl http://localhost:8000/health
```

### ⚠️ Warning: "High response times"
**Solución**: Reducir número de usuarios o verificar BD
```powershell
# Reducir carga
locust -f locustfile.py --users 25 --spawn-rate 3 ...
```

### 🐌 Performance degradado
**Solución**: Usar múltiples workers de gunicorn
```powershell
pip install gunicorn
gunicorn server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## ✅ CHECKLIST

Antes de documentar resultados:

- [ ] Servidor corriendo en localhost:8000
- [ ] Benchmarks ejecutados y guardados
- [ ] Al menos 1 prueba de Locust completada
- [ ] Screenshots/reportes HTML guardados
- [ ] Métricas de CPU/memoria observadas
- [ ] Resultados copiados a PRUEBAS_CAPACIDAD.md

---

## 📞 SIGUIENTE PASO

Una vez ejecutadas las pruebas:

```powershell
# Abrir documento para documentar
code PRUEBAS_CAPACIDAD.md

# Sección a completar: "Resultados Obtenidos"
```

---

**¡Listo para ejecutar!** 🚀

Ejecuta cualquiera de las opciones arriba y documenta los resultados.
