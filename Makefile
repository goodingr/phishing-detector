.PHONY: test-backend test-frontend build-frontend install-frontend

test-backend:
	python -m pytest

test-frontend:
	cd frontend && npm test -- --watchAll=false

build-frontend:
	cd frontend && npm run build

install-frontend:
	cd frontend && npm install
