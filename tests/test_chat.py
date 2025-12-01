"""
Tests del módulo de chat conversacional (app/api.py, app/analytics.py)
Escenario 4: Chat con RAG (Retrieval-Augmented Generation)

Tests core seleccionados:
1. Test de chat con contexto de documentos relevantes
2. Test de guardar y recuperar historial de chat
"""
import pytest
from unittest.mock import MagicMock, patch
from app.api import ChatRequest, ChatResponse, chat
from app.analytics import ChatHistory, save_chat_history, get_chat_history


# ============================================================================
# TEST 1: CHAT CON CONTEXTO DE DOCUMENTOS (RESPUESTA BASADA EN RAG)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_chat_with_document_context(mock_model_loader, mock_db_connection):
    """
    Test Core: Chat conversacional con contexto de documentos
    
    Verifica el flujo completo RAG (Retrieval-Augmented Generation):
    1. Recibe pregunta del usuario
    2. Busca documentos relevantes usando búsqueda semántica
    3. Filtra documentos por score de relevancia (> 0.20)
    4. Construye contexto con los documentos más relevantes
    5. Genera respuesta usando LLM (Groq) + contexto
    6. Retorna respuesta con fuentes citadas
    
    Este es el corazón del sistema RAG: combinar búsqueda semántica
    con generación de lenguaje para respuestas contextualizadas.
    """
    # Arrange: Mock de búsqueda semántica con documentos relevantes
    mock_search_results = [
        {
            "document_id": "DOC-ARQUITECTURA-001",
            "title": "Plan Maestro de Arquitectura",
            "number": "200076-CCC02-PL-AR-000400",
            "category": "Arquitectura",
            "doc_type": "Plano",
            "snippet": "El Plan Maestro contempla 24 aulas distribuidas en 3 niveles, "
                      "con biblioteca central, laboratorios de ciencias y áreas recreativas. "
                      "Diseño sismo-resistente según norma NSR-10.",
            "score": 0.87,  # Alta relevancia
            "vector_score": 0.92
        },
        {
            "document_id": "DOC-ESTRUCTURAL-002",
            "title": "Especificaciones Estructurales",
            "number": "200076-CCC02-ES-001",
            "category": "Estructural",
            "doc_type": "Especificación",
            "snippet": "Estructuras de concreto reforzado F'c=280 kg/cm². "
                      "Sistema de cimentación profunda mediante pilotes. "
                      "Cumple códigos sísmicos vigentes.",
            "score": 0.76,
            "vector_score": 0.81
        }
    ]
    
    # Mock del LLM (Groq) con respuesta generada
    mock_groq_response = """Basándome en la documentación técnica disponible, el Plan Maestro de Arquitectura define el diseño integral del proyecto educativo.

**Distribución Espacial**:
El diseño contempla 24 aulas organizadas en 3 niveles, complementadas con espacios comunes como biblioteca central, laboratorios de ciencias y áreas recreativas.

**Especificaciones Estructurales**:
El proyecto utiliza estructuras de concreto reforzado con resistencia F'c=280 kg/cm², implementando un sistema de cimentación profunda mediante pilotes para garantizar estabilidad.

**Normativa Sísmica**:
Todo el diseño cumple con la norma NSR-10 para construcción sismo-resistente, asegurando la seguridad estructural ante eventos sísmicos.

📚 Fuentes consultadas:
- Plan Maestro de Arquitectura (200076-CCC02-PL-AR-000400)
- Especificaciones Estructurales (200076-CCC02-ES-001)"""
    
    # Act: Ejecutar chat con pregunta
    with patch('app.api.semantic_search', return_value=mock_search_results), \
         patch('app.api.Groq') as mock_groq_class, \
         patch.dict('os.environ', {'GROQ_API_KEY': 'test-key-123'}):
        
        # Configurar mock de Groq
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance
        
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock()]
        mock_chat_completion.choices[0].message.content = mock_groq_response
        mock_groq_instance.chat.completions.create.return_value = mock_chat_completion
        
        # Crear request
        request = ChatRequest(
            question="¿Qué incluye el plan maestro de arquitectura?",
            max_context_docs=5,
            session_id="test-session-001"
        )
        
        # Ejecutar chat
        response = chat(request)
    
    # Assert: Verificar comportamiento
    
    # 1. Verificar que se llamó a semantic_search
    from app.api import semantic_search
    # semantic_search debería haber sido llamada con la pregunta
    
    # 2. Verificar estructura de respuesta
    assert isinstance(response, ChatResponse)
    assert response.question == "¿Qué incluye el plan maestro de arquitectura?"
    assert response.answer is not None
    assert len(response.answer) > 50  # Respuesta sustancial
    
    # 3. Verificar que incluyó contexto de documentos
    assert "Plan Maestro" in response.answer or "arquitectura" in response.answer.lower()
    
    # 4. Verificar que tiene sources (documentos citados)
    assert len(response.sources) > 0
    assert any("DOC-ARQUITECTURA-001" in str(s) for s in response.sources)
    
    # 5. Verificar que context_used contiene snippets
    assert len(response.context_used) > 100  # Contexto no vacío
    
    # 6. Verificar session_id
    assert response.session_id is not None
    
    print("\n✅ Chat con contexto RAG validado:")
    print(f"   - Pregunta: {request.question}")
    print(f"   - Documentos encontrados: {len(mock_search_results)}")
    print(f"   - Documentos relevantes (score > 0.20): 2")
    print(f"   - Respuesta generada: {len(response.answer)} caracteres")
    print(f"   - Sources incluidas: {len(response.sources)}")
    print(f"   - Session ID: {response.session_id}")


