"""
Módulo para subir documentos nuevos y hacer ingesta en tiempo real
Soporta: PDF, TXT, JSON, DOCX
"""
import os
import json
import tempfile
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib

# PDF extraction
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# DOCX extraction
try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from sentence_transformers import SentenceTransformer
from app.utils import get_db_connection


class DocumentUploader:
    """Maneja la carga y procesamiento de documentos nuevos"""
    
    def __init__(self):
        self.model = SentenceTransformer(
            os.getenv("EMBEDDING_MODEL", "hiiamsid/sentence_similarity_spanish_es")
        )
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extrae texto de un PDF"""
        if not HAS_PDF:
            raise ImportError("PyPDF2 no está instalado. Ejecuta: pip install PyPDF2")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error extrayendo texto de PDF: {e}")
        
        return text.strip()
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extrae texto de un DOCX"""
        if not HAS_DOCX:
            raise ImportError("python-docx no está instalado. Ejecuta: pip install python-docx")
        
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extrayendo texto de DOCX: {e}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Lee texto plano"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Error leyendo archivo TXT: {e}")
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extrae texto según el tipo de archivo"""
        if file_type == "pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type == "docx":
            return self.extract_text_from_docx(file_path)
        elif file_type == "txt":
            return self.extract_text_from_txt(file_path)
        elif file_type == "json":
            # Para JSON, leer y extraer campos relevantes
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Si es un objeto con campos, extraerlos
                if isinstance(data, dict):
                    return json.dumps(data, indent=2, ensure_ascii=False)
                return str(data)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_type}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Divide el texto en chunks con overlap"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Intentar cortar en un punto natural (., !, ?, \n)
            if end < len(text):
                last_period = max(
                    chunk.rfind('.'),
                    chunk.rfind('!'),
                    chunk.rfind('?'),
                    chunk.rfind('\n')
                )
                if last_period > self.chunk_size * 0.5:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return chunks
    
    def generate_document_id(self, filename: str, content: str) -> str:
        """Genera un ID único para el documento"""
        hash_input = f"{filename}_{content[:100]}_{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def ingest_document(
        self,
        file_path: str,
        filename: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        raw_content: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Ingesta un documento completo:
        1. Extrae texto
        2. Divide en chunks
        3. Genera embeddings
        4. Guarda en PostgreSQL
        
        Args:
            file_path: Ruta temporal del archivo
            filename: Nombre del archivo original
            file_type: Tipo (pdf, txt, docx, json)
            metadata: Metadatos opcionales
            raw_content: Contenido binario del archivo original (para poder servirlo después)
        
        Returns:
            Dict con información del documento ingestado
        """
        try:
            # 1. Leer contenido binario si no se proporcionó
            if raw_content is None:
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
            
            # 2. Extraer texto
            print(f"📄 Extrayendo texto de {filename}...")
            text = self.extract_text(file_path, file_type)
            
            if not text or len(text) < 10:
                raise ValueError("El documento está vacío o tiene muy poco contenido")
            
            # 2. Generar ID único
            doc_id = self.generate_document_id(filename, text)
            
            # 3. Preparar metadata
            if metadata is None:
                metadata = {}
            
            project_id = metadata.get("project_id", "UPLOADED")
            doc_type = metadata.get("doc_type", "documento")
            title = metadata.get("title", filename.rsplit('.', 1)[0])
            
            # 4. Conectar a la base de datos
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 5. Verificar si el documento ya existe
            cursor.execute(
                "SELECT document_id FROM documents WHERE document_id = %s",
                (doc_id,)
            )
            if cursor.fetchone():
                raise ValueError(f"El documento ya existe en la base de datos (ID: {doc_id})")
            
            # 6. Insertar documento usando el schema correcto
            print(f"💾 Guardando documento en la base de datos...")
            cursor.execute("""
                INSERT INTO documents (
                    document_id, project_id, title, filename, 
                    file_type, doc_type, date_modified, file_content
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (
                doc_id,
                project_id,
                title,
                filename,
                file_type,
                doc_type,
                raw_content  # ← GUARDAR EN file_content (bytea), no en raw (jsonb)
            ))
            
            # 7. Dividir en chunks
            print(f"✂️  Dividiendo texto en chunks...")
            chunks = self.chunk_text(text)
            print(f"   → {len(chunks)} chunks generados")
            
            # 8. Generar embeddings e insertar chunks
            print(f"🔢 Generando embeddings...")
            for idx, chunk in enumerate(chunks):
                # Generar embedding
                embedding = self.model.encode(chunk).tolist()
                embedding_str = '[' + ','.join(str(float(x)) for x in embedding) + ']'
                
                # Insertar chunk usando el schema correcto (chunk_id debe ser UUID)
                chunk_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO document_chunks (
                        chunk_id, document_id, project_id, 
                        title, content, embedding, date_modified
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::vector, NOW())
                """, (
                    chunk_id,
                    doc_id,
                    project_id,
                    title,
                    chunk,
                    embedding_str
                ))
            
            # 9. Commit
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Documento ingestado exitosamente!")
            
            return {
                "success": True,
                "document_id": doc_id,
                "filename": filename,
                "chunks_created": len(chunks),
                "text_length": len(text),
                "project_id": project_id,
                "title": title
            }
        
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            raise Exception(f"Error en la ingesta: {str(e)}")


def upload_and_ingest(
    file_content: bytes,
    filename: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Función helper para subir un archivo desde bytes
    
    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre original del archivo
        metadata: Metadata opcional del documento
    
    Returns:
        Dict con resultado de la ingesta
    """
    # Determinar tipo de archivo
    file_ext = filename.split('.')[-1].lower()
    if file_ext not in ['pdf', 'txt', 'docx', 'json']:
        raise ValueError(f"Tipo de archivo no soportado: {file_ext}")
    
    # Guardar temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    try:
        # Ingestar
        uploader = DocumentUploader()
        result = uploader.ingest_document(
            tmp_path, 
            filename, 
            file_ext, 
            metadata,
            raw_content=file_content  # ← Pasar contenido binario original
        )
        return result
    finally:
        # Limpiar archivo temporal
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
