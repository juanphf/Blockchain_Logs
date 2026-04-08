import os
from dotenv import load_dotenv
import random

load_dotenv()

# --- Configurações do Kafka ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# Tópico onde os logs soltos chegam
TOPIC_LOGS = os.getenv("TOPIC_LOGS", "audit_logs")

# Tópico onde os blocos fechados são transmitidos para a rede
TOPIC_BLOCKS = os.getenv("TOPIC_BLOCKS", "new_blocks")

# Tópico de Pulsação de Vida (Heartbeat)
TOPIC_PINGS = os.getenv("TOPIC_PINGS", "network_pings")

# Identidade Global do Nó 
NODE_ID = os.getenv("KAFKA_GROUP_ID", f"blockchain_node_{random.randint(1000, 99999)}")


def get_consumer_config(group_id=None):
    """
    Retorna o dicionário de configuração padrão para um Consumidor Kafka.
    O group_id define quem está lendo. Nós diferentes devem ter group_ids diferentes
    se quiserem ler todas as mensagens.
    """
    if group_id is None:
        # Se não configurou um ID, pega o fixo global
        group_id = NODE_ID
    return {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': group_id,
        'auto.offset.reset': 'earliest' 
    }


def get_producer_config():
    """
    Retorna o dicionário de configuração padrão para um Produtor Kafka.
    """
    return {
        'bootstrap.servers': KAFKA_BROKER
    }