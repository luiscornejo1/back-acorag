# Script de instalación de nuevas dependencias para la funcionalidad de upload
# Ejecuta esto en el backend

Write-Host "📦 Instalando dependencias para upload de documentos..." -ForegroundColor Cyan
Write-Host ""

# Activar entorno virtual si existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✓ Activando entorno virtual..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
}

# Instalar dependencias
Write-Host "📥 Instalando PyPDF2, python-docx y python-multipart..." -ForegroundColor Yellow
pip install PyPDF2==3.0.1 python-docx==1.1.0 python-multipart==0.0.6

Write-Host ""
Write-Host "✅ Instalación completada!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Para probar la funcionalidad:" -ForegroundColor Cyan
Write-Host "   1. Reinicia el servidor: uvicorn app.api:app --reload" -ForegroundColor White
Write-Host "   2. Ejecuta el test: python test_upload.py" -ForegroundColor White
Write-Host ""
