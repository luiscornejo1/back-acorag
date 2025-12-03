# 🔧 GUÍA TÉCNICA - Implementación y Optimización

## 📋 Índice
1. [Correcciones Inmediatas](#correcciones-inmediatas)
2. [Optimizaciones Recomendadas](#optimizaciones-recomendadas)
3. [Monitoreo y Observabilidad](#monitoreo-y-observabilidad)
4. [Escalamiento](#escalamiento)
5. [Checklist Pre-Deployment](#checklist-pre-deployment)

---

## 🔴 Correcciones Inmediatas

### 1. Fix: Error en Locust Tests (PRIORIDAD ALTA)

**Problema**: 
```
LocustError: In order to use a with-block for requests, 
you must also pass catch_response=True
```

**Ubicación**: `locustfile.py` líneas 143, 156, 174

**Solución**:

```python
# ANTES (línea 143):
with self.client.post("/search", json=payload, name="Search Documents") as response:
    if response.status_code == 200:
        pass

# DESPUÉS:
with self.client.post("/search", json=payload, name="Search Documents", catch_response=True) as response:
    if response.status_code == 200:
        response.success()
    else:
        response.failure(f"Got status code {response.status_code}")
```

**Aplicar en todas las tareas**:

```python
@task(3)
def chat(self):
    payload = {
        "message": random.choice(self.queries),
        "conversation_id": f"conv_{random.randint(1, 100)}"
    }
    
    with self.client.post("/chat", json=payload, name="Chat Query", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Chat failed: {response.status_code}")

@task(1)
def get_history(self):
    conv_id = f"conv_{random.randint(1, 100)}"
    
    with self.client.get(f"/history/{conv_id}", name="Get History", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"History failed: {response.status_code}")

@task(1)
def health_check(self):
    with self.client.get("/health", name="Health Check", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Health check failed: {response.status_code}")
```

**Tiempo estimado**: 10 minutos  
**Impacto**: ✅ Elimina 100% de errores falsos en pruebas

---

### 2. Fix: Warm-up del Servidor

**Problema**: Outlier de 83.8ms en primera búsqueda (cold start)

**Solución**: Agregar warm-up antes de pruebas

```python
# Agregar al inicio de las pruebas (antes de Locust)
# warm_up.py
import requests
import time

def warm_up_server(host="http://localhost:8000", iterations=100):
    """Pre-calentar servidor antes de pruebas de carga"""
    print("🔥 Warm-up del servidor...")
    
    queries = [
        "proyecto aconex",
        "documentación técnica",
        "búsqueda rápida",
        "performance test"
    ]
    
    for i in range(iterations):
        try:
            # Búsquedas de calentamiento
            response = requests.post(
                f"{host}/search",
                json={"query": queries[i % len(queries)], "top_k": 5},
                timeout=5
            )
            
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{iterations} requests...")
                
        except Exception as e:
            print(f"  ⚠️ Error en warm-up: {e}")
            
    print("✅ Warm-up completado\n")

if __name__ == "__main__":
    warm_up_server()
```

**Ejecutar antes de pruebas**:
```powershell
python warm_up.py
locust -f locustfile.py --headless --users 50 ...
```

**Tiempo estimado**: 5 minutos implementación + 2 minutos ejecución  
**Impacto**: ✅ Elimina outliers por cold start

---

## ⚡ Optimizaciones Recomendadas

### 3. Connection Pooling para PostgreSQL

**Beneficio**: Reduce latencia en conexiones a BD

```python
# config.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = "postgresql://user:pass@host:5432/db"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Conexiones permanentes
    max_overflow=40,       # Conexiones adicionales bajo carga
    pool_timeout=30,       # Timeout para obtener conexión
    pool_recycle=3600,     # Reciclar conexiones cada hora
    pool_pre_ping=True     # Verificar conexión antes de usar
)
```

**Impacto esperado**: 
- ✅ -50ms en latencia de búsquedas
- ✅ Soporte para 100+ usuarios concurrentes

---

### 4. Caching de Búsquedas Frecuentes

**Beneficio**: Reduce carga en BD y modelo de embeddings

```python
# cache.py
from functools import lru_cache
import hashlib

class SearchCache:
    def __init__(self, maxsize=1000):
        self.cache = {}
        self.maxsize = maxsize
    
    def get_cache_key(self, query: str, project_id: str, top_k: int) -> str:
        """Generar clave única para búsqueda"""
        data = f"{query}:{project_id}:{top_k}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, query: str, project_id: str, top_k: int):
        """Obtener resultado cacheado"""
        key = self.get_cache_key(query, project_id, top_k)
        return self.cache.get(key)
    
    def set(self, query: str, project_id: str, top_k: int, results):
        """Guardar resultado en caché"""
        if len(self.cache) >= self.maxsize:
            # Eliminar entrada más antigua (simple FIFO)
            self.cache.pop(next(iter(self.cache)))
        
        key = self.get_cache_key(query, project_id, top_k)
        self.cache[key] = results

# Uso en endpoint
cache = SearchCache(maxsize=1000)

@app.post("/search")
def search(req: SearchRequest):
    # Intentar obtener de caché
    cached = cache.get(req.query, req.project_id, req.top_k)
    if cached:
        return cached
    
    # Si no está en caché, ejecutar búsqueda
    results = semantic_search(req.query, req.project_id, req.top_k)
    
    # Guardar en caché
    cache.set(req.query, req.project_id, req.top_k, results)
    
    return results
```

**Impacto esperado**:
- ✅ -400ms en búsquedas repetidas (casi instantáneo)
- ✅ 10x más throughput para queries comunes
- ✅ Reduce carga en BD hasta 80%

---

### 5. Rate Limiting

**Beneficio**: Previene abuso y protege recursos

```python
# rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

# Agregar a app
from fastapi import FastAPI
app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Demasiadas solicitudes. Intente de nuevo en unos momentos."
        }
    )

# Aplicar a endpoints
@app.post("/search")
@limiter.limit("100/minute")  # 100 búsquedas por minuto por IP
async def search(request: Request, req: SearchRequest):
    ...

@app.post("/chat")
@limiter.limit("30/minute")   # 30 chats por minuto por IP
async def chat(request: Request, req: ChatRequest):
    ...

@app.post("/upload")
@limiter.limit("10/hour")     # 10 uploads por hora por IP
async def upload(request: Request):
    ...
```

**Instalación**:
```powershell
pip install slowapi
```

**Impacto esperado**:
- ✅ Previene ataques de denegación de servicio
- ✅ Distribución justa de recursos
- ✅ Protege contra bots

---

## 📊 Monitoreo y Observabilidad

### 6. APM (Application Performance Monitoring)

**Opción A: New Relic** (Recomendado para producción)

```python
# newrelic.ini (configuración)
[newrelic]
license_key = YOUR_LICENSE_KEY
app_name = Aconex RAG Production
monitor_mode = true
distributed_tracing.enabled = true

# Iniciar con New Relic
# powershell:
pip install newrelic
$env:NEW_RELIC_CONFIG_FILE="newrelic.ini"
newrelic-admin run-program python server.py
```

**Opción B: Prometheus + Grafana** (Open Source)

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Métricas
search_requests = Counter('search_requests_total', 'Total search requests')
search_duration = Histogram('search_duration_seconds', 'Search duration')
active_users = Gauge('active_users', 'Currently active users')
errors = Counter('errors_total', 'Total errors', ['endpoint'])

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Uso en endpoints
@app.post("/search")
async def search(req: SearchRequest):
    search_requests.inc()
    
    with search_duration.time():
        try:
            results = semantic_search(req.query, req.project_id, req.top_k)
            return results
        except Exception as e:
            errors.labels(endpoint='search').inc()
            raise
```

**Instalación**:
```powershell
pip install prometheus-client
```

**Dashboard Grafana**: Importar plantilla #11159

---

### 7. Logging Estructurado

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar extras si existen
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_obj['duration_ms'] = record.duration_ms
            
        return json.dumps(log_obj)

# Configurar logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger('aconex_rag')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Uso
@app.post("/search")
async def search(req: SearchRequest):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    logger.info(
        f"Search request",
        extra={
            'request_id': request_id,
            'query': req.query[:50],  # Solo primeros 50 chars
            'project_id': req.project_id
        }
    )
    
    results = semantic_search(req.query, req.project_id, req.top_k)
    
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"Search completed",
        extra={
            'request_id': request_id,
            'duration_ms': duration_ms,
            'results_count': len(results)
        }
    )
    
    return results
```

---

## 🚀 Escalamiento

### 8. Configuración Multi-Worker con Gunicorn

```python
# gunicorn.conf.py
import multiprocessing

# Configuración básica
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1  # Fórmula recomendada
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120

# Performance
worker_connections = 1000
max_requests = 10000  # Reciclar workers después de 10k requests
max_requests_jitter = 1000
timeout = 120

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Monitoreo
proc_name = "aconex_rag"
```

**Ejecutar**:
```powershell
pip install gunicorn
gunicorn server:app -c gunicorn.conf.py
```

**Impacto esperado**:
- ✅ 4-8x más throughput (según CPU cores)
- ✅ Soporte para 200-500 usuarios concurrentes
- ✅ Mejor utilización de CPU

---

### 9. Auto-escalamiento con Docker + Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aconex-rag
spec:
  replicas: 3  # Mínimo 3 pods
  selector:
    matchLabels:
      app: aconex-rag
  template:
    metadata:
      labels:
        app: aconex-rag
    spec:
      containers:
      - name: aconex-rag
        image: aconex-rag:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aconex-rag-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aconex-rag
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## ✅ Checklist Pre-Deployment

### Código y Tests

- [x] Tests de performance ejecutados
- [ ] Tests de carga de 1 hora completados
- [ ] Scripts de Locust corregidos
- [ ] Warm-up implementado
- [ ] Todos los tests funcionales pasan

### Infraestructura

- [ ] Connection pooling configurado
- [ ] Rate limiting implementado
- [ ] Gunicorn multi-worker configurado
- [ ] Variables de entorno en producción
- [ ] Certificados SSL configurados

### Monitoreo

- [ ] APM configurado (New Relic/Prometheus)
- [ ] Logging estructurado implementado
- [ ] Alertas configuradas:
  - [ ] Response time > 500ms
  - [ ] Error rate > 1%
  - [ ] CPU > 80%
  - [ ] Memory > 85%
  - [ ] Disk > 90%
- [ ] Dashboard de Grafana creado

### Seguridad

- [ ] Rate limiting activo
- [ ] CORS configurado correctamente
- [ ] Secrets en variables de entorno (no en código)
- [ ] HTTPS habilitado
- [ ] Headers de seguridad configurados

### Backup y Recuperación

- [ ] Backup automático de BD configurado
- [ ] Procedimiento de rollback documentado
- [ ] Disaster recovery plan
- [ ] Prueba de restauración completada

### Documentación

- [x] PRUEBAS_CAPACIDAD.md completo
- [x] RESUMEN_EJECUTIVO_CAPACIDAD.md creado
- [x] VISUALIZACION_RESULTADOS_CAPACIDAD.md generado
- [ ] Runbook de operaciones
- [ ] Documentación API actualizada

---

## 📞 Recursos y Referencias

### Herramientas Mencionadas

- **Locust**: https://locust.io/
- **pytest-benchmark**: https://pytest-benchmark.readthedocs.io/
- **New Relic**: https://newrelic.com/
- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/
- **slowapi** (rate limiting): https://github.com/laurentS/slowapi

### Documentos Relacionados

- [PRUEBAS_CAPACIDAD.md](PRUEBAS_CAPACIDAD.md)
- [RESUMEN_EJECUTIVO_CAPACIDAD.md](RESUMEN_EJECUTIVO_CAPACIDAD.md)
- [VISUALIZACION_RESULTADOS_CAPACIDAD.md](VISUALIZACION_RESULTADOS_CAPACIDAD.md)
- [PRUEBAS_CAJA_NEGRA.md](PRUEBAS_CAJA_NEGRA.md)

---

**Autor**: Luis Cornejo  
**Fecha**: 3 de Diciembre, 2025  
**Próxima Revisión**: Post-deployment (1 semana después de go-live)
