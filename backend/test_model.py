import os
from sentence_transformers import SentenceTransformer

# Set offline mode like in rag.py
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

MODEL_NAME = "BAAI/bge-small-en-v1.5"

print(f"Attempting to load model: {MODEL_NAME}...")
try:
    model = SentenceTransformer(MODEL_NAME, device="cpu", local_files_only=True)
    print("Success: Model loaded successfully.")
except Exception as e:
    print(f"Error: Failed to load model. {str(e)}")
