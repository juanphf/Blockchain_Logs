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


def get_consumer_config(group_id="blockchain_node_1"):
    """
    Retorna o dicionário de configuração padrão para um Consumidor Kafka.
    O group_id define quem está lendo. Nós diferentes devem ter group_ids diferentes
    se quiserem ler todas as mensagens.
    """
    if group_id is None:
        group_id = f"blockchain_node_{random.randint(1000, 99999)}"
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