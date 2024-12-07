FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* .env /app/

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --without dev

COPY . /app

EXPOSE 8501

ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "main.py"]
