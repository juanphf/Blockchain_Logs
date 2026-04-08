import asyncio
import threading
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from dotenv import load_dotenv

# Importando o seu Core e o seu Consumer
from core.blockchain import Blockchain
from network.consumer import AuditConsumer

load_dotenv()

blockchain = Blockchain()

# Lista para guardar todos os painéis que estiverem com a tela aberta
connected_clients = set()
# Variável global para guardar o motor assíncrono do servidor web
server_loop = None 

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
            on_block_mined=handle_block_mined
        )

    # Inicia a thread em segundo plano
    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    
    yield # O servidor web fica rodando enquanto estiver nesse 'yield'
    
    # O servidor passa por aqui para desligar limpo
    print("\n[*] Desligando a API e o Consumidor...")
    consumer.stop()


# --- INICIALIZAÇÃO DA API ---
app = FastAPI(title="Nó da Blockchain de Auditoria", lifespan=lifespan)

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