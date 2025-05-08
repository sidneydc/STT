# Usando a imagem base oficial do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo de código para dentro do container
COPY . /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta 5000 para o Flask
EXPOSE 5000

# Comando para rodar o app Flask
CMD ["python", "app.py"]
