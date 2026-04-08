# Blockchain para Auditoria de Logs (Backend)

> **Em desenvolvimento:** A documentação completa sobre a arquitetura do projeto, fluxo de consenso e integração com o Front-end será adicionada nesta seção em breve.

## 🚀 Como Rodar o Projeto Localmente

Este repositório contém o Core da Blockchain, a API (FastAPI), a infraestrutura de mensageria (Kafka via Docker) e o simulador de microsserviços.

### Pré-requisitos
* **Python 3.10+** instalado.
* **Docker Desktop** instalado e rodando.

### Passo a Passo

**1. Preparar o ambiente Python**
No terminal do seu projeto, crie e ative um ambiente virtual, depois instale as dependências:
```bash
python -m venv venv
source venv/Scripts/activate  # (No Windows/Git Bash)
pip install -r requirements.txt
```

**2. Subir a Infraestrutura (Kafka)**
Com o Docker Desktop aberto, inicie o barramento de eventos:
```bash
docker compose up -d
```
*(Aguarde o contêiner kafka-node ficar com o status "Running" no Docker).*

**3. Ligar o Nó da Blockchain (API)**
No seu terminal (com o venv ativado), inicie o servidor web. Ele rodará na porta 5000 e ativará o consumidor do Kafka em segundo plano:
```bash
python -m network.api
```

**4. Iniciar a Simulação (Gerador de Logs)**
Abra um **segundo terminal** no VS Code, ative o ambiente virtual novamente e ligue o gerador:
```bash
source venv/Scripts/activate
python log_generator.py
```

Neste momento, o terminal do Gerador começará a enviar logs assinados criptograficamente, e o terminal da API começará a validar os logs e selar os blocos de auditoria em tempo real.