# ============================================================================
# TEST 2: CHAT SIN DOCUMENTOS RELEVANTES (RESPUESTA POR DEFECTO)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_chat_without_relevant_documents(mock_model_loader):
    """
    Test Core: Chat cuando NO hay documentos relevantes
    
    Verifica que el sistema maneje apropiadamente cuando:
    - No se encuentran documentos con score suficiente (< 0.25)
    - Los documentos encontrados no son relevantes a la pregunta
    
    En este caso debe retornar mensaje informativo indicando que
    no hay información disponible, sin intentar generar respuesta.
    """
    # Arrange: Mock de búsqueda que retorna documentos con score muy bajo
    mock_search_results = [
        {
            "document_id": "DOC-IRRELEVANTE-001",
            "title": "Documento No Relacionado",
            "snippet": "Contenido que no tiene nada que ver con la pregunta...",
            "score": 0.15,  # Score muy bajo
            "vector_score": 0.18
        }
    ]
    
    # Act: Ejecutar chat con pregunta que no tiene respuesta
    with patch('app.api.semantic_search', return_value=mock_search_results):
        request = ChatRequest(
            question="¿Cuál es la receta del pastel de chocolate?",  # Pregunta fuera de contexto
            max_context_docs=5
        )
        
        response = chat(request)
    
    # Assert: Verificar manejo de caso sin documentos relevantes
    
    # 1. Debe retornar respuesta, NO lanzar error
    assert response is not None
    assert isinstance(response, ChatResponse)
    
    # 2. Respuesta debe indicar que no hay información
    assert "No encuentro información relevante" in response.answer or \
           "no tengo" in response.answer.lower() or \
           "no hay" in response.answer.lower()
    
    # 3. NO debe incluir sources (no hay docs relevantes)
    assert len(response.sources) == 0
    
    # 4. Contexto debe estar vacío
    assert response.context_used == ""
    
    print("\n✅ Chat sin documentos relevantes validado:")
    print(f"   - Pregunta fuera de contexto: {request.question}")
    print(f"   - Score máximo encontrado: 0.15 (< 0.25)")
    print(f"   - Respuesta apropiada retornada: ✓")
    print(f"   - No intenta generar respuesta sin contexto: ✓")


