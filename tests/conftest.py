"""
Configuración y fixtures compartidas para todos los tests
"""
import os
import sys
import pytest
import json
import tempfile
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from typing import Dict, Any, List

# Añadir el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ============================================================================
# FIXTURES DE CONFIGURACIÓN
# ============================================================================

@pytest.fixture(scope="session")
def test_env_vars():
    """Configura variables de entorno para tests"""
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/testdb"
    os.environ["EMBEDDING_MODEL"] = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    os.environ["GROQ_API_KEY"] = "test_groq_key_12345"
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_jwt_testing_only"
    os.environ["CHUNK_SIZE"] = "1000"
    os.environ["CHUNK_OVERLAP"] = "200"
    yield
    # Cleanup después de todos los tests
    for key in ["DATABASE_URL", "EMBEDDING_MODEL", "GROQ_API_KEY", "JWT_SECRET_KEY"]:
        os.environ.pop(key, None)


# ============================================================================
# FIXTURES DE BASE DE DATOS
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """Mock de conexión a PostgreSQL"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Configurar comportamiento del cursor
    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    
    # Attach mock_cursor as an attribute for easy access in tests
    mock_conn.mock_cursor = mock_cursor
    
    return mock_conn


@pytest.fixture
def mock_db_rows():
    """Datos de prueba que simularían retornarse de la BD"""
    return [
        {
            "document_id": "DOC-001",
            "project_id": "PROJ-A",
            "title": "Plano de Arquitectura Principal",
            "number": "PA-001",
            "category": "Arquitectura",
            "doc_type": "Plano",
            "revision": "Rev 3",
            "filename": "plano_arquitectura.pdf",
            "file_type": "pdf",
            "date_modified": datetime(2024, 1, 15),
            "snippet": "Este plano muestra la distribución general del edificio...",
            "vector_score": 0.85,
            "text_score": 0.75,
            "score": 0.82
        },
        {
            "document_id": "DOC-002",
            "project_id": "PROJ-A",
            "title": "Cronograma de Obra",
            "number": "CR-002",
            "category": "Planificación",
            "doc_type": "Cronograma",
            "revision": "Rev 1",
            "filename": "cronograma.pdf",
            "file_type": "pdf",
            "date_modified": datetime(2024, 1, 20),
            "snippet": "Cronograma detallado de actividades de construcción...",
            "vector_score": 0.78,
            "text_score": 0.65,
            "score": 0.73
        }
    ]


# ============================================================================
# FIXTURES DE MODELOS DE EMBEDDINGS
# ============================================================================

@pytest.fixture
def mock_sentence_transformer():
    """Mock del modelo SentenceTransformer"""
    mock_model = MagicMock()
    
    # Simular embeddings normalizados de 768 dimensiones (compatible con BD)
    def mock_encode(texts, normalize_embeddings=True, convert_to_numpy=True):
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        # Generar vectores aleatorios normalizados de 768 dims
        embeddings = np.random.rand(len(texts), 768).astype(np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms
        # Si era un string único, retornar array 1D
        if is_single:
            return embeddings[0]
        return embeddings
    
    mock_model.encode.side_effect = mock_encode
    mock_model.get_sentence_embedding_dimension.return_value = 768
    
    return mock_model


@pytest.fixture
def mock_model_loader(mock_sentence_transformer):
    """Patchea la carga del modelo en todos los módulos"""
    with patch('app.ingest.SentenceTransformer', return_value=mock_sentence_transformer), \
         patch('app.search_core.SentenceTransformer', return_value=mock_sentence_transformer), \
         patch('app.upload.SentenceTransformer', return_value=mock_sentence_transformer):
        yield mock_sentence_transformer


# ============================================================================
# FIXTURES DE DATOS DE PRUEBA
# ============================================================================

@pytest.fixture
def sample_aconex_document():
    """Documento Aconex completo de ejemplo"""
    return {
        "DocumentId": "200076-CCC02-PL-AR-000400",
        "project_id": "PROJ-TEST-001",
        "metadata": {
            "Title": "Plan Maestro de Arquitectura",
            "DocumentNumber": "200076-CCC02-PL-AR-000400",
            "Category": "Arquitectura",
            "DocumentType": "Plano",
            "DocumentStatus": "Aprobado",
            "ReviewStatus": "Revisado",
            "Revision": "Rev 3",
            "Filename": "plan_maestro_arquitectura.pdf",
            "FileType": "pdf",
            "FileSize": "2548736",
            "DateModified": "2024-01-15T10:30:00Z",
            "SelectList2": "PROYECTO-EDUCATIVO-001",
            "SelectList7": "Fase 1"
        },
        "full_text": """Plan Maestro de Arquitectura - Edificio Educativo
        
