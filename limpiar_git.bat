@echo off
echo =====================================================
echo LIMPIANDO ARCHIVO GRANDE DEL REPOSITORIO
echo =====================================================
echo.

echo [1/4] Eliminando archivo del staging area...
git rm --cached datos_backup.sql 2>nul
if exist datos_backup.sql (
    git rm --cached datos_backup.sql -f 2>nul
)

echo.
echo [2/4] Agregando .gitignore actualizado...
git add .gitignore

echo.
echo [3/4] Verificando archivos preparados para commit...
git status

echo.
echo [4/4] Listo para commit limpio
echo.
echo =====================================================
echo SIGUIENTE PASO:
echo =====================================================
echo Ejecuta estos comandos:
echo.
echo git commit -m "fix: remover archivo SQL grande del repositorio"
echo git push
echo.
pause
