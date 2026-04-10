import asyncio
import random
import threading
import os
import json
import time
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.blockchain import Blockchain
from network.consumer import AuditConsumer
from network.config import get_producer_config, TOPIC_PINGS, TOPIC_BLOCKS, NODE_ID, NODE_API_URL, NODE_PORT
from confluent_kafka import Producer

blockchain = Blockchain()
producer = Producer(get_producer_config())

connected_clients = set()
server_loop = None 
active_nodes = {}

# --- CALLBACKS E SINCRONIZAÇÃO ---
def notify_clients(message_dict):
    if server_loop is None: return
    for client in list(connected_clients):
        try:
            asyncio.run_coroutine_threadsafe(client.send_json(message_dict), server_loop)
        except Exception:
            pass

def handle_new_log(log_data):
    notify_clients({"type": "NEW_LOG", "data": log_data})

def handle_block_mined(block, broadcast=False):
    """Avisa o Front que um bloco foi fechado e transmite para a rede se fomos o minerador."""
    notify_clients({"type": "NEW_BLOCK", "data": block.to_dict()})
    
    if broadcast:
        print("[*] Transmitindo novo bloco para a rede Kafka...")

        time.sleep(random.uniform(0.01, 0.15))
        
        producer.produce(
            TOPIC_BLOCKS, 
            key="consensus", 
            value=json.dumps(block.to_dict()).encode('utf-8')
        )
        producer.flush()

def handle_sync_needed(peer_api_url):
    """Outro nó avisou via Ping que tem uma cadeia maior. Vamos baixar."""
    if not peer_api_url or peer_api_url == NODE_API_URL: return
    try:
        print(f"[*] Rede mais avançada detectada. Sincronizando com {peer_api_url}...")
        response = requests.get(f"{peer_api_url}/blocks", timeout=5)
        if response.status_code == 200:
            external_chain = response.json()
            updated = blockchain.replace_chain(external_chain)
            if updated:
                # Se atualizou com sucesso, notifica o front-end
                chain_data = [b.to_dict() for b in blockchain.chain]
                notify_clients({"type": "CHAIN_HISTORY", "data": chain_data})
    except Exception as e:
        print(f"[X] Falha ao sincronizar com {peer_api_url}: {e}")

def handle_ping(ping_data):
    node_id = ping_data.get("node_id")
    if not node_id: return
    
    active_nodes[node_id] = time.time()
    current_time = time.time()
    for nid in list(active_nodes.keys()):
        if current_time - active_nodes[nid] > 12:
            del active_nodes[nid]
            
    notify_clients({"type": "NODE_COUNT", "data": len(active_nodes)})


# --- GERENCIADOR DE CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global server_loop
    server_loop = asyncio.get_running_loop() 
    consumer = AuditConsumer(blockchain)
    
    def run_consumer():
        consumer.start(
            on_log_received=handle_new_log,
            on_block_mined=handle_block_mined,
            on_ping_received=handle_ping,
            on_sync_needed=handle_sync_needed # Callback de Resolução de Conflitos
        )
        
    def run_pinger():
        print(f"[*] Moto de Coração ativo na URL: {NODE_API_URL}")
        while True:
            try:
                ping_payload = {
                    "node_id": NODE_ID, 
                    "api_url": NODE_API_URL,
                    "chain_length": len(blockchain.chain) # Envia o tamanho da cadeia
                }
                producer.produce(TOPIC_PINGS, value=json.dumps(ping_payload).encode('utf-8'))
                producer.poll(0)
            except Exception:
                pass
            time.sleep(5)

    threading.Thread(target=run_consumer, daemon=True).start()
    threading.Thread(target=run_pinger, daemon=True).start()
    
    yield 
    consumer.stop()

# --- INICIALIZAÇÃO DA API ---
app = FastAPI(title="Nó da Blockchain - PoA", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/blocks")
def get_blockchain():
    return [b.to_dict() for b in blockchain.chain]

@app.get("/mempool")
def get_mempool():
    return [log.to_dict() for log in blockchain.pending_logs]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        await websocket.send_json({"type": "CHAIN_HISTORY", "data": [b.to_dict() for b in blockchain.chain]})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

# --- EXECUÇÃO ---
if __name__ == "__main__":
    print(f"[*] Preparando inicialização na porta {NODE_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=NODE_PORT, access_log=False)