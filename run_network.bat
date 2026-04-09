@echo off
echo [*] Iniciando a Rede Blockchain com 4 Nos...

start cmd /k "call venv\Scripts\activate && set NODE_PORT=5000 && python -m network.api"
start cmd /k "call venv\Scripts\activate && set NODE_PORT=5001 && python -m network.api"
start cmd /k "call venv\Scripts\activate && set NODE_PORT=5002 && python -m network.api"
start cmd /k "call venv\Scripts\activate && set NODE_PORT=5003 && python -m network.api"

echo [*] Todos os 4 nos estao rodando em terminais separados!