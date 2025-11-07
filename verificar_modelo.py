"""
Script para verificar dimensiones reales del modelo
"""
from sentence_transformers import SentenceTransformer
import os

model_name = os.environ.get("EMBEDDING_MODEL", "hiiamsid/sentence_similarity_spanish_es")

print(f"Cargando modelo: {model_name}")
model = SentenceTransformer(model_name)

# Generar embedding de prueba
test_text = "documento de prueba"
embedding = model.encode(test_text)

print(f"\n✅ Dimensiones REALES del embedding: {len(embedding)}")
print(f"📊 Tipo: {type(embedding)}")
print(f"🔢 Shape: {embedding.shape}")
