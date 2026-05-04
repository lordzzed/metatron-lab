# Dockerfile
FROM python:3.11-slim

# Instalação de dependências do SO no build (onde temos privilégios)
RUN apt-get update && apt-get install -y \
    nmap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalação das abstrações Python
RUN pip install --no-cache-dir \
    requests \
    ollama \
    python-nmap

# O container iniciará aguardando comandos do orquestrador
CMD ["tail", "-f", "/dev/null"]
