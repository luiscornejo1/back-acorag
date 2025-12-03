"""
Tests de performance y benchmark para el sistema RAG

Ejecutar con:
    pytest tests/test_performance.py -v --benchmark-only
    pytest tests/test_performance.py -v --benchmark-only --benchmark-verbose
    pytest tests/test_performance.py --benchmark-only --benchmark-save=baseline
"""

import pytest
import time
from app.search_core import semantic_search, encode_vec_str
from app.ingest import normalize_doc
from app.utils import simple_chunk
from app.upload import DocumentUploader


# ==============================================================================
# BENCHMARKS DE BÚSQUEDA
# ==============================================================================

@pytest.mark.benchmark(group="search")
def test_search_performance_basic(benchmark, mock_model_loader, mock_db_connection):
    """
    Benchmark: Búsqueda semántica básica
    
    Objetivo: < 500ms promedio
    """
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    mock_cursor.fetchall.return_value = [
        {
            "document_id": "DOC-001",
            "title": "Test Document",
            "snippet": "Test content",
            "score": 0.85
        }
    ]
    
    def search():
        from unittest.mock import patch
        with patch('app.search_core.get_conn', return_value=mock_db_connection):
            return semantic_search(
                query="construcción sismo resistente",
                project_id="PROJ-001",
                top_k=10
            )
    
    result = benchmark(search)
    
    assert len(result) > 0
    # Verificar que el tiempo promedio está dentro del objetivo
    assert benchmark.stats['mean'] < 0.5, f"Search too slow: {benchmark.stats['mean']:.3f}s"


@pytest.mark.benchmark(group="search")
def test_search_performance_large_result(benchmark, mock_model_loader, mock_db_connection):
    """
    Benchmark: Búsqueda con muchos resultados (top_k=50)
    
    Objetivo: < 800ms promedio
    """
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    # Simular 50 resultados
    mock_cursor.fetchall.return_value = [
        {
            "document_id": f"DOC-{i:03d}",
            "title": f"Document {i}",
            "snippet": f"Content {i}",
            "score": 0.9 - (i * 0.01)
        }
        for i in range(50)
    ]
    
    def search():
        from unittest.mock import patch
        with patch('app.search_core.get_conn', return_value=mock_db_connection):
            return semantic_search(
                query="test query",
                project_id=None,
                top_k=50
            )
    
    result = benchmark(search)
    
    assert len(result) == 50
    assert benchmark.stats['mean'] < 0.8, f"Large search too slow: {benchmark.stats['mean']:.3f}s"


# ==============================================================================
# BENCHMARKS DE INGESTA
# ==============================================================================

@pytest.mark.benchmark(group="ingest")
def test_normalize_doc_performance(benchmark, sample_aconex_document):
    """
    Benchmark: Normalización de documento
    
    Objetivo: < 10ms promedio
    """
    result = benchmark(normalize_doc, sample_aconex_document, "DEFAULT-PROJ")
    
    assert result is not None
    assert result["document_id"] is not None
    assert benchmark.stats['mean'] < 0.01, f"Normalization too slow: {benchmark.stats['mean']:.3f}s"


@pytest.mark.benchmark(group="ingest")
def test_normalize_batch_performance(benchmark, sample_aconex_document):
    """
    Benchmark: Normalización de batch de documentos (100 docs)
    
    Objetivo: < 1s para 100 documentos
    """
    def normalize_batch():
        results = []
        for i in range(100):
            doc = sample_aconex_document.copy()
            doc["DocumentId"] = f"DOC-{i:05d}"
            results.append(normalize_doc(doc, "DEFAULT-PROJ"))
        return results
    
    results = benchmark(normalize_batch)
    
    assert len(results) == 100
    rate = 100 / benchmark.stats['mean']
    print(f"\nNormalization rate: {rate:.2f} docs/second")
    assert benchmark.stats['mean'] < 1.0, f"Batch normalization too slow: {benchmark.stats['mean']:.3f}s"


# ==============================================================================
# BENCHMARKS DE CHUNKING
# ==============================================================================

@pytest.mark.benchmark(group="chunking")
def test_chunking_small_text(benchmark):
    """
    Benchmark: Chunking de texto pequeño (1000 palabras)
    
    Objetivo: < 50ms promedio
    """
    text = "palabra " * 1000
    
    result = benchmark(simple_chunk, text, size=100, overlap=20)
    
    assert len(result) > 0
    assert benchmark.stats['mean'] < 0.05, f"Small chunking too slow: {benchmark.stats['mean']:.3f}s"


@pytest.mark.benchmark(group="chunking")
def test_chunking_large_text(benchmark):
    """
    Benchmark: Chunking de texto grande (10,000 palabras)
    
    Objetivo: < 200ms promedio
    """
    text = "palabra " * 10000
    
    result = benchmark(simple_chunk, text, size=100, overlap=20)
    
    assert len(result) > 0
    rate = 10000 / benchmark.stats['mean']
    print(f"\nChunking rate: {rate:.2f} words/second")
    assert benchmark.stats['mean'] < 0.2, f"Large chunking too slow: {benchmark.stats['mean']:.3f}s"


@pytest.mark.benchmark(group="chunking")
def test_chunking_massive_text(benchmark):
    """
    Benchmark: Chunking de texto masivo (100,000 palabras)
    
    Objetivo: < 2s promedio
    """
    text = "palabra " * 100000
    
    result = benchmark(simple_chunk, text, size=100, overlap=20)
    
    assert len(result) > 0
    rate = 100000 / benchmark.stats['mean']
    print(f"\nMassive chunking rate: {rate:.2f} words/second")
    assert benchmark.stats['mean'] < 2.0, f"Massive chunking too slow: {benchmark.stats['mean']:.3f}s"


# ==============================================================================
# BENCHMARKS DE UPLOAD
# ==============================================================================

@pytest.mark.benchmark(group="upload")
def test_extract_text_performance(benchmark, tmp_path, mock_model_loader):
    """
    Benchmark: Extracción de texto de archivo TXT
    
    Objetivo: < 100ms promedio
    """
    # Crear archivo de prueba
    txt_file = tmp_path / "test.txt"
    content = "Línea de texto de prueba\n" * 1000
    txt_file.write_text(content, encoding='utf-8')
    
    uploader = DocumentUploader()
    
    result = benchmark(uploader.extract_text_from_txt, str(txt_file))
    
    assert len(result) > 0
    assert benchmark.stats['mean'] < 0.1, f"Text extraction too slow: {benchmark.stats['mean']:.3f}s"


@pytest.mark.benchmark(group="upload")
def test_generate_document_id_performance(benchmark, mock_model_loader):
    """
    Benchmark: Generación de document IDs
    
    Objetivo: < 1ms promedio
    """
    uploader = DocumentUploader()
    
    result = benchmark(
        uploader.generate_document_id,
        "test_file.txt",
        "contenido de prueba"
    )
    
    assert len(result) == 32  # MD5 hash
    assert benchmark.stats['mean'] < 0.001, f"ID generation too slow: {benchmark.stats['mean']:.3f}s"


# ==============================================================================
# BENCHMARKS DE ENCODING
# ==============================================================================

@pytest.mark.benchmark(group="encoding")
def test_vector_encoding_performance(benchmark):
    """
    Benchmark: Encoding de vector a string PostgreSQL
    
    Objetivo: < 1ms promedio
    """
    import numpy as np
    vector = np.random.rand(768).astype('float32')
    
    result = benchmark(encode_vec_str, vector)
    
    assert result.startswith('[')
    assert result.endswith(']')
    assert benchmark.stats['mean'] < 0.001, f"Vector encoding too slow: {benchmark.stats['mean']:.3f}s"


# ==============================================================================
# TESTS DE CARGA (NO SON BENCHMARKS)
# ==============================================================================

@pytest.mark.load
@pytest.mark.skip(reason="Load test - ejecutar manualmente")
def test_concurrent_searches(mock_model_loader, mock_db_connection):
    """
    Test de carga: Búsquedas concurrentes
    
    Simula 100 búsquedas concurrentes y mide tiempos
    """
    import concurrent.futures
    from unittest.mock import patch
    
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    mock_cursor.fetchall.return_value = [{"document_id": "DOC-001", "score": 0.85}]
    
    def single_search(query_id):
        start = time.time()
        with patch('app.search_core.get_conn', return_value=mock_db_connection):
            result = semantic_search(
                query=f"query {query_id}",
                project_id="PROJ-001",
                top_k=10
            )
        duration = time.time() - start
        return duration
    
    # Ejecutar 100 búsquedas en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(single_search, i) for i in range(100)]
        durations = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # Análisis de resultados
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    
    print(f"\n{'='*60}")
    print(f"CONCURRENT SEARCHES TEST (100 searches, 10 workers)")
    print(f"{'='*60}")
    print(f"Average: {avg_duration*1000:.2f}ms")
    print(f"Min:     {min_duration*1000:.2f}ms")
    print(f"Max:     {max_duration*1000:.2f}ms")
    print(f"{'='*60}")
    
    assert avg_duration < 1.0, f"Average search time too high: {avg_duration:.3f}s"


@pytest.mark.load
@pytest.mark.skip(reason="Load test - ejecutar manualmente")
def test_sustained_load(mock_model_loader, mock_db_connection):
    """
    Test de carga sostenida: 1000 operaciones en 60 segundos
    
    Simula carga constante y verifica que no hay degradación
    """
    from unittest.mock import patch
    
    mock_cursor = mock_db_connection.cursor.return_value.__enter__.return_value
    mock_cursor.fetchall.return_value = [{"document_id": "DOC-001", "score": 0.85}]
    
    target_duration = 60  # segundos
    target_operations = 1000
    
    start_time = time.time()
    operations_completed = 0
    durations = []
    
    with patch('app.search_core.get_conn', return_value=mock_db_connection):
        while time.time() - start_time < target_duration and operations_completed < target_operations:
            op_start = time.time()
            
            # Operación (búsqueda)
            semantic_search(
                query=f"query {operations_completed}",
                project_id="PROJ-001",
                top_k=10
            )
            
            op_duration = time.time() - op_start
            durations.append(op_duration)
            operations_completed += 1
            
            # Pequeña pausa para simular carga realista
            time.sleep(0.05)
    
    total_duration = time.time() - start_time
    
    # Análisis de resultados
    avg_duration = sum(durations) / len(durations)
    throughput = operations_completed / total_duration
    
    # Verificar degradación: últimos 100 vs primeros 100
    first_100_avg = sum(durations[:100]) / 100
    last_100_avg = sum(durations[-100:]) / 100
    degradation = ((last_100_avg - first_100_avg) / first_100_avg) * 100
    
    print(f"\n{'='*60}")
    print(f"SUSTAINED LOAD TEST")
    print(f"{'='*60}")
    print(f"Operations:  {operations_completed}")
    print(f"Duration:    {total_duration:.2f}s")
    print(f"Throughput:  {throughput:.2f} ops/second")
    print(f"Avg Time:    {avg_duration*1000:.2f}ms")
    print(f"First 100:   {first_100_avg*1000:.2f}ms")
    print(f"Last 100:    {last_100_avg*1000:.2f}ms")
    print(f"Degradation: {degradation:+.2f}%")
    print(f"{'='*60}")
    
    assert degradation < 20, f"Performance degradation too high: {degradation:.2f}%"


# ==============================================================================
# COMANDOS ÚTILES
# ==============================================================================
"""
# Ejecutar todos los benchmarks
pytest tests/test_performance.py -v --benchmark-only

# Con estadísticas detalladas
pytest tests/test_performance.py --benchmark-only --benchmark-verbose

# Solo grupo de búsqueda
pytest tests/test_performance.py -k "search" --benchmark-only

# Guardar baseline para comparaciones futuras
pytest tests/test_performance.py --benchmark-only --benchmark-save=baseline

# Comparar con baseline
pytest tests/test_performance.py --benchmark-only --benchmark-compare=baseline

# Generar histograma
pytest tests/test_performance.py --benchmark-only --benchmark-histogram

# Tests de carga (no benchmarks)
pytest tests/test_performance.py -v -m load -s

# Ver solo estadísticas, sin tests
pytest tests/test_performance.py --benchmark-only --benchmark-columns=min,max,mean,stddev,median,ops
"""
