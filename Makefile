SHELL := powershell.exe
WORKDIR := fastapi-mcp
VENV_ACTIVATE := .\$(WORKDIR)\.venv\Scripts\Activate.ps1
PYTHON := .\$(WORKDIR)\.venv\Scripts\python.exe

.PHONY: start-server prod-test flask-test

start-server:
	Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force; \
	cd $(WORKDIR); \
	.\start-server.ps1

prod-test:
	Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force; \
	cd $(WORKDIR); \
	. $(VENV_ACTIVATE); \
	$(PYTHON) prod_tests/04_invoke_tool_http.py --query "AI regulation" --limit 3 --summary-count 2
