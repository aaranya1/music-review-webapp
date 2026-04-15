SHELL := bash
.PHONY: dev db backend frontend stop setup docker docker-down seed clean

# ── Local Development (3 services, one command) ──────────────────────────────

dev: db
	@echo "Starting backend and frontend..."
	@cd backend && source venv/Scripts/activate && flask run &
	@cd frontend && npm run dev

db:
	cd backend && docker compose up -d

backend:
	cd backend && source venv/Scripts/activate && flask run

frontend:
	cd frontend && npm run dev

stop:
	cd backend && docker compose down
	@echo "Stopped database. Kill flask/vite processes manually if needed."

# ── First-Time Setup ─────────────────────────────────────────────────────────

setup:
	cd backend && python -m venv venv && source venv/Scripts/activate && pip install -r requirements.txt
	cd frontend && npm install
	cd backend && docker compose up -d
	@echo "Waiting for database to start..."
	@sleep 3
	cd backend && source venv/Scripts/activate && flask db upgrade
	@echo "Setup complete! Run 'make dev' to start."

# ── Docker Production (single command) ───────────────────────────────────────

docker:
	docker compose up --build -d
	@echo "App running at http://localhost"

docker-down:
	docker compose down

# ── Database ─────────────────────────────────────────────────────────────────

seed:
	docker compose exec -T db psql -U jukeboxed jukeboxed < backup.sql
	@echo "Database restored from backup.sql"

# ── Clean ────────────────────────────────────────────────────────────────────

clean:
	$(MAKE) clean-$(if $(filter Windows_NT,$(OS)),windows,unix)

clean-windows:
	-taskkill /FI "WINDOWTITLE eq *flask*" /F >NUL 2>&1
	-taskkill /FI "WINDOWTITLE eq *vite*" /F >NUL 2>&1
	-cd backend && docker compose down
	-if exist backend\venv rmdir /S /Q backend\venv
	-if exist frontend\node_modules rmdir /S /Q frontend\node_modules
	-if exist frontend\dist rmdir /S /Q frontend\dist
	-if exist backend\.pytest_cache rmdir /S /Q backend\.pytest_cache
	-if exist backend\__pycache__ rmdir /S /Q backend\__pycache__
	-docker system prune -a -f
	@echo "Cleanup complete!"

clean-unix:
	pkill -f "flask run" || true
	pkill -f "vite" || true
	cd backend && docker compose down
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -rf frontend/dist
	rm -rf backend/.pytest_cache
	rm -rf backend/__pycache__
	docker system prune -a -f
	@echo "Cleanup complete!"
