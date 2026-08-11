FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY examples ./examples
RUN pip install --no-cache-dir .
RUN useradd --create-home --uid 10001 benchmind \
    && mkdir -p /app/.benchmind \
    && chown -R benchmind:benchmind /app
USER benchmind
EXPOSE 8000
CMD ["uvicorn", "benchmind.api:app", "--host", "0.0.0.0", "--port", "8000"]
