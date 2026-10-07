.PHONY: install data test lint run bench docker
install: ; pip install -r requirements.txt
data: ; python scripts/generate_sample_data.py --out data
test: ; pytest -q
lint: ; ruff check app tests scripts
run: ; uvicorn app.main:app --reload
bench: ; python scripts/benchmark.py links.txt 500
docker: ; docker compose up --build