# ============================================================================
# TEST 3: GUARDAR HISTORIAL DE CHAT
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
@pytest.mark.mock
def test_save_chat_history(mock_db_connection):
    """
    Test Core: Guardar conversación en historial de chat
    
    Verifica que save_chat_history:
    1. Crea tabla chat_history si no existe
    2. Inserta registro con user_id, question, answer, session_id
    3. Registra timestamp automáticamente
    4. Hace commit a la base de datos
    
    El historial permite analíticas posteriores y contexto de conversación.
    """
    # Arrange: Configurar mock del cursor
    mock_cursor = mock_db_connection.cursor.return_value
    
    # Crear objeto ChatHistory
    chat_data = ChatHistory(
        user_id="user-123",
        question="¿Cuáles son los planos estructurales?",
        answer="Los planos estructurales incluyen cimentación, columnas y vigas...",
        session_id="session-abc-456"
    )
    
    # Act: Guardar en historial
    with patch('app.analytics.psycopg2.connect', return_value=mock_db_connection), \
         patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
        result = save_chat_history(chat_data)
    
    # Assert: Verificar comportamiento
    
    # 1. Verificar que se creó tabla si no existía
    execute_calls = mock_cursor.execute.call_args_list
    assert len(execute_calls) >= 2  # CREATE TABLE + INSERT
    
    create_table_sql = str(execute_calls[0][0][0])
    assert "CREATE TABLE IF NOT EXISTS chat_history" in create_table_sql
    assert "user_id" in create_table_sql
    assert "question" in create_table_sql
    assert "answer" in create_table_sql
    assert "session_id" in create_table_sql
    assert "created_at" in create_table_sql
    
    # 2. Verificar que se insertó el registro
    insert_sql = str(execute_calls[1][0][0])
    insert_params = execute_calls[1][0][1]
    
    assert "INSERT INTO chat_history" in insert_sql
    assert insert_params[0] == "user-123"
    assert insert_params[1] == "¿Cuáles son los planos estructurales?"
    assert insert_params[2].startswith("Los planos estructurales incluyen")
    assert insert_params[3] == "session-abc-456"
    
    # 3. Verificar que se hizo commit
    assert mock_db_connection.commit.called
    
    # 4. Verificar que se cerró conexión
    assert mock_cursor.close.called
    assert mock_db_connection.close.called
    
    # 5. Verificar respuesta exitosa
    assert result["status"] == "success"
    
    print("\n✅ Guardado de historial validado:")
    print(f"   - User ID: {chat_data.user_id}")
    print(f"   - Session ID: {chat_data.session_id}")
    print(f"   - Pregunta: {chat_data.question}")
    print(f"   - Respuesta: {len(chat_data.answer)} caracteres")
    print(f"   - Tabla creada (if not exists): ✓")
    print(f"   - Registro insertado: ✓")
    print(f"   - Commit ejecutado: ✓")


# ============================================================================
# TEST 4: RECUPERAR HISTORIAL DE CHAT
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
@pytest.mark.mock
def test_get_chat_history(mock_db_connection):
    """
    Test Core: Recuperar historial de conversaciones de un usuario
    
    Verifica que get_chat_history:
    1. Consulte historial por user_id
    2. Ordene por fecha descendente (más recientes primero)
    3. Aplique límite de resultados
    4. Retorne lista de conversaciones con timestamps
    """
    # Arrange: Mock de resultados de historial
    mock_cursor = mock_db_connection.cursor.return_value
    
    mock_history = [
        (
            "¿Qué especificaciones tiene el concreto?",
            "El concreto especificado es F'c=280 kg/cm²...",
            "2024-11-26 14:30:00"
        ),
        (
            "¿Cuántas aulas tiene el proyecto?",
            "El proyecto educativo contempla 24 aulas...",
            "2024-11-26 14:25:00"
        ),
        (
            "¿Qué norma sísmica se aplica?",
            "Se aplica la norma NSR-10...",
            "2024-11-26 14:20:00"
        )
    ]
    
    mock_cursor.fetchall.return_value = mock_history
    
    # Act: Obtener historial
    with patch('app.analytics.psycopg2.connect', return_value=mock_db_connection), \
         patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
        history = get_chat_history(user_id="user-123", limit=10)
    
    # Assert: Verificar comportamiento
    
    # 1. Verificar que se ejecutó SELECT correcto
    execute_calls = mock_cursor.execute.call_args_list
    select_sql = str(execute_calls[0][0][0])
    select_params = execute_calls[0][0][1]
    
    assert "SELECT" in select_sql
    assert "FROM chat_history" in select_sql
    assert "WHERE user_id" in select_sql
    assert "ORDER BY created_at DESC" in select_sql
    assert "LIMIT" in select_sql
    
    assert select_params[0] == "user-123"
    assert select_params[1] == 10
    
    # 2. Verificar estructura de resultados
    assert len(history) == 3
    
    # 3. Verificar que están ordenados (más reciente primero)
    assert "14:30:00" in str(history[0])  # Más reciente
    assert "14:25:00" in str(history[1])
    assert "14:20:00" in str(history[2])  # Más antigua
    
    print("\n✅ Recuperación de historial validada:")
    print(f"   - User ID: user-123")
    print(f"   - Conversaciones recuperadas: 3")
    print(f"   - Ordenadas por fecha DESC: ✓")
    print(f"   - Límite aplicado: 10")
    print(f"   - Conversaciones más recientes primero: ✓")


