FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir kafka-python==2.0.2

COPY producer/produce_oci_logs.py /app/produce_oci_logs.py
COPY fixtures/oci-log-samples.jsonl /app/fixtures/oci-log-samples.jsonl

ENTRYPOINT ["python", "/app/produce_oci_logs.py"]
