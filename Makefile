.PHONY: run test benchmark prepare-data

run:
	python -m app.server

test:
	python -m unittest discover -s tests -v

benchmark:
	python scripts/benchmark.py

prepare-data:
	python scripts/prepare_official_data.py official_data data_official --version official-v1
