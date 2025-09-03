# Usa uma imagem Python oficial como base
FROM python:3.9-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e os instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta que o Django usa
EXPOSE 8000

# Comando para rodar o servidor Django quando o contêiner for iniciado
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]