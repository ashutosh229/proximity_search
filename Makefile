.PHONY: install data test lint run bench docker load
install: ; pip install -r requirements-dev.txt
data: ; python scripts/generate_sample_data.py --out data
test: ; pytest -q
lint: ; ruff check app tests scripts
run: ; uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
bench: ; python scripts/benchmark.py link.txt 500
docker: ; docker compose up --build
load: ; locust -f scripts/locustfile.py --headless -u 100 -r 20 -t 60s -H http://localhost