FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY market_risk_platform ./market_risk_platform

EXPOSE 8000
CMD ["uvicorn", "market_risk_platform.api:app", "--host", "0.0.0.0", "--port", "8000"]

