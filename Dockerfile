# Use uma imagem base Python oficial
FROM python:3.9-slim-buster
# Defina variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Defina o diretório de trabalho dentro do container
WORKDIR /app
# Copie o arquivo requirements.txt e instale as dependências
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt
# Copie o restante do código da aplicação para o diretório de trabalho
COPY . /app/
# Coletar arquivos estáticos (se aplicável)
# RUN python manage.py collectstatic --noinput
# Exponha a porta que o servidor de desenvolvimento Django irá escutar
EXPOSE 8000
# Comando para rodar o servidor de desenvolvimento Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
