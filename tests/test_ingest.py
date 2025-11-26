"""
Tests del módulo de ingesta de documentos (app/ingest.py)
Escenario 1: Ingesta y Normalización de Documentos

Tests core seleccionados:
1. Test de normalización completa de documento Aconex
2. Test de lectura de archivos JSON/NDJSON
"""
import pytest
from datetime import datetime
import json
from app.ingest import (
    normalize_doc,
    iter_docs_from_file
)


# ============================================================================
# TEST 1: NORMALIZACIÓN COMPLETA DE DOCUMENTO ACONEX
# ============================================================================

@pytest.mark.unit
def test_normalize_doc_complete(sample_aconex_document):
    """
    Test Core: Normalización completa de documento Aconex
    
    Verifica que normalize_doc procese correctamente un documento completo
    con todos sus metadatos, priorice el full_text cuando existe, y construya
    correctamente el body_text para embeddings.
    
    Este es el proceso más crítico de la ingesta porque determina cómo
    se indexarán los documentos para búsqueda semántica.
    """
    # Act: Normalizar documento con proyecto por defecto
    result = normalize_doc(sample_aconex_document, "DEFAULT-PROJ")
    
    # Assert: Verificar extracción correcta de metadatos
    assert result["document_id"] == "200076-CCC02-PL-AR-000400"
    assert result["title"] == "Plan Maestro de Arquitectura"
    assert result["number"] == "200076-CCC02-PL-AR-000400"
    assert result["category"] == "Arquitectura"
    assert result["doc_type"] == "Plano"
    assert result["status"] == "Aprobado"
    assert result["review_status"] == "Revisado"
    assert result["revision"] == "Rev 3"
    assert result["filename"] == "plan_maestro_arquitectura.pdf"
    assert result["file_type"] == "pdf"
    assert result["file_size"] == 2548736
    
    # Verificar que usa project_id de nivel superior (prioridad)
    assert result["project_id"] == "PROJ-TEST-001"
    
    # Verificar que el body_text contiene información semántica relevante
    assert "Plan Maestro de Arquitectura" in result["body_text"]
    assert "Edificio Educativo" in result["body_text"]
    assert "sismo-resistente" in result["body_text"]
    assert len(result["body_text"]) > 100
    
    # Verificar que date_modified se parsea correctamente
    assert isinstance(result["date_modified"], datetime)
    assert result["date_modified"].year == 2024
    assert result["date_modified"].month == 1
    assert result["date_modified"].day == 15
    
    print("\n✅ Test de Normalización Completa:")
    print(f"   - DocumentId: {result['document_id']}")
    print(f"   - Título: {result['title']}")
    print(f"   - Proyecto: {result['project_id']}")
    print(f"   - Body text length: {len(result['body_text'])} caracteres")


# ============================================================================
# TEST 2: LECTURA Y PARSEO DE DIFERENTES FORMATOS (JSON/NDJSON)
# ============================================================================

@pytest.mark.unit
def test_iter_docs_from_file_json_and_ndjson(tmp_path):
    """
    Test Core: Lectura flexible de formatos JSON y NDJSON
    
    Verifica que iter_docs_from_file maneje correctamente:
    - Archivos JSON con lista de documentos
    - Archivos NDJSON con un documento por línea
    - Manejo de líneas vacías
    
    Esto es crítico porque los documentos Aconex pueden venir en diferentes
    formatos según la fuente de extracción.
    """
    # Test 1: JSON con lista
    json_file = tmp_path / "docs_list.json"
    docs_list = [
        {"DocumentId": "001", "metadata": {"Title": "Doc 1"}},
        {"DocumentId": "002", "metadata": {"Title": "Doc 2"}}
    ]
    with open(json_file, 'w') as f:
        json.dump(docs_list, f)
    
    result_list = list(iter_docs_from_file(str(json_file)))
    assert len(result_list) == 2
    assert result_list[0]["DocumentId"] == "001"
    assert result_list[1]["DocumentId"] == "002"
    
    # Test 2: NDJSON (un documento por línea)
    ndjson_file = tmp_path / "docs.ndjson"
    with open(ndjson_file, 'w') as f:
        f.write('{"DocumentId": "003", "metadata": {"Title": "Doc 3"}}\n')
        f.write('\n')  # Línea vacía (debe ignorarse)
        f.write('{"DocumentId": "004", "metadata": {"Title": "Doc 4"}}\n')
    
    result_ndjson = list(iter_docs_from_file(str(ndjson_file)))
    assert len(result_ndjson) == 2
    assert result_ndjson[0]["DocumentId"] == "003"
    assert result_ndjson[1]["DocumentId"] == "004"
    
    print("\n✅ Lectura de formatos validada:")
    print(f"   - JSON lista: {len(result_list)} documentos")
    print(f"   - NDJSON: {len(result_ndjson)} documentos")
    print(f"   - Líneas vacías ignoradas correctamente")


# ============================================================================
# TEST 3: NORMALIZACIÓN CON CAMPOS FALTANTES (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_normalize_doc_missing_fields():
    """
    Test de Caso Negativo: Validar que normalize_doc maneja documentos incompletos
    
    Verifica que la función NO falle cuando faltan campos opcionales,
    y que use valores por defecto apropiados.
    """
    from app.ingest import normalize_doc
    
    # Arrange: Documento con campos mínimos (falta metadata opcional)
    incomplete_doc = {
        "project_id": "PROYECTO-001",
        "subject": "Documento sin metadata completa",
        # Faltan: body, from_company, to_company, date_sent, etc.
    }
    
    # Act: Normalizar documento incompleto
    result = normalize_doc(incomplete_doc)
    
    # Assert: NO debe lanzar error, debe usar defaults
    assert result is not None
    assert result["project_id"] == "PROYECTO-001"
    assert "subject" in result["body_text"] or result["body_text"] != ""
    
    # Campos faltantes deben tener valores por defecto
    assert "from_company" in result  # Puede ser None o ""
    assert "to_company" in result
    
    print("\n✅ Manejo de campos faltantes validado:")
    print(f"   - Documento procesado sin errores: ✓")
    print(f"   - Valores por defecto aplicados: ✓")


# ============================================================================
# TEST 4: ARCHIVO JSON MALFORMADO (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_iter_docs_invalid_json(tmp_path):
    """
    Test de Caso Negativo: Validar que iter_docs_from_file maneja JSON inválido
    
    Verifica que la función lance una excepción apropiada cuando
    el archivo JSON está malformado o corrupto.
    """
    from app.ingest import iter_docs_from_file
    
    # Arrange: Crear archivo JSON malformado
    bad_json_file = tmp_path / "malformed.json"
    bad_json_file.write_text('{"subject": "incomplete"', encoding='utf-8')  # JSON incompleto
    
    # Act & Assert: Debe lanzar excepción
    with pytest.raises(Exception):  # JSONDecodeError o similar
        list(iter_docs_from_file(str(bad_json_file)))
    
    print("\n✅ Manejo de JSON inválido validado:")
    print(f"   - Excepción lanzada correctamente: ✓")
    print(f"   - Sistema no crashea silenciosamente: ✓")
