FROM python:3.9-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir flask

# Criar o banco de dados na inicialização
RUN mkdir -p /app/instance

# Expor a porta 5000
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
