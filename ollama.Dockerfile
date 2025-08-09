FROM ollama/ollama AS builder
RUN ollama serve & sleep 5 && ollama pull llama3 && pkill ollama

FROM ollama/ollama
COPY --from=builder /root/.ollama /root/.ollama