# =====================================================
# SOLUCIÓN PASO A PASO - ARCHIVO SQL DEMASIADO GRANDE
# =====================================================

## Problema:
# El archivo datos_backup.sql (1.3 GB) excede el límite de GitHub (100 MB)

## Solución:

### PASO 1: Deshacer el último commit (SIN perder cambios)
```powershell
git reset --soft HEAD~1
```
Esto deshace el commit pero mantiene tus cambios

### PASO 2: Remover el archivo SQL del staging
```powershell
git rm --cached datos_backup.sql
```
Si da error, intenta:
```powershell
git reset HEAD datos_backup.sql
```

### PASO 3: Agregar archivos correctos (sin el SQL)
```powershell
git add .gitignore
git add app/ingest.py
git add optimize_metadata_only.py
git add run_optimization.py
git add OPTIMIZACION_SIN_PDFS.md
```

### PASO 4: Verificar qué se va a commitear
```powershell
git status
```
**Asegúrate de que datos_backup.sql NO aparezca en verde**

### PASO 5: Hacer commit limpio
```powershell
git commit -m "feat: optimización máxima sin PDFs - modelo español + metadatos enriquecidos"
```

### PASO 6: Push limpio
```powershell
git push
```

---

## Si el archivo YA está en el historial de Git:

Si ya lo habías subido antes y sigue dando error, necesitas limpiarlo del historial:

```powershell
# Opción A: BFG (recomendado para archivos grandes)
# Descarga BFG desde: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files datos_backup.sql

# Opción B: git filter-branch (nativo pero más lento)
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch datos_backup.sql" --prune-empty --tag-name-filter cat -- --all
```

Luego:
```powershell
git push origin --force --all
```

⚠️ **ADVERTENCIA**: Esto reescribe el historial. Si trabajas en equipo, coordina primero.

---

## Alternativa: Mover archivo grande a otro lugar

Si necesitas conservar el backup:

```powershell
# Mover fuera del repositorio
move datos_backup.sql C:\Users\luisc\Desktop\backups\

# Luego continuar con los pasos 1-6
```

---

## Prevenir en el futuro:

El archivo .gitignore ya está actualizado para ignorar *.sql

Verifica siempre antes de commit:
```powershell
git status
```

Si ves archivos grandes, no los agregues:
```powershell
git reset HEAD archivo_grande.sql
```
