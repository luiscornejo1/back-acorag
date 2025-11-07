"""Test rápido para ver la estructura de respuesta"""
import requests
import json

url = "https://back-acorag-production.up.railway.app/search"

response = requests.post(url, json={"query": "plano", "top_k": 2})

print(f"Status: {response.status_code}")
print(f"Response:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
