# Imagen del agente economico (plan seccion 8).
# REGLA: nunca COPY .env ni secrets/ — se inyectan en runtime (compose).

FROM python:3.12-slim

# HF_HOME: carpeta donde Hugging Face guarda el modelo de embeddings.
# Al vivir dentro de la imagen, no se vuelve a descargar en cada contenedor.
ENV HF_HOME=/app/.hf_cache \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# torch en version solo-CPU: la de PyPI trae CUDA (~varios GB) que aqui no se usa
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Dependencias primero (mejor cache de capas Docker)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Descarga el modelo de sentence-transformers en el build (una sola vez, ~470 MB).
# Esta capa queda cacheada: solo se repite si cambian las capas anteriores.
RUN python -c "from sentence_transformers import SentenceTransformer; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# A partir de aqui, nunca consultar el Hub: usar solo el modelo ya horneado
ENV HF_HUB_OFFLINE=1

# Codigo de aplicacion: paquetes agent/ y ontology/ + app Streamlit (sin secretos)
COPY agent/ ./agent/
COPY ontology/ ./ontology/
COPY app.py .
COPY .streamlit/ ./.streamlit/

# Puerto de la interfaz Streamlit (servicio "ui" en docker-compose)
EXPOSE 8501

# Entrypoint del plan (CLI); la pregunta se pasa como argumento o por stdin
CMD ["python", "-m", "agent.main"]
