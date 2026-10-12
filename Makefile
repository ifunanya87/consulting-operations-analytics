# Variables
DBT_DIR = data_modeling
STORY_DIR = data_storytelling
APP_PATH = $(STORY_DIR)/streamlit/app.py
EXPORT_SCRIPT = $(STORY_DIR)/export_gold_tables.py

.PHONY: all setup dbt export app run clean help

# Default target when running just 'make'
all: run

setup: ## Install/sync virtual environment and dependencies using uv
	@echo "==> Syncing dependencies with uv..."
	uv sync

dbt: ## Run dbt models to compile Bronze, Silver, and Gold tables
	@echo "==> Running dbt models..."
	cd $(DBT_DIR) && uv run dbt run

export: ## Export Gold tables to the data/ folder for Power BI
	@echo "==> Exporting Gold models to data/ folder..."
	uv run python $(EXPORT_SCRIPT)

app: ## Launch the Streamlit multi-page dashboard
	@echo "==> Launching Streamlit multi-page application..."
	uv run streamlit run $(APP_PATH)

run: setup dbt export app ## Execute full pipeline sequentially (setup -> dbt -> export -> streamlit)

clean: ## Remove dbt build target artifacts and Python byte-cache files
	@echo "==> Cleaning temporary build files and caches..."
	rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -rf .pytest_cache
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages

help: ## Display available Makefile commands
	@echo ""
	@echo "Available Makefile Commands:"
	@echo "----------------------------"
	@python3 -c 'import sys; [print(f"  \033[36m{l.split(chr(58))[0].strip():<15}\033[0m {l.split(chr(35)*2)[1].strip()}") for l in open("Makefile") if chr(35)*2 in l and chr(58) in l and not l.strip().startswith(chr(35)) and not l.strip().startswith("help")]'
	@echo ""

%:
	@echo ""
	@echo "Error: Unknown target '$@'."
	@$(MAKE) --no-print-directory help
