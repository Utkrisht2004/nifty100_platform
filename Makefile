# Nifty 100 Financial Intelligence Platform - Makefile

.PHONY: load ratios test report dashboard api clean

load:
	python src/etl/loader.py

ratios:
	python src/analytics/ratios.py

test:
	pytest tests/ --html=reports/pytest_report.html

report:
	python src/reports/portfolio_report.py

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --port 8000 --reload

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache