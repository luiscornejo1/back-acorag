"""
Script de Diagnóstico de Embeddings y Búsqueda Vectorial
========================================================

Verifica:
1. Calidad de embeddings (normas, distribución)
2. Similitud entre queries y documentos
3. Funcionamiento del índice IVFFlat
4. Comparación con búsqueda de texto
5. Análisis de chunks problemáticos
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    return psycopg2.connect(url)

def get_model():
    name = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print_info(f"Cargando modelo: {name}")
    return SentenceTransformer(name, trust_remote_code=True)

def encode_text(model, text):
    """Genera embedding normalizado"""
    v = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
    return v

def cosine_similarity(v1, v2):
    """Calcula similitud coseno entre dos vectores"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# ============================================================================
# TEST 1: Información básica de la BD
# ============================================================================

def test_database_info():
    print_header("TEST 1: Información de la Base de Datos")
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Contar documentos
        cur.execute("SELECT COUNT(*) as total FROM documents")
        doc_count = cur.fetchone()['total']
        print_info(f"Total de documentos: {doc_count}")
        
        # Contar chunks
        cur.execute("SELECT COUNT(*) as total FROM document_chunks")
        chunk_count = cur.fetchone()['total']
        print_info(f"Total de chunks: {chunk_count}")
        
        if chunk_count == 0:
            print_error("No hay chunks en la BD. Necesitas ingestar documentos primero.")
            return False
        
        # Chunks con embeddings
        cur.execute("SELECT COUNT(*) as total FROM document_chunks WHERE embedding IS NOT NULL")
        chunks_with_emb = cur.fetchone()['total']
        print_info(f"Chunks con embeddings: {chunks_with_emb}")
        
        if chunks_with_emb < chunk_count:
            print_warning(f"{chunk_count - chunks_with_emb} chunks sin embeddings")
        
        # Verificar índice IVFFlat
        cur.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'document_chunks' 
            AND indexdef LIKE '%ivfflat%'
        """)
        indexes = cur.fetchall()
        
        if indexes:
            print_success(f"Índice IVFFlat encontrado: {indexes[0]['indexname']}")
            print(f"   Definición: {indexes[0]['indexdef'][:100]}...")
        else:
            print_error("No se encontró índice IVFFlat. La búsqueda será lenta.")
        
        # Promedio de chunks por documento
        avg_chunks = chunk_count / doc_count if doc_count > 0 else 0
        print_info(f"Promedio de chunks por documento: {avg_chunks:.1f}")
        
        if avg_chunks < 3:
            print_warning("Promedio de chunks muy bajo. Los documentos podrían ser muy cortos.")
        elif avg_chunks > 100:
            print_warning("Promedio de chunks muy alto. Los chunks podrían ser muy pequeños.")
        
        return True

# ============================================================================
# TEST 2: Calidad de los embeddings
# ============================================================================

def test_embedding_quality():
    print_header("TEST 2: Calidad de los Embeddings")
    
    model = get_model()
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Obtener muestra de embeddings
        cur.execute("""
            SELECT embedding::text 
            FROM document_chunks 
            WHERE embedding IS NOT NULL 
            LIMIT 100
        """)
        rows = cur.fetchall()
        
        if not rows:
            print_error("No hay embeddings para analizar")
            return False
        
        print_info(f"Analizando {len(rows)} embeddings...")
        
        norms = []
        dimensions = []
        
        for row in rows:
            # Parsear vector desde string PostgreSQL '[1.23,4.56,...]'
            emb_str = row['embedding']
            emb_values = [float(x) for x in emb_str.strip('[]').split(',')]
            emb_array = np.array(emb_values)
            
            norm = np.linalg.norm(emb_array)
            norms.append(norm)
            dimensions.append(len(emb_array))
        
        # Análisis de normas
        avg_norm = np.mean(norms)
        std_norm = np.std(norms)
        min_norm = np.min(norms)
        max_norm = np.max(norms)
        
        print(f"\n{Colors.BOLD}Análisis de Normas:{Colors.END}")
        print(f"   Promedio: {avg_norm:.4f}")
        print(f"   Desv. Est: {std_norm:.4f}")
        print(f"   Mínimo: {min_norm:.4f}")
        print(f"   Máximo: {max_norm:.4f}")
        
        # Los embeddings normalizados deberían tener norma ~1.0
        if 0.95 <= avg_norm <= 1.05:
            print_success("Embeddings están correctamente normalizados")
        else:
            print_warning(f"Embeddings NO están normalizados (esperado: ~1.0, actual: {avg_norm:.4f})")
        
        # Verificar dimensionalidad
        unique_dims = set(dimensions)
        if len(unique_dims) == 1:
            dim = dimensions[0]
            print_success(f"Todos los embeddings tienen {dim} dimensiones")
            
            # Verificar si coincide con el modelo
            test_emb = encode_text(model, "test")
            if len(test_emb) == dim:
                print_success(f"Dimensionalidad coincide con el modelo ({len(test_emb)}D)")
            else:
                print_error(f"Dimensionalidad NO coincide: BD={dim}D, Modelo={len(test_emb)}D")
        else:
            print_error(f"Dimensiones inconsistentes: {unique_dims}")
        
        return True

# ============================================================================
# TEST 3: Similitud entre queries y documentos
# ============================================================================

def test_query_similarity():
    print_header("TEST 3: Similitud entre Queries y Documentos")
    
    model = get_model()
    
    # Queries de prueba
    test_queries = [
        "informe mensual de costos",
        "cronograma del proyecto",
        "especificaciones técnicas",
        "planos estructurales",
        "contrato de construcción"
    ]
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        for query in test_queries:
            print(f"\n{Colors.BOLD}Query: '{query}'{Colors.END}")
            
            # Generar embedding de la query
            query_emb = encode_text(model, query)
            query_str = '[' + ','.join(str(float(x)) for x in query_emb) + ']'
            
            # Búsqueda vectorial (top 5)
            cur.execute(f"""
                SELECT 
                    dc.content,
                    d.title,
                    d.number,
                    1 - (dc.embedding <=> '{query_str}') AS similarity
                FROM document_chunks dc
                JOIN documents d ON d.document_id = dc.document_id
                WHERE dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> '{query_str}'
                LIMIT 5
            """)
            results = cur.fetchall()
            
            if not results:
                print_error("Sin resultados")
                continue
            
            print(f"\n   Top 5 resultados:")
            for i, row in enumerate(results, 1):
                similarity = row['similarity']
                title = row['title'][:40] + "..." if len(row['title']) > 40 else row['title']
                snippet = row['content'][:60] + "..." if len(row['content']) > 60 else row['content']
                
                # Clasificar similitud
                if similarity >= 0.7:
                    color = Colors.GREEN
                    label = "EXCELENTE"
                elif similarity >= 0.5:
                    color = Colors.YELLOW
                    label = "BUENA"
                elif similarity >= 0.3:
                    color = Colors.YELLOW
                    label = "MODERADA"
                else:
                    color = Colors.RED
                    label = "BAJA"
                
                print(f"   {i}. {color}[{similarity:.3f} - {label}]{Colors.END}")
                print(f"      Doc: {title}")
                print(f"      Snippet: {snippet}")
            
            # Análisis de distribución
            max_sim = results[0]['similarity']
            avg_sim = np.mean([r['similarity'] for r in results])
            
            if max_sim < 0.4:
                print_warning(f"Similitud máxima muy baja ({max_sim:.3f}). Posibles causas:")
                print("      - Query no relacionada con contenido de documentos")
                print("      - Embeddings de mala calidad")
                print("      - Modelo no adecuado para el dominio")
            elif max_sim >= 0.7:
                print_success(f"Excelente similitud máxima: {max_sim:.3f}")
            
            print(f"   Similitud promedio (top 5): {avg_sim:.3f}")

# ============================================================================
# TEST 4: Comparación Vector vs Texto
# ============================================================================

def test_vector_vs_text():
    print_header("TEST 4: Comparación Búsqueda Vectorial vs Texto")
    
    model = get_model()
    test_query = "informe de costos del proyecto"
    
    print_info(f"Query de prueba: '{test_query}'")
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Búsqueda vectorial
        query_emb = encode_text(model, test_query)
        query_str = '[' + ','.join(str(float(x)) for x in query_emb) + ']'
        
        cur.execute(f"""
            SELECT 
                d.title,
                1 - (dc.embedding <=> '{query_str}') AS vector_score
            FROM document_chunks dc
            JOIN documents d ON d.document_id = dc.document_id
            WHERE dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> '{query_str}'
            LIMIT 5
        """)
        vector_results = cur.fetchall()
        
        # Búsqueda de texto
        cur.execute("""
            SELECT 
                d.title,
                ts_rank(to_tsvector('spanish', d.title || ' ' || dc.content), 
                        plainto_tsquery('spanish', %s)) AS text_score
            FROM document_chunks dc
            JOIN documents d ON d.document_id = dc.document_id
            ORDER BY text_score DESC
            LIMIT 5
        """, (test_query,))
        text_results = cur.fetchall()
        
        print(f"\n{Colors.BOLD}Búsqueda Vectorial:{Colors.END}")
        for i, row in enumerate(vector_results, 1):
            print(f"   {i}. [{row['vector_score']:.3f}] {row['title'][:60]}")
        
        print(f"\n{Colors.BOLD}Búsqueda de Texto:{Colors.END}")
        for i, row in enumerate(text_results, 1):
            score = row['text_score'] if row['text_score'] else 0
            print(f"   {i}. [{score:.3f}] {row['title'][:60]}")
        
        # Comparar scores promedio
        avg_vector = np.mean([r['vector_score'] for r in vector_results])
        avg_text = np.mean([r['text_score'] if r['text_score'] else 0 for r in text_results])
        
        print(f"\n{Colors.BOLD}Comparación:{Colors.END}")
        print(f"   Score promedio vectorial: {avg_vector:.3f}")
        print(f"   Score promedio texto: {avg_text:.3f}")
        
        if avg_vector < 0.3:
            print_warning("Búsqueda vectorial tiene scores muy bajos")
        if avg_text > avg_vector:
            print_info("Búsqueda de texto supera a vectorial en este caso")

# ============================================================================
# TEST 5: Análisis de chunks problemáticos
# ============================================================================

def test_problematic_chunks():
    print_header("TEST 5: Análisis de Chunks Problemáticos")
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Chunks muy cortos
        cur.execute("""
            SELECT COUNT(*) as total, AVG(LENGTH(content)) as avg_length
            FROM document_chunks
            WHERE LENGTH(content) < 50
        """)
        short_chunks = cur.fetchone()
        
        if short_chunks['total'] > 0:
            print_warning(f"{short_chunks['total']} chunks con menos de 50 caracteres")
            print(f"   Longitud promedio: {short_chunks['avg_length']:.0f} chars")
        
        # Chunks muy largos
        cur.execute("""
            SELECT COUNT(*) as total, AVG(LENGTH(content)) as avg_length
            FROM document_chunks
            WHERE LENGTH(content) > 2000
        """)
        long_chunks = cur.fetchone()
        
        if long_chunks['total'] > 0:
            print_warning(f"{long_chunks['total']} chunks con más de 2000 caracteres")
            print(f"   Longitud promedio: {long_chunks['avg_length']:.0f} chars")
        
        # Chunks sin embedding
        cur.execute("""
            SELECT COUNT(*) as total
            FROM document_chunks
            WHERE embedding IS NULL
        """)
        no_emb = cur.fetchone()['total']
        
        if no_emb > 0:
            print_error(f"{no_emb} chunks sin embedding")
        
        # Distribución de longitudes
        cur.execute("""
            SELECT 
                MIN(LENGTH(content)) as min_len,
                MAX(LENGTH(content)) as max_len,
                AVG(LENGTH(content)) as avg_len,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY LENGTH(content)) as median_len
            FROM document_chunks
        """)
        stats = cur.fetchone()
        
        print(f"\n{Colors.BOLD}Estadísticas de Longitud de Chunks:{Colors.END}")
        print(f"   Mínimo: {stats['min_len']} chars")
        print(f"   Máximo: {stats['max_len']} chars")
        print(f"   Promedio: {stats['avg_len']:.0f} chars")
        print(f"   Mediana: {stats['median_len']:.0f} chars")
        
        # Longitud ideal: 200-800 caracteres
        if 200 <= stats['avg_len'] <= 800:
            print_success("Longitud de chunks en rango óptimo (200-800 chars)")
        elif stats['avg_len'] < 200:
            print_warning("Chunks demasiado cortos. Considera aumentar el tamaño.")
        else:
            print_warning("Chunks demasiado largos. Considera reducir el tamaño.")

# ============================================================================
# TEST 6: Test de similitud manual
# ============================================================================

def test_manual_similarity():
    print_header("TEST 6: Test de Similitud Manual")
    
    model = get_model()
    
    # Pares de texto similares
    test_pairs = [
        ("informe de costos", "reporte de gastos"),
        ("cronograma del proyecto", "plan temporal de trabajo"),
        ("plano estructural", "diseño de estructura"),
        ("gato negro", "auto rojo"),  # Par NO similar
    ]
    
    print_info("Calculando similitud entre pares de texto...")
    print()
    
    for text1, text2 in test_pairs:
        emb1 = encode_text(model, text1)
        emb2 = encode_text(model, text2)
        
        similarity = cosine_similarity(emb1, emb2)
        
        if similarity >= 0.7:
            color = Colors.GREEN
            label = "MUY SIMILAR"
        elif similarity >= 0.5:
            color = Colors.YELLOW
            label = "SIMILAR"
        elif similarity >= 0.3:
            color = Colors.YELLOW
            label = "POCO SIMILAR"
        else:
            color = Colors.RED
            label = "NO SIMILAR"
        
        print(f"   '{text1}' <-> '{text2}'")
        print(f"   {color}Similitud: {similarity:.3f} ({label}){Colors.END}\n")
    
    print_info("Si los pares similares tienen score < 0.5, el modelo podría no ser adecuado.")

# ============================================================================
# TEST 7: Verificar configuración de probes
# ============================================================================

def test_ivfflat_probes():
    print_header("TEST 7: Configuración de IVFFlat Probes")
    
    with get_conn() as conn, conn.cursor() as cur:
        # Verificar configuración actual
        try:
            cur.execute("SHOW ivfflat.probes")
            probes = cur.fetchone()[0]
            print_info(f"ivfflat.probes actual: {probes}")
            
            if int(probes) < 10:
                print_warning("Probes muy bajo. Considera aumentar a 10-20 para mejor precisión.")
            else:
                print_success("Probes en rango adecuado")
        except Exception as e:
            print_error(f"No se pudo verificar probes: {e}")
            conn.rollback()  # Limpiar transacción fallida
            return  # Salir del test si no se puede verificar probes
        
        # Test con diferentes valores de probes
        test_query = "informe costos"
        model = get_model()
        query_emb = encode_text(model, test_query)
        query_str = '[' + ','.join(str(float(x)) for x in query_emb) + ']'
        
        print(f"\n{Colors.BOLD}Comparando resultados con diferentes probes:{Colors.END}")
        
        for probe_val in [1, 5, 10, 20]:
            try:
                cur.execute(f"SET LOCAL ivfflat.probes = {probe_val}")
                cur.execute(f"""
                    SELECT 1 - (embedding <=> '{query_str}') AS similarity
                    FROM document_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> '{query_str}'
                    LIMIT 1
                """)
                result = cur.fetchone()
            except Exception as e:
                print_error(f"Error con probes={probe_val}: {e}")
                conn.rollback()
                continue
            
            if result:
                sim = result[0]
                print(f"   Probes={probe_val:2d} → Mejor similitud: {sim:.4f}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║          DIAGNÓSTICO DE EMBEDDINGS Y BÚSQUEDA VECTORIAL                      ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    try:
        # Ejecutar todos los tests
        tests = [
            ("Información de BD", test_database_info),
            ("Calidad de Embeddings", test_embedding_quality),
            ("Similitud Query-Docs", test_query_similarity),
            ("Vector vs Texto", test_vector_vs_text),
            ("Chunks Problemáticos", test_problematic_chunks),
            ("Similitud Manual", test_manual_similarity),
            ("IVFFlat Probes", test_ivfflat_probes),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                result = test_func()
                if result is None or result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"Error en {name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        # Resumen final
        print_header("RESUMEN FINAL")
        print(f"   Tests ejecutados: {passed + failed}")
        print(f"   {Colors.GREEN}Exitosos: {passed}{Colors.END}")
        print(f"   {Colors.RED}Fallidos: {failed}{Colors.END}")
        
        print(f"\n{Colors.BOLD}Recomendaciones:{Colors.END}")
        print("   1. Si las similitudes son < 0.4, considera re-generar embeddings")
        print("   2. Si hay muchos chunks sin embeddings, ejecuta regenerar_embeddings.py")
        print("   3. Si la búsqueda de texto supera a vectorial, verifica el modelo")
        print("   4. Longitud óptima de chunks: 200-800 caracteres")
        print("   5. Probes óptimos: 10-20 para mejor precision/recall")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Diagnóstico interrumpido por el usuario{Colors.END}")
    except Exception as e:
        print_error(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
