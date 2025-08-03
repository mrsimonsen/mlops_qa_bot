FROM python:3.12-slim
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src /app/src
COPY ./data/chroma_db /app/data/chroma_db
EXPOSE 8000
ENV PYTHONPATH="${PYTHONPATH}:/app"
CMD [ "uvicorn", "src.rag_app.main:app", "--host", "0.0.0.0", "--port", "8000" ]