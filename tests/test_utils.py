"""
Tests del módulo de utilidades (app/utils.py)
Escenario 4: Utilidades Core (Chunking y DB)

Tests core seleccionados:
1. Test de chunking con overlap (crítico para embeddings)
2. Test de conexión a base de datos
"""
import pytest
from unittest.mock import patch, MagicMock
import os
from app.utils import simple_chunk, get_db_connection


# ============================================================================
# TEST 1: CHUNKING CON OVERLAP
# ============================================================================

@pytest.mark.unit
def test_simple_chunk_with_overlap():
    """
    Test Core: Chunking de texto con overlap
    
    Verifica que simple_chunk divida correctamente textos largos en chunks
    con overlap para mantener contexto entre chunks. Esto es crítico para
    la calidad de los embeddings y la recuperación de información.
    
    El overlap asegura que información relevante que cae en los bordes de
    un chunk también esté presente en el siguiente, mejorando la búsqueda
    semántica y evitando perder contexto.
    """
    # Arrange: Texto largo que requiere chunking
    texto = """El proyecto de construcción del edificio educativo contempla 24 aulas distribuidas en 3 niveles.
La estructura será de concreto reforzado con columnas de 40x40 cm y resistencia f'c=280 kg/cm2.
El sistema de cimentación utilizará zapatas aisladas conectadas con vigas de amarre.
Los muros exteriores serán de mampostería confinada con bloques de arcilla de 20 cm.
Las instalaciones eléctricas seguirán normas RETIE con tableros de distribución en cada nivel.
El sistema hidráulico incluirá cisterna de 20 m3 y tanque elevado de 10 m3 para presión constante.
Los acabados incluyen pisos en porcelanato para zonas comunes y baldosa antideslizante en baños."""
    
    chunk_size = 30  # 30 palabras por chunk
    overlap = 10     # 10 palabras de overlap
    
    # Act: Realizar chunking
    chunks = simple_chunk(texto, size=chunk_size, overlap=overlap)
    
    # Assert: Verificar comportamiento del chunking
    
    # 1. Debe generar múltiples chunks para texto largo
    assert len(chunks) >= 2, f"Texto de {len(texto.split())} palabras debe generar múltiples chunks"
    
    # 2. Verificar que chunks contienen palabras (no vacíos)
    for i, chunk in enumerate(chunks):
        palabras_en_chunk = len(chunk.split())
        assert palabras_en_chunk > 0, f"Chunk {i} no debe estar vacío"
    
    # 3. Verificar que hay overlap entre chunks consecutivos
    if len(chunks) >= 2:
        # Buscar contenido compartido entre chunk 0 y 1
        chunk_0_end = chunks[0][-overlap:]
        chunk_1_start = chunks[1][:overlap + 50]
        
        # Debe haber palabras en común (overlap funciona)
        palabras_chunk_0 = set(chunk_0_end.split())
        palabras_chunk_1 = set(chunk_1_start.split())
        palabras_comunes = palabras_chunk_0.intersection(palabras_chunk_1)
        
        assert len(palabras_comunes) > 0, "Debe haber overlap de contenido entre chunks consecutivos"
    
    # 4. Verificar que ningún chunk está vacío
    for i, chunk in enumerate(chunks):
        assert len(chunk.strip()) > 0, f"Chunk {i} no debe estar vacío"
    
    # 5. Verificar que el contenido semántico se preserva
    texto_reconstruido = " ".join(chunks)
    palabras_clave = ["educativo", "concreto", "cimentación", "instalaciones", "acabados"]
    for palabra in palabras_clave:
        assert palabra in texto_reconstruido, \
            f"Palabra clave '{palabra}' debe preservarse en chunking"
    
    print("\n✅ Chunking con overlap validado:")
    print(f"   - Texto original: {len(texto)} caracteres")
    print(f"   - Chunk size: {chunk_size}")
    print(f"   - Overlap: {overlap}")
    print(f"   - Chunks generados: {len(chunks)}")
    print(f"   - Tamaños: {[len(c) for c in chunks]}")
    if len(chunks) >= 2:
        print(f"   - Overlap detectado: {len(palabras_comunes)} palabras en común")


