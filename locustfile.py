"""
Locustfile para pruebas de carga del sistema RAG Aconex

Simula usuarios reales realizando operaciones típicas:
- Búsquedas semánticas
- Consultas de chat
- Obtención de historial

Uso:
    # Modo UI (recomendado para primeras pruebas)
    locust -f locustfile.py --host=http://localhost:8000
    
    # Modo headless (para CI/CD)
    locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AconexRAGUser(HttpUser):
    """
    Usuario simulado que interactúa con el sistema RAG
    
    Distribución de tareas (por peso):
    - Búsqueda semántica: 60% (peso 6)
    - Chat conversacional: 30% (peso 3)
    - Historial: 10% (peso 1)
    """
    
    # Tiempo de espera entre requests (simula tiempo de lectura del usuario)
    wait_time = between(1, 3)  # Entre 1 y 3 segundos
    
    # Queries realistas para búsquedas
    search_queries = [
        "construcción sismo resistente",
        "planos arquitectónicos edificio",
        "especificaciones técnicas concreto",
        "normativa vigente construcción",
        "materiales de construcción certificados",
        "diseño estructural columnas",
        "sistema eléctrico instalaciones",
        "plomería y sanitarios",
        "acabados interiores",
        "plan maestro arquitectura"
    ]
    
    # Preguntas realistas para chat
    chat_questions = [
        "¿Qué incluye el plan maestro de arquitectura?",
        "¿Cuáles son las especificaciones del concreto?",
        "¿Qué normativa sísmica se aplica en este proyecto?",
        "¿Cuántas aulas contempla el diseño?",
        "¿Qué sistema de cimentación se utiliza?",
        "¿Cuál es la resistencia del concreto especificado?",
        "¿Qué materiales se usan en la estructura?",
        "¿Cuáles son los planos aprobados?"
    ]
    
    def on_start(self):
        """Se ejecuta cuando un usuario virtual comienza"""
        self.project_id = random.choice(["PROJ-001", "PROJ-002", "PROJ-TEST"])
        self.user_id = f"user-{random.randint(1000, 9999)}"
        logger.info(f"Usuario {self.user_id} iniciado en proyecto {self.project_id}")
    
    @task(6)  # Peso 6: se ejecuta 6 veces más frecuente
    def search_documents(self):
        """
        Tarea: Búsqueda semántica de documentos
        
        Simula un usuario buscando información técnica
        """
        query = random.choice(self.search_queries)
        
        payload = {
            "query": query,
            "project_id": self.project_id,
            "top_k": random.choice([5, 10, 20]),
            "probes": 10
        }
        
        with self.client.post(
            "/search",
            json=payload,
            catch_response=True,
            name="Search Documents"
        ) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                        logger.debug(f"Search OK: {len(data)} resultados")
                    else:
                        response.failure(f"Formato inesperado: {type(data)}")
                else:
                    response.failure(f"Status {response.status_code}")
            except Exception as e:
                response.failure(f"Error: {str(e)}")
    
    @task(3)  # Peso 3: menos frecuente que búsqueda
    def chat_query(self):
        """
        Tarea: Chat conversacional con RAG
        
        Simula un usuario haciendo preguntas en lenguaje natural
        """
        question = random.choice(self.chat_questions)
        
        payload = {
            "question": question,
            "max_context_docs": random.choice([3, 5, 7]),
            "project_id": self.project_id,
            "session_id": f"session-{self.user_id}"
        }
        
        with self.client.post(
            "/chat",
            json=payload,
            catch_response=True,
            name="Chat Query"
        ) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "answer" in data:
                        response.success()
                        logger.debug(f"Chat OK: {len(data['answer'])} chars")
                    else:
                        response.failure("No answer in response")
                else:
                    response.failure(f"Status {response.status_code}")
            except Exception as e:
                response.failure(f"Error: {str(e)}")
    
    @task(1)  # Peso 1: operación menos frecuente
    def get_history(self):
        """
        Tarea: Obtener historial de chat
        
        Simula un usuario revisando conversaciones anteriores
        """
        with self.client.get(
            f"/chat/history/{self.user_id}?limit=20",
            catch_response=True,
            name="Get History"
        ) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    response.success()
                    logger.debug(f"History OK: {len(data)} items")
                elif response.status_code == 404:
                    # Usuario nuevo sin historial es válido
                    response.success()
                else:
                    response.failure(f"Status {response.status_code}")
            except Exception as e:
                response.failure(f"Error: {str(e)}")
    
    @task(1)
    def health_check(self):
        """
        Tarea: Health check del sistema
        
        Simula monitoreo básico
        """
        with self.client.get("/health", name="Health Check") as response:
            if response.status_code != 200:
                logger.warning(f"Health check failed: {response.status_code}")


# ==============================================================================
# EVENTOS PERSONALIZADOS
# ==============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al iniciar la prueba"""
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO PRUEBA DE CARGA - SISTEMA RAG ACONEX")
    logger.info("=" * 80)
    logger.info(f"Host: {environment.host}")
    logger.info(f"Usuarios objetivo: {environment.parsed_options.num_users if hasattr(environment, 'parsed_options') else 'N/A'}")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al finalizar la prueba"""
    logger.info("=" * 80)
    logger.info("✅ PRUEBA DE CARGA FINALIZADA")
    logger.info("=" * 80)
    
    # Obtener estadísticas
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    
    if total_requests > 0:
        error_rate = (total_failures / total_requests) * 100
        logger.info(f"Total Requests: {total_requests}")
        logger.info(f"Total Failures: {total_failures}")
        logger.info(f"Error Rate: {error_rate:.2f}%")
        logger.info(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
        logger.info(f"RPS: {stats.total.current_rps:.2f}")
    
    logger.info("=" * 80)


# ==============================================================================
# LOAD TEST SHAPES (Formas de carga personalizadas)
# ==============================================================================

from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    Forma de carga por pasos (escalera)
    
    Incrementa usuarios gradualmente:
    - Paso 1: 10 usuarios por 2 minutos
    - Paso 2: 25 usuarios por 2 minutos
    - Paso 3: 50 usuarios por 3 minutos
    - Paso 4: 75 usuarios por 2 minutos
    - Paso 5: 100 usuarios por 1 minuto
    """
    
    step_time = 60  # Duración de cada paso en segundos
    step_load = 10  # Usuarios a agregar en cada paso
    spawn_rate = 5  # Usuarios por segundo al escalar
    
    stages = [
        {"duration": 120, "users": 10, "spawn_rate": 2},
        {"duration": 240, "users": 25, "spawn_rate": 5},
        {"duration": 420, "users": 50, "spawn_rate": 5},
        {"duration": 540, "users": 75, "spawn_rate": 10},
        {"duration": 600, "users": 100, "spawn_rate": 10},
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None  # Terminar prueba


class SpikeLoadShape(LoadTestShape):
    """
    Forma de carga con pico (spike)
    
    Simula tráfico repentino:
    - Base: 20 usuarios
    - Pico: 150 usuarios por 5 minutos
    - Regreso: 20 usuarios
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},      # Calentamiento
        {"duration": 120, "users": 20, "spawn_rate": 5},     # Base normal
        {"duration": 150, "users": 150, "spawn_rate": 50},   # PICO REPENTINO
        {"duration": 450, "users": 150, "spawn_rate": 0},    # Mantener pico 5 min
        {"duration": 510, "users": 20, "spawn_rate": 30},    # Regreso a normal
        {"duration": 600, "users": 20, "spawn_rate": 0},     # Mantener normal
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None


# ==============================================================================
# USO
# ==============================================================================
"""
COMANDOS ÚTILES:

1. Prueba básica con UI:
   locust -f locustfile.py --host=http://localhost:8000
   Luego abrir: http://localhost:8089

2. Prueba headless (sin UI):
   locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000

3. Con carga por pasos (StepLoadShape):
   # Descomentar la clase que hereda de LoadTestShape en AconexRAGUser
   locust -f locustfile.py --host=http://localhost:8000

4. Generar reporte HTML:
   locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host=http://localhost:8000 --html report.html

5. Modo distribuido (múltiples máquinas):
   # Master
   locust -f locustfile.py --master --host=http://localhost:8000
   
   # Workers (en otras máquinas)
   locust -f locustfile.py --worker --master-host=192.168.1.100
"""
