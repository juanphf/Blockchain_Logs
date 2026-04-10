import json
import traceback
from confluent_kafka import Consumer, KafkaError
from network.config import get_consumer_config, TOPIC_LOGS, TOPIC_PINGS, TOPIC_BLOCKS

class AuditConsumer:
    def __init__(self, blockchain_instance):
        self.blockchain = blockchain_instance
        self.consumer = Consumer(get_consumer_config())
        self.running = False

    def start(self, on_log_received=None, on_block_mined=None, on_ping_received=None, on_sync_needed=None):
        self.consumer.subscribe([TOPIC_LOGS, TOPIC_PINGS, TOPIC_BLOCKS])
        self.running = True
        
        print(f"[*] Consumidor iniciado. Ouvindo redes Kafka...")

        try:
            while self.running:
                try: 
                    msg = self.consumer.poll(timeout=1.0)
                    if msg is None: continue
                    if msg.error(): continue

                    topic = msg.topic()
                    payload = json.loads(msg.value().decode('utf-8'))
                    
                    if topic == TOPIC_PINGS:
                        if on_ping_received: on_ping_received(payload)
                        
                        # Verifica se o nó do ping tem uma corrente maior. Se sim, dispara sync.
                        peer_chain_length = payload.get("chain_length", 0)
                        if peer_chain_length > len(self.blockchain.chain) and on_sync_needed:
                            on_sync_needed(payload.get("api_url"))
                        continue

                    if topic == TOPIC_BLOCKS:
                        # Todos os nós validam o bloco vindo do Kafka, inclusive quem enviou. 
                        # O Kafka dita a ordem de chegada (Consenso determinístico)
                        accepted = self.blockchain.add_proposed_block(payload)
                        
                        if accepted and on_block_mined:
                            on_block_mined(self.blockchain.get_latest_block())
                        continue
                        
                    if topic == TOPIC_LOGS:
                        if on_log_received: on_log_received(payload)
                        
                        # add_log retorna um bloco se esse log engatilhou a selagem
                        new_block = self.blockchain.add_log(payload)
                        
                        # Se nós fechamos o bloco, avisamos o Front e devolvemos pra API transmitir a proposta
                        if new_block and on_block_mined:
                            on_block_mined(new_block, broadcast=True)

                except Exception as e:
                    traceback.print_exc() 
                    break 

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

    def stop(self):
        self.running = False