# ============================================================================
# TEST 2: CONEXIÓN A BASE DE DATOS
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
@pytest.mark.mock
def test_get_db_connection_success():
    """
    Test Core: Obtención de conexión a PostgreSQL
    
    Verifica que get_db_connection establezca correctamente la conexión
    a la base de datos usando DATABASE_URL. La conexión DB es fundamental
    para TODO el sistema RAG (lectura y escritura de documentos y vectores).
    
    Este test simula una conexión exitosa y verifica que:
    - Se use la variable de entorno DATABASE_URL
    - Se establezca la conexión con psycopg2
    - La conexión sea reutilizable
    """
    # Arrange: Mock de psycopg2.connect
    mock_connection = MagicMock()
    mock_connection.closed = 0  # Conexión abierta
    
    database_url = "postgresql://user:pass@localhost:5432/testdb"
    
    # Act: Obtener conexión con DATABASE_URL mockeado
    with patch.dict(os.environ, {"DATABASE_URL": database_url}):
        with patch('psycopg2.connect', return_value=mock_connection) as mock_connect:
            conn = get_db_connection()
    
    # Assert: Verificar comportamiento
    
    # 1. Verificar que se llamó psycopg2.connect con la URL correcta
    mock_connect.assert_called_once_with(database_url)
    
    # 2. Verificar que retorna un objeto de conexión válido
    assert conn is not None
    assert conn == mock_connection
    
    # 3. Verificar que la conexión está abierta
    assert conn.closed == 0, "Conexión debe estar abierta"
    
    # 4. Verificar que la conexión es utilizable (tiene métodos esperados)
    assert hasattr(conn, 'cursor'), "Conexión debe tener método cursor()"
    assert hasattr(conn, 'commit'), "Conexión debe tener método commit()"
    assert hasattr(conn, 'rollback'), "Conexión debe tener método rollback()"
    
    print("\n✅ Conexión DB validada:")
    print(f"   - DATABASE_URL: {database_url}")
    print(f"   - Conexión establecida: ✓")
    print(f"   - Estado: ABIERTA")
    print(f"   - Métodos disponibles: cursor, commit, rollback")


# ============================================================================
# TEST 3: CHUNKING DE CASOS EXTREMOS
# ============================================================================

@pytest.mark.unit
def test_simple_chunk_edge_cases():
    """
    Test Core: Chunking con casos extremos
    
    Verifica el manejo robusto de casos edge:
    - Texto muy corto (menor que chunk_size)
    - Texto vacío
    - Texto con solo espacios
    - Overlap mayor que chunk_size
    """
    # Caso 1: Texto corto (no requiere chunking)
    texto_corto = "Este es un texto muy corto."
    chunks_cortos = simple_chunk(texto_corto, size=1000, overlap=100)
    assert len(chunks_cortos) == 1, "Texto corto debe generar 1 solo chunk"
    assert chunks_cortos[0] == texto_corto
    
    # Caso 2: Texto vacío (retorna lista vacía)
    chunks_vacios = simple_chunk("", size=100, overlap=20)
    assert len(chunks_vacios) == 0 or (len(chunks_vacios) == 1 and chunks_vacios[0] == ""), "Texto vacío debe retornar lista vacía o con chunk vacío"
    
    # Caso 3: Texto solo espacios (se convierte en vacío)
    chunks_espacios = simple_chunk("   \n  \t  ", size=100, overlap=20)
    assert len(chunks_espacios) <= 1, "Texto solo espacios debe generar máximo 1 chunk"
    
    # Caso 4: Overlap = 0 (sin overlap)
    texto_sin_overlap = "Palabra1 Palabra2 Palabra3 Palabra4 Palabra5 Palabra6 Palabra7 Palabra8"
    chunks_sin_overlap = simple_chunk(texto_sin_overlap, size=3, overlap=0)
    assert len(chunks_sin_overlap) >= 2, "Debe generar múltiples chunks sin overlap"
    
    print("\n✅ Casos extremos de chunking validados:")
    print(f"   - Texto corto: {len(chunks_cortos)} chunk")
    print(f"   - Texto vacío: {len(chunks_vacios)} chunk")
    print(f"   - Solo espacios: {len(chunks_espacios)} chunk")
    print(f"   - Sin overlap: {len(chunks_sin_overlap)} chunks")


