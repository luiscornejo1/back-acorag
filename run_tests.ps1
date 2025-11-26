# ===================================================================
# Script de Ejecución de Tests para Aconex RAG
# ===================================================================
# Uso: .\run_tests.ps1 [opcion]
#
# Opciones:
#   all        - Ejecutar todos los tests
#   cov        - Ejecutar con cobertura
#   unit       - Solo tests unitarios
#   integration - Solo tests de integración
#   api        - Solo tests de API
#   fast       - Tests rápidos en paralelo
#   watch      - Modo watch (re-ejecuta en cambios)
# ===================================================================

param(
    [string]$Mode = "all"
)

Write-Host "🧪 Aconex RAG - Test Runner" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "tests")) {
    Write-Host "❌ Error: Directorio 'tests' no encontrado" -ForegroundColor Red
    Write-Host "   Asegúrate de ejecutar este script desde backend-acorag/" -ForegroundColor Yellow
    exit 1
}

# Verificar que pytest está instalado
try {
    $null = & python -m pytest --version 2>&1
} catch {
    Write-Host "❌ Error: pytest no está instalado" -ForegroundColor Red
    Write-Host "   Instala con: pip install -r requirements-test.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 Modo de ejecución: $Mode" -ForegroundColor Green
Write-Host ""

# Ejecutar según el modo
switch ($Mode) {
    "all" {
        Write-Host "▶️  Ejecutando todos los tests..." -ForegroundColor Blue
        & python -m pytest tests/ -v --tb=short
    }
    
    "cov" {
        Write-Host "▶️  Ejecutando tests con cobertura..." -ForegroundColor Blue
        & python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -v
        Write-Host ""
        Write-Host "📊 Reporte de cobertura generado en: htmlcov/index.html" -ForegroundColor Green
        
        # Preguntar si abrir el reporte
        $response = Read-Host "¿Abrir reporte en navegador? (s/n)"
        if ($response -eq "s" -or $response -eq "S") {
            Start-Process "htmlcov\index.html"
        }
    }
    
    "unit" {
        Write-Host "▶️  Ejecutando tests unitarios..." -ForegroundColor Blue
        & python -m pytest tests/ -m "unit" -v
    }
    
    "integration" {
        Write-Host "▶️  Ejecutando tests de integración..." -ForegroundColor Blue
        & python -m pytest tests/ -m "integration" -v
    }
    
    "api" {
        Write-Host "▶️  Ejecutando tests de API..." -ForegroundColor Blue
        & python -m pytest tests/ -m "api" -v
    }
    
    "fast" {
        Write-Host "▶️  Ejecutando tests en paralelo..." -ForegroundColor Blue
        & python -m pytest tests/ -n auto -v
    }
    
    "watch" {
        Write-Host "▶️  Modo watch activado (Ctrl+C para salir)..." -ForegroundColor Blue
        Write-Host "   Esperando cambios en archivos..." -ForegroundColor Gray
        
        # Usar pytest-watch si está disponible
        try {
            & python -m ptw tests/ -- -v
        } catch {
            Write-Host "❌ pytest-watch no instalado" -ForegroundColor Red
            Write-Host "   Instala con: pip install pytest-watch" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "   Alternativa: ejecutar manualmente después de cada cambio" -ForegroundColor Gray
        }
    }
    
    "quick" {
        Write-Host "▶️  Tests rápidos (solo unitarios, sin slow)..." -ForegroundColor Blue
        & python -m pytest tests/ -m "unit and not slow" -v --tb=short
    }
    
    "failing" {
        Write-Host "▶️  Re-ejecutando tests que fallaron..." -ForegroundColor Blue
        & python -m pytest tests/ --lf -v
    }
    
    "new" {
        Write-Host "▶️  Ejecutando solo tests nuevos o modificados..." -ForegroundColor Blue
        & python -m pytest tests/ --nf -v
    }
    
    default {
        Write-Host "❌ Modo desconocido: $Mode" -ForegroundColor Red
        Write-Host ""
        Write-Host "Opciones disponibles:" -ForegroundColor Yellow
        Write-Host "  all         - Todos los tests" -ForegroundColor Gray
        Write-Host "  cov         - Con cobertura" -ForegroundColor Gray
        Write-Host "  unit        - Solo unitarios" -ForegroundColor Gray
        Write-Host "  integration - Solo integración" -ForegroundColor Gray
        Write-Host "  api         - Solo API" -ForegroundColor Gray
        Write-Host "  fast        - Paralelo (rápido)" -ForegroundColor Gray
        Write-Host "  quick       - Rápidos sin slow" -ForegroundColor Gray
        Write-Host "  failing     - Re-ejecutar fallidos" -ForegroundColor Gray
        Write-Host "  watch       - Modo watch" -ForegroundColor Gray
        exit 1
    }
}

# Capturar el código de salida
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ Todos los tests pasaron!" -ForegroundColor Green
} else {
    Write-Host "❌ Algunos tests fallaron" -ForegroundColor Red
}

Write-Host ""
exit $exitCode