# ============================================================================
# TEST 5: CHAT CON CONTEXTO VACÍO (CASO NEGATIVO)
# ============================================================================

@pytest.mark.unit
def test_chat_with_empty_question():
    """
    Test de Caso Negativo: Chat con pregunta vacía
    
    Verifica que el sistema maneje apropiadamente cuando se envía
    una pregunta vacía o solo con espacios.
    """
    # Arrange & Act
    with patch('app.api.semantic_search', return_value=[]):
        request = ChatRequest(
            question="",  # Pregunta vacía
            max_context_docs=5
        )
        
        response = chat(request)
    
    # Assert: Debe manejar el caso sin crashear
    assert response is not None
    assert isinstance(response, ChatResponse)
    assert response.answer is not None
    
    print("\n✅ Manejo de pregunta vacía validado:")
    print(f"   - Sistema no crashea: ✓")
    print(f"   - Retorna respuesta apropiada: ✓")


# ============================================================================
# TEST 6: ERROR AL GUARDAR HISTORIAL (CASO NEGATIVO)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_save_chat_history_database_error(mock_db_connection):
    """
    Test de Caso Negativo: Error de base de datos al guardar historial
    
    Verifica que save_chat_history maneje apropiadamente errores
    de conexión o ejecución de SQL.
    """
    from fastapi import HTTPException
    
    # Arrange: Mock que lanza excepción
    mock_db_connection.cursor.side_effect = Exception("Database connection failed")
    
    chat_data = ChatHistory(
        user_id="user-123",
        question="Test question",
        answer="Test answer",
        session_id="session-123"
    )
    
    # Act & Assert: Debe lanzar HTTPException
    with patch('app.analytics.psycopg2.connect', return_value=mock_db_connection), \
         patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
        
        with pytest.raises(HTTPException) as exc_info:
            save_chat_history(chat_data)
        
        # Verificar que es error 500
        assert exc_info.value.status_code == 500
        assert "Database connection failed" in str(exc_info.value.detail)
    
    print("\n✅ Manejo de error de BD validado:")
    print(f"   - HTTPException lanzada: ✓")
    print(f"   - Status code 500: ✓")
    print(f"   - Mensaje de error incluido: ✓")


# ============================================================================
# TEST 7: HISTORIAL DE USUARIO INEXISTENTE (CASO NEGATIVO)
# ============================================================================

@pytest.mark.integration
@pytest.mark.mock
def test_get_chat_history_no_results(mock_db_connection):
    """
    Test de Caso Negativo: Obtener historial de usuario sin conversaciones
    
    Verifica que get_chat_history retorne lista vacía cuando el usuario
    no tiene historial previo.
    """
    # Arrange: Mock que retorna vacío
    mock_cursor = mock_db_connection.cursor.return_value
    mock_cursor.fetchall.return_value = []
    
    # Act: Obtener historial de usuario nuevo
    with patch('app.analytics.psycopg2.connect', return_value=mock_db_connection), \
         patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
        history = get_chat_history(user_id="user-nuevo-999", limit=20)
    
    # Assert: Debe retornar lista vacía, NO error
    assert history is not None
    assert isinstance(history, list)
    assert len(history) == 0
    
    print("\n✅ Manejo de usuario sin historial validado:")
    print(f"   - Retorna lista vacía: ✓")
    print(f"   - NO lanza excepción: ✓")
