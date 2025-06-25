# Chatbot Docker Development Commands

.PHONY: help build run dev stop clean logs shell-backend shell-frontend health

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker containers
	docker compose build

run: build ## Build and run all services
	docker compose up --remove-orphans
	@echo "Services started in background. Use 'make logs' to view logs."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8080"
	@echo "MongoDB: localhost:27017"
	@echo "Redis: localhost:6379"

stop: ## Stop all running services
	docker compose down

clean: ## Stop services and remove containers, networks, and volumes
	docker compose down -v --remove-orphans
	docker system prune -f

logs: ## Follow logs from all services
	docker compose logs -f

logs-backend: ## Follow backend logs only
	docker compose logs -f backend

logs-frontend: ## Follow frontend logs only
	docker compose logs -f frontend

shell-backend: ## Open shell in backend container
	docker compose exec backend sh

shell-frontend: ## Open shell in frontend container
	docker compose exec frontend sh

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8080/health | python3 -m json.tool || echo "Backend health check failed"