Este documento presenta el diseño arquitectónico integral del proyecto educativo.
El edificio contará con 24 aulas distribuidas en 3 niveles, con áreas comunes que
incluyen biblioteca, laboratorios, cafetería y espacios recreativos.

Especificaciones técnicas:
- Estructura sismo-resistente según NSR-10
- Columnas de concreto reforzado F'c=280 kg/cm²
- Sistema de ventilación natural cruzada
- Captación de aguas lluvias para riego

Área total construida: 4,500 m²
Área de circulación: 800 m²
Área verde: 1,200 m²
"""
    }


@pytest.fixture
def sample_aconex_document_minimal():
    """Documento Aconex con campos mínimos"""
    return {
        "DocumentId": "MIN-001",
        "metadata": {
            "Title": "Documento Mínimo",
            "DocumentNumber": "MIN-001"
        }
    }


@pytest.fixture
def sample_json_file(tmp_path):
    """Crea un archivo JSON temporal para tests"""
    def _create_json(data, filename="test.json"):
        file_path = tmp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(file_path)
    return _create_json


@pytest.fixture
def sample_ndjson_file(tmp_path):
    """Crea un archivo NDJSON temporal para tests"""
    def _create_ndjson(data_list, filename="test.ndjson"):
        file_path = tmp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            for obj in data_list:
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
        return str(file_path)
    return _create_ndjson


@pytest.fixture
def sample_text_chunks():
    """Chunks de texto de ejemplo"""
    return [
        "Este es el primer chunk de texto que contiene información sobre arquitectura.",
        "El segundo chunk habla sobre especificaciones técnicas y materiales de construcción.",
        "El tercer chunk describe el cronograma y fases del proyecto de construcción."
    ]


# ============================================================================
# FIXTURES DE API (FastAPI)
# ============================================================================

@pytest.fixture
async def test_client():
    """Cliente de prueba async para FastAPI"""
    from httpx import AsyncClient, ASGITransport
    from app.api import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Headers de autenticación para tests de API"""
    # Token JWT de prueba (mock)
    return {
        "Authorization": "Bearer test_jwt_token_123456"
    }


@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }


# ============================================================================
# FIXTURES DE ARCHIVOS
# ============================================================================

@pytest.fixture
def sample_pdf_content():
    """Contenido simulado de un PDF"""
    return b"%PDF-1.4\n%Mock PDF content for testing\nTest PDF document content here"


@pytest.fixture
def sample_txt_file(tmp_path):
    """Crea un archivo TXT temporal"""
    def _create_txt(content, filename="test.txt"):
        file_path = tmp_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)
    return _create_txt


@pytest.fixture
def sample_large_text():
    """Texto largo para tests de chunking"""
    return " ".join([f"Palabra{i}" for i in range(2000)])


# ============================================================================
# FIXTURES DE UTILIDADES
# ============================================================================

@pytest.fixture
def mock_datetime():
    """Mock de datetime para tests deterministas"""
    mock_dt = datetime(2024, 1, 15, 10, 30, 0)
    with patch('app.ingest.datetime') as mock:
        mock.now.return_value = mock_dt
        mock.fromisoformat = datetime.fromisoformat
        yield mock


@pytest.fixture
def capture_logs(caplog):
    """Captura logs durante los tests"""
    import logging
    caplog.set_level(logging.INFO)
    return caplog


# ============================================================================
# FIXTURES DE LIMPIEZA
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Resetea singletons globales entre tests"""
    # Resetear el modelo cargado en search_core
    import app.search_core as search_core
    search_core._model = None
    yield


# ============================================================================
# HELPERS DE TESTING
# ============================================================================

def assert_valid_embedding(embedding: List[float], expected_dim: int = 384):
    """Verifica que un embedding sea válido"""
    assert len(embedding) == expected_dim, f"Dimensión incorrecta: {len(embedding)} != {expected_dim}"
    # Verificar que está normalizado (norma L2 ≈ 1)
    norm = np.linalg.norm(embedding)
    assert 0.99 < norm < 1.01, f"Embedding no normalizado: norma = {norm}"


def assert_valid_document(doc: Dict[str, Any]):
    """Verifica que un documento tenga la estructura correcta"""
    required_fields = ["document_id", "project_id", "title", "body_text"]
    for field in required_fields:
        assert field in doc, f"Campo requerido faltante: {field}"
    assert len(doc["document_id"]) > 0, "document_id vacío"
    assert len(doc["body_text"]) > 0, "body_text vacío"


def assert_valid_search_result(result: Dict[str, Any]):
    """Verifica que un resultado de búsqueda sea válido"""
    required_fields = ["document_id", "title", "score"]
    for field in required_fields:
        assert field in result, f"Campo requerido faltante: {field}"
    assert 0 <= result["score"] <= 1, f"Score fuera de rango: {result['score']}"