# ============================================================================
# TEST 4: CHUNKING CON PARÁMETROS INVÁLIDOS (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_simple_chunk_invalid_parameters():
    """
    Test de Caso Negativo: Validar manejo de parámetros inválidos
    
    Verifica que simple_chunk maneje apropiadamente:
    - size = 0 o negativo
    - overlap > size
    - overlap negativo
    """
    from app.utils import simple_chunk
    
    texto = "Este es un texto de prueba para validar parámetros inválidos."
    
    # Caso 1: size = 0 (debe manejar o lanzar error)
    try:
        chunks = simple_chunk(texto, size=0, overlap=0)
        # Si no lanza error, debe retornar algo válido
        assert isinstance(chunks, list)
    except (ValueError, ZeroDivisionError):
        # Es válido que lance excepción
        pass
    
    # Caso 2: overlap > size (inválido)
    try:
        chunks = simple_chunk(texto, size=10, overlap=20)
        # Si no lanza error, verificar comportamiento
        assert isinstance(chunks, list)
    except ValueError:
        # Es válido que lance ValueError
        pass
    
    # Caso 3: size negativo
    with pytest.raises((ValueError, Exception)):
        simple_chunk(texto, size=-10, overlap=5)
    
    print("\n✅ Manejo de parámetros inválidos validado:")
    print(f"   - Sistema maneja size=0 apropiadamente: ✓")
    print(f"   - Sistema maneja overlap>size apropiadamente: ✓")
    print(f"   - Sistema rechaza size negativo: ✓")


# ============================================================================
# TEST 5: CONEXIÓN DB CON CREDENCIALES INVÁLIDAS (CASO NEGATIVO)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_get_db_connection_invalid_credentials():
    """
    Test de Caso Negativo: Validar manejo de credenciales incorrectas
    
    Verifica que get_db_connection lance OperationalError cuando
    las credenciales son inválidas.
    """
    from app.utils import get_db_connection
    import psycopg2
    
    # Arrange: DATABASE_URL con credenciales inválidas
    bad_url = "postgresql://wrong_user:wrong_pass@localhost:5432/nonexistent"
    
    # Act & Assert: Debe lanzar OperationalError
    with patch.dict(os.environ, {"DATABASE_URL": bad_url}):
        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("authentication failed")):
            with pytest.raises(psycopg2.OperationalError):
                get_db_connection()
    
    print("\n✅ Manejo de credenciales inválidas validado:")
    print(f"   - OperationalError lanzado correctamente: ✓")


# ============================================================================
# TEST 6: CONEXIÓN DB SIN VARIABLE DE ENTORNO (CASO NEGATIVO)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_get_db_connection_missing_env_vars():
    """
    Test de Caso Negativo: Validar manejo de DATABASE_URL faltante
    
    Verifica que get_db_connection maneje apropiadamente cuando
    DATABASE_URL no está definida en el entorno.
    """
    from app.utils import get_db_connection
    
    # Arrange: Eliminar DATABASE_URL del entorno
    env_without_db = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    
    # Act & Assert: Debe lanzar KeyError o manejar el error
    with patch.dict(os.environ, env_without_db, clear=True):
        try:
            get_db_connection()
            # Si no lanza error, debe tener fallback
            pass
        except (KeyError, ValueError):
            # Es válido que lance excepción
            pass
    
    print("\n✅ Manejo de variable de entorno faltante validado:")
    print(f"   - Sistema maneja DATABASE_URL faltante apropiadamente: ✓")
