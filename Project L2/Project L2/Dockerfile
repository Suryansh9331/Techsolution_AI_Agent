FROM python:3.10-slim

WORKDIR /app

# Install base dependencies
RUN pip install --no-cache-dir \
    langchain==0.1.3 \
    langchain-community==0.0.16 \
    langchain-core==0.1.15 \
    pydantic==2.5.2 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-dotenv==1.0.0 \
    chromadb==0.4.17 \
    sentence-transformers==2.2.2 \
    openai==1.3.7 \
    ollama==0.1.5 \
    autogen==0.2.19 \
    bs4==0.0.1 \
    pypdf==3.17.1 \
    tiktoken==0.5.1 \
    numpy==1.26.2 \
    pandas==2.1.3

# Copy project files
COPY . .

# Expose port for API
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


