import asyncio
import threading
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Importando o seu Core e o seu Consumer
from core.blockchain import Blockchain
from network.consumer import AuditConsumer
from network.config import get_producer_config, TOPIC_PINGS, NODE_ID
import json
import time

load_dotenv()

blockchain = Blockchain()

# Lista para guardar todos os painéis que estiverem com a tela aberta
connected_clients = set()
# Variável global para guardar o motor assíncrono do servidor web
server_loop = None 
active_nodes = {} # Guarda o timestamp do último ping de cada nó


# --- CALLBACKS DO KAFKA ---
def notify_clients(message_dict):
    """Envia uma mensagem JSON para todos os front-ends conectados via WebSocket."""
    if server_loop is None:
        return
        
    for client in list(connected_clients):
        try:
            asyncio.run_coroutine_threadsafe(client.send_json(message_dict), server_loop)
        except Exception:
            pass # Ignora se o cliente já tiver desconectado

def handle_new_log(log_data):
    """Avisa o Front que um novo log chegou e está na Mempool."""
    notify_clients({"type": "NEW_LOG", "data": log_data})

def handle_block_mined(block):
    """Avisa o Front que um bloco de 10 logs foi fechado (Cadeado)."""
    notify_clients({"type": "NEW_BLOCK", "data": block.to_dict()})

def handle_ping(ping_data):
    """Processa um sinal de vida recebido de qualquer nó na rede Kafka"""
    node_id = ping_data.get("node_id")
    if not node_id: return
    
    active_nodes[node_id] = time.time()
    
    # Prune (Poda) dos nós que não falam há mais de 12 segundos
    current_time = time.time()
    for nid in list(active_nodes.keys()):
        if current_time - active_nodes[nid] > 12:
            del active_nodes[nid]
            
    # Avisa o Front end qual a qtde atualizada (o front exibirá isso na tela)
    notify_clients({"type": "NODE_COUNT", "data": len(active_nodes)})


# --- GERENCIADOR DE CICLO DE VIDA  ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global server_loop
    # Captura o motor exato que o Uvicorn acabou de ligar
    server_loop = asyncio.get_running_loop() 
    
    consumer = AuditConsumer(blockchain)
    
    def run_consumer():
        print("[*] Iniciando a Thread do Consumidor Kafka...")
        consumer.start(
            on_log_received=handle_new_log,
            on_block_mined=handle_block_mined,
            on_ping_received=handle_ping
        )
        
    def run_pinger():
        from confluent_kafka import Producer
        producer = Producer(get_producer_config())
        print(f"[*] Moto de Coração ativo. Seu Nó é: {NODE_ID}")
        while True:
            try:
                # Grita para o Kafka a cada 5 segundos
                producer.produce(TOPIC_PINGS, value=json.dumps({"node_id": NODE_ID}).encode('utf-8'))
                producer.poll(0)
            except Exception:
                pass
            time.sleep(5)

    # Inicia as threads em segundo plano
    threading.Thread(target=run_consumer, daemon=True).start()
    threading.Thread(target=run_pinger, daemon=True).start()
    
    yield # O servidor web fica rodando enquanto estiver nesse 'yield'
    
    # O servidor passa por aqui para desligar limpo
    print("\n[*] Desligando a API e o Consumidor...")
    consumer.stop()


# --- INICIALIZAÇÃO DA API ---
app = FastAPI(title="Nó da Blockchain de Auditoria", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROTAS DA API ---
@app.get("/blocks")
def get_blockchain():
    """Retorna a cadeia de blocos inteira para o navegador"""
    return [b.to_dict() for b in blockchain.chain]

@app.get("/mempool")
def get_mempool():
    """Retorna os logs validados que estão na fila esperando para virar bloco"""
    return [log.to_dict() for log in blockchain.pending_logs]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """A porta de entrada para o React se conectar."""
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"[*] Novo Front-end conectado! Total: {len(connected_clients)}")
    
    try:
        chain_data = [b.to_dict() for b in blockchain.chain]
        await websocket.send_json({
            "type": "CHAIN_HISTORY", 
            "data": chain_data
        })
        
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("[*] Front-end desconectado.")

# --- EXECUÇÃO ---
if __name__ == "__main__":
    porta = int(os.getenv("NODE_PORT", 5000))
    print(f"[*] Preparando inicialização na porta {porta}...")
    uvicorn.run(app, host="0.0.0.0", port=porta)