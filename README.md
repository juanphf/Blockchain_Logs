# Blockchain para Auditoria de Logs (Permissioned)

## 📌 Sobre o Projeto
Este é um sistema de auditoria de logs baseado em uma **Blockchain Permissionada**, projetado para garantir a integridade, imutabilidade e rastreabilidade de eventos críticos em microsserviços. 

O sistema utiliza um mecanismo de consenso **Proof-of-Authority (PoA)** e integra uma infraestrutura de mensageria descentralizada via **Kafka** para gerenciar a mempool de logs e realizar a descoberta dinâmica de nós na rede P2P através de heartbeats.

## 🏗 Arquitetura
A aplicação é dividida nos seguintes componentes principais:
* **Core da Blockchain:** Implementação da estrutura de blocos, criptografia (hashes SHA-256), validação e selagem de blocos via PoA.
* **Rede P2P & Mensageria:** Utiliza Apache Kafka para sincronização do ledger, propagação da mempool de logs e emissão de heartbeats, permitindo a descoberta em tempo real de nós ativos e sincronização de dados.
* **API de Nós (FastAPI):** Cada nó roda um servidor web independente e um consumidor Kafka em background.
* **Frontend Dashboard:** Uma interface web moderna com suporte a painel em tempo real, renderizando os blocos selados, transações da mempool e status dos nós conectados sem duplicação.
* **Simuladores de Logs e Ataques:** Scripts (`log_generator.py`, `attack_1_fake_log.py`, `attack_2_rewrite_history.py`, `malicious_injector.py`) para simular o comportamento normal de microsserviços e testar a resiliência da rede contra logs inválidos ou tentativas de adulteração do histórico.

## 🔐 Segurança e Consenso (PoA)
- **Proof-of-Authority (PoA):** Apenas nós autorizados (identificados criptograficamente) podem selar blocos. A rede resolve concorrências (race conditions) rejeitando blocos órfãos ou duplicados.
- **Assinatura de Logs:** Cada log gerado possui uma assinatura digital. Tentativas de forjar logs geram falhas de validação, que são monitoradas na dashboard.
- **Imutabilidade:** O histórico não pode ser reescrito sem quebrar a cadeia de hashes, uma tentativa que é rapidamente isolada e rejeitada pela rede durante a sincronização.

## 🚀 Como Rodar o Projeto Localmente

### Pré-requisitos
* **Python 3.10+** instalado.
* **Docker Desktop** (ou docker engine) instalado e rodando.

### Passo a Passo

**1. Preparar o ambiente Python**
No terminal do seu projeto, crie e ative um ambiente virtual, depois instale as dependências:
```bash
python -m venv venv
# No Linux/Mac:
source venv/bin/activate
# No Windows/Git Bash:
source venv/Scripts/activate  

pip install -r requirements.txt
```

**2. Subir a Infraestrutura (Kafka)**
Com o Docker Desktop aberto, inicie o barramento de eventos:
```bash
docker compose up -d
```
*(Aguarde o contêiner de Kafka ficar com o status "Running" no Docker).*

**3. Ligar o Nó da Blockchain (API)**
No seu terminal (com o venv ativado), inicie a aplicação base (servidor web e consumidor Kafka em segundo plano):
```bash
python -m network.api
```

**4. Iniciar o Frontend Dashboard**
Abra o arquivo `frontend/index.html` em seu navegador para visualizar a rede em tempo real, monitorar os nós ativos e acompanhar a formação da blockchain.

**5. Iniciar a Simulação (Gerador de Logs)**
Abra um **segundo terminal**, ative o ambiente virtual novamente e ligue o gerador de eventos normais:
```bash
source venv/bin/activate  # ou venv/Scripts/activate no Windows
python log_generator.py
```
Neste momento, o terminal do Gerador começará a enviar logs assinados criptograficamente, e a rede P2P começará a validar os logs e selar os blocos de auditoria em tempo real, refletindo diretamente no Frontend.

**6. Simulação de Ataques (Opcional)**
Você pode testar a resiliência da blockchain rodando os scripts de ataque em terminais paralelos:
```bash
python attack_1_fake_log.py
python attack_2_rewrite_history.py
```
O sistema irá detectar, rejeitar e evidenciar no frontend as tentativas de fraude.