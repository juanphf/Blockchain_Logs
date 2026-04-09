import os
from dotenv import load_dotenv
import random

load_dotenv()

# --- Configurações do Kafka ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_LOGS = os.getenv("TOPIC_LOGS", "audit_logs")
TOPIC_BLOCKS = os.getenv("TOPIC_BLOCKS", "new_blocks")
TOPIC_PINGS = os.getenv("TOPIC_PINGS", "network_pings")

# Identidade Global do Nó
NODE_ID = os.getenv("KAFKA_GROUP_ID", f"node_{random.randint(1000, 99999)}")
NODE_PORT = int(os.getenv("NODE_PORT", 5000))
# URL que este nó usa para ser acessado pelos outros na hora de sincronizar a rede
NODE_API_URL = os.getenv("NODE_API_URL", f"http://localhost:{NODE_PORT}")

# --- Segurança e Consenso (Proof of Authority) ---
# Lista de Chaves Públicas autorizadas separadas por vírgula. 
# Se estiver vazia, aceita qualquer um (apenas para testes).
WHITELIST_STR = os.getenv("WHITELIST", "")
ALLOWED_NODES = [key.strip() for key in WHITELIST_STR.split(",")] if WHITELIST_STR else []

def get_consumer_config(group_id=None):
    if group_id is None:
        group_id = NODE_ID
    return {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': group_id,
        'auto.offset.reset': 'latest' 
    }

def get_producer_config():
    return {
        'bootstrap.servers': KAFKA_BROKER
    }