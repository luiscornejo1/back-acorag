"""
Script para ejecutar suite completa de pruebas de capacidad

Ejecuta automáticamente todas las pruebas en secuencia y genera reportes
"""

import subprocess
import time
import os
import sys
from datetime import datetime

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{message.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")


def print_step(step_num, message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}[Paso {step_num}]{Colors.END} {message}")


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def run_command(cmd, description, timeout=None, check_error=True):
    """Ejecuta un comando y muestra resultado"""
    print(f"\n{Colors.CYAN}Ejecutando:{Colors.END} {description}")
    print(f"{Colors.CYAN}Comando:{Colors.END} {cmd}")
    
    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        
        if result.returncode == 0:
            print_success(f"{description} completado")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            if check_error:
                print_error(f"{description} falló")
                if result.stderr:
                    print(result.stderr)
                return False
            else:
                print_warning(f"{description} completado con warnings")
                return True
    
    except subprocess.TimeoutExpired:
        print_error(f"{description} excedió tiempo límite")
        return False
    except Exception as e:
        print_error(f"Error ejecutando {description}: {str(e)}")
        return False


def check_server_running():
    """Verifica si el servidor está corriendo"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    print_header("SUITE DE PRUEBAS DE CAPACIDAD - SISTEMA RAG ACONEX")
    
    # Timestamp para reportes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = f"performance_reports_{timestamp}"
    
    # ===========================================================================
    # PASO 0: VERIFICACIONES PREVIAS
    # ===========================================================================
    print_step(0, "Verificaciones previas")
    
    # Verificar Python
    python_version = sys.version_info
    print(f"Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_error("Se requiere Python 3.8 o superior")
        return
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("locustfile.py"):
        print_error("No se encuentra locustfile.py. Ejecuta desde backend-acorag/")
        return
    
    print_success("Verificaciones completadas")
    
    # ===========================================================================
    # PASO 1: INSTALAR DEPENDENCIAS
    # ===========================================================================
    print_step(1, "Instalando dependencias necesarias")
    
    dependencies = ["locust", "pytest-benchmark", "requests"]
    for dep in dependencies:
        run_command(
            f"pip install {dep}",
            f"Instalando {dep}",
            timeout=60
        )
    
    # ===========================================================================
    # PASO 2: VERIFICAR SERVIDOR
    # ===========================================================================
    print_step(2, "Verificando servidor")
    
    if check_server_running():
        print_success("Servidor corriendo en http://localhost:8000")
    else:
        print_warning("Servidor no detectado. Iniciándolo...")
        print(f"\n{Colors.YELLOW}NOTA: El servidor se iniciará en segundo plano.{Colors.END}")
        print(f"{Colors.YELLOW}Presiona Ctrl+C al final para detenerlo.{Colors.END}\n")
        
        # Iniciar servidor en background (no funciona bien en Windows)
        # En su lugar, mostrar instrucciones
        print_error("Por favor, inicia el servidor manualmente en otra terminal:")
        print(f"{Colors.CYAN}python -m uvicorn server:app --reload --port 8000{Colors.END}")
        input("\nPresiona Enter cuando el servidor esté corriendo...")
        
        if not check_server_running():
            print_error("Servidor no disponible. Abortando.")
            return
    
    # Crear directorio de reportes
    os.makedirs(report_dir, exist_ok=True)
    print_success(f"Directorio de reportes creado: {report_dir}/")
    
    # ===========================================================================
    # PASO 3: BENCHMARKS CON PYTEST
    # ===========================================================================
    print_step(3, "Ejecutando benchmarks con pytest-benchmark")
    
    benchmark_results = f"{report_dir}/benchmark_results.txt"
    
    # Benchmark básico
    if run_command(
        f"pytest tests/test_performance.py --benchmark-only --benchmark-verbose > {benchmark_results}",
        "Benchmarks básicos",
        timeout=300
    ):
        print_success(f"Resultados guardados en {benchmark_results}")
    
    # Guardar como baseline
    run_command(
        f"pytest tests/test_performance.py --benchmark-only --benchmark-save=baseline_{timestamp}",
        "Guardando baseline",
        timeout=300
    )
    
    time.sleep(2)
    
    # ===========================================================================
    # PASO 4: PRUEBA DE CARGA LIGERA (50 usuarios, 2 min)
    # ===========================================================================
    print_step(4, "Prueba de carga ligera (50 usuarios, 2 minutos)")
    
    light_report = f"{report_dir}/light_load_50users.html"
    
    run_command(
        f"locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m --host=http://localhost:8000 --html {light_report}",
        "Carga ligera",
        timeout=180,
        check_error=False
    )
    
    time.sleep(5)
    
    # ===========================================================================
    # PASO 5: PRUEBA DE CARGA MEDIA (100 usuarios, 3 min)
    # ===========================================================================
    print_step(5, "Prueba de carga media (100 usuarios, 3 minutos)")
    
    medium_report = f"{report_dir}/medium_load_100users.html"
    
    run_command(
        f"locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 3m --host=http://localhost:8000 --html {medium_report}",
        "Carga media",
        timeout=240,
        check_error=False
    )
    
    time.sleep(5)
    
    # ===========================================================================
    # PASO 6: PRUEBA DE ESTRÉS (200 usuarios, 2 min)
    # ===========================================================================
    print_step(6, "Prueba de estrés (200 usuarios, 2 minutos)")
    
    stress_report = f"{report_dir}/stress_load_200users.html"
    
    run_command(
        f"locust -f locustfile.py --headless --users 200 --spawn-rate 20 --run-time 2m --host=http://localhost:8000 --html {stress_report}",
        "Prueba de estrés",
        timeout=180,
        check_error=False
    )
    
    # ===========================================================================
    # RESUMEN FINAL
    # ===========================================================================
    print_header("RESUMEN DE PRUEBAS COMPLETADAS")
    
    print(f"\n{Colors.BOLD}Reportes generados en:{Colors.END} {report_dir}/\n")
    
    files = [
        ("benchmark_results.txt", "Resultados de benchmarks"),
        ("light_load_50users.html", "Carga ligera - 50 usuarios"),
        ("medium_load_100users.html", "Carga media - 100 usuarios"),
        ("stress_load_200users.html", "Estrés - 200 usuarios")
    ]
    
    for filename, description in files:
        filepath = os.path.join(report_dir, filename)
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"  {Colors.GREEN}✓{Colors.END} {description}")
            print(f"    {Colors.CYAN}→{Colors.END} {filepath} ({size_kb:.2f} KB)")
        else:
            print(f"  {Colors.YELLOW}⚠{Colors.END} {description} - No generado")
    
    print(f"\n{Colors.BOLD}Próximos pasos:{Colors.END}")
    print("  1. Revisar reportes HTML en navegador")
    print("  2. Analizar tiempos de respuesta y throughput")
    print("  3. Documentar resultados en PRUEBAS_CAPACIDAD.md")
    print("  4. Identificar cuellos de botella")
    print("  5. Optimizar según hallazgos\n")
    
    # Abrir reporte principal
    try:
        import webbrowser
        if os.path.exists(f"{report_dir}/medium_load_100users.html"):
            print(f"{Colors.CYAN}Abriendo reporte principal en navegador...{Colors.END}")
            webbrowser.open(f"{report_dir}/medium_load_100users.html")
    except:
        pass
    
    print_header("¡PRUEBAS COMPLETADAS!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Pruebas interrumpidas por el usuario{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Error inesperado: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
