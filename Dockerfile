FROM python:3.11-slim

WORKDIR /workspace
ENV PYTHONPATH=/workspace:/workspace/streamlit

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit/Home.py", "--server.address=0.0.0.0", "--server.port=8501"]
