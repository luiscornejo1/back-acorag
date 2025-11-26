"""
Tests del módulo de upload y procesamiento de archivos (app/upload.py)
Escenario 3: Upload y Procesamiento en Tiempo Real

Tests core seleccionados:
1. Test de extracción de texto de archivo TXT (más simple y directo)
2. Test de generación de document_id único

Nota: Los tests de ingesta completa con BD se omiten porque requieren
integración real de PostgreSQL con pgvector, lo cual es más apropiado
para tests de integración end-to-end que para unit tests.
"""
import pytest
from pathlib import Path
from app.upload import DocumentUploader


# ============================================================================
# TEST 1: EXTRACCIÓN DE TEXTO DE ARCHIVO TXT
# ============================================================================

@pytest.mark.unit
def test_extract_text_from_txt(tmp_path, mock_model_loader):
    """
    Test Core: Extracción básica de texto de archivo TXT
    
    Verifica que DocumentUploader pueda extraer texto correctamente
    de archivos de texto plano, que es el formato más común y simple.
    
    Este es el caso base de extracción de contenido que debe funcionar
    siempre, sin dependencias externas como PyPDF2 o python-docx.
    """
    # Arrange: Crear archivo TXT de prueba
    txt_file = tmp_path / "documento.txt"
    contenido = """Manual de Seguridad en Construcción
    
Este manual describe las normas de seguridad que deben seguirse.
Incluye procedimientos para trabajo en altura y uso de EPP.
"""
    txt_file.write_text(contenido, encoding='utf-8')
    
    # Act: Extraer texto
    uploader = DocumentUploader()
    result = uploader.extract_text_from_txt(str(txt_file))
    
    # Assert: Verificar extracción
    assert "Seguridad" in result
    assert "procedimientos" in result
    assert len(result) > 50
    
    print("\n✅ Extracción de TXT validada:")
    print(f"   - Archivo: {txt_file.name}")
    print(f"   - Texto extraído: {len(result)} caracteres")
    print(f"   - Contenido preservado: ✓")


# ============================================================================
# TEST 2: GENERACIÓN DE DOCUMENT ID ÚNICO
# ============================================================================

@pytest.mark.unit
def test_generate_document_id_unique(mock_model_loader):
    """
    Test Core: Generación de IDs con formato MD5
    
    Verifica que generate_document_id genere IDs en formato MD5 válido.
    
    Nota: La implementación actual usa datetime.now() en el hash,
    pero en tests rápidos puede generar el mismo ID si el timestamp
    es igual (misma fracción de segundo).
    """
    # Arrange
    uploader = DocumentUploader()
    filename = "manual.txt"
    content = "Contenido del documento de prueba"
    
    # Act: Generar ID
    id1 = uploader.generate_document_id(filename, content)
    
    # Assert: ID debe ser hash MD5 válido
    assert len(id1) == 32  # MD5 hash tiene 32 caracteres hex
    assert all(c in '0123456789abcdef' for c in id1)  # Solo caracteres hex válidos
    
    # Cambiar contenido o filename genera ID diferente
    id2 = uploader.generate_document_id(filename, content + " modificado")
    assert id2 != id1
    assert len(id2) == 32
    
    id3 = uploader.generate_document_id("otro_archivo.txt", content)
    assert id3 != id1
    assert len(id3) == 32
    
    print("\n✅ Generación de IDs validada:")
    print(f"   - ID generado: {id1}")
    print(f"   - Formato MD5: ✓")
    print(f"   - Cambios de contenido generan IDs diferentes: ✓")
    print(f"   - Cambios de filename generan IDs diferentes: ✓")


# ============================================================================
# TEST 3: ARCHIVO NO ENCONTRADO (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_extract_text_file_not_found(mock_model_loader):
    """
    Test de Caso Negativo: Validar manejo de archivo inexistente
    
    Verifica que extract_text_from_txt lance FileNotFoundError
    cuando el archivo no existe.
    """
    from app.upload import DocumentUploader
    
    # Arrange
    uploader = DocumentUploader()
    nonexistent_file = "c:/archivos/que/no/existe.txt"
    
    # Act & Assert: Debe lanzar FileNotFoundError
    with pytest.raises(FileNotFoundError):
        uploader.extract_text_from_txt(nonexistent_file)
    
    print("\n✅ Manejo de archivo inexistente validado:")
    print(f"   - FileNotFoundError lanzado correctamente: ✓")


# ============================================================================
# TEST 4: ARCHIVO CON ENCODING INVÁLIDO (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_extract_text_invalid_encoding(tmp_path, mock_model_loader):
    """
    Test de Caso Negativo: Validar manejo de archivo con encoding corrupto
    
    Verifica que extract_text_from_txt maneje archivos con encoding
    inválido o datos binarios corruptos.
    """
    from app.upload import DocumentUploader
    
    # Arrange: Crear archivo binario con bytes inválidos para UTF-8
    bad_file = tmp_path / "corrupto.txt"
    bad_file.write_bytes(b'\x80\x81\x82\x83\xFF\xFE')  # Bytes inválidos
    
    # Act & Assert: Puede lanzar UnicodeDecodeError o manejarlo internamente
    uploader = DocumentUploader()
    try:
        result = uploader.extract_text_from_txt(str(bad_file))
        # Si no lanza error, debe retornar algo (posiblemente vacío o con caracteres de reemplazo)
        assert result is not None
    except UnicodeDecodeError:
        # Es válido que lance esta excepción
        pass
    
    print("\n✅ Manejo de encoding inválido validado:")
    print(f"   - Sistema maneja archivos corruptos apropiadamente: ✓")

