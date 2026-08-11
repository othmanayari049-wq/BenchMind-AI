.PHONY: install dev backend frontend test lint format typecheck demo docker

install:
	python -m pip install -e '.[dev]'
	cd frontend && npm install

backend:
	uvicorn benchmind.api:app --app-dir backend --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	pytest

lint:
	ruff check backend tests

format:
	ruff format backend tests

typecheck:
	mypy backend/benchmind
	cd frontend && npm run typecheck

demo:
	BENCHMIND_MODEL_PROVIDER=mock python -m benchmind.cli "My HC-SR04 always reads 0 cm" examples/esp32_wrong_gpio/firmware.ino examples/esp32_wrong_gpio/wiring.txt

docker:
	docker compose up --build
