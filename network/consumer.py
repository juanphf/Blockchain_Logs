import json
import traceback
from confluent_kafka import Consumer, KafkaError
from network.config import get_consumer_config, TOPIC_LOGS, TOPIC_PINGS

class AuditConsumer:
    def __init__(self, blockchain_instance):
        """
        Inicia o consumidor atrelando-o à instância local da blockchain.
        """
        self.blockchain = blockchain_instance
        self.consumer = Consumer(get_consumer_config())
        self.running = False

    def start(self, on_log_received=None, on_block_mined=None, on_ping_received=None):
        """
        Inicia o loop infinito de escuta do Kafka.
        Os callbacks servem para enviar dados ao Front-end em tempo real.
        """
        self.consumer.subscribe([TOPIC_LOGS, TOPIC_PINGS])
        self.running = True
        
        print(f"[*] Consumidor iniciado. Ouvindo o tópico: {TOPIC_LOGS}")

        try:
            while self.running:
                # Evita que a Thread morra em silêncio
                try: 
                    msg = self.consumer.poll(timeout=1.0)

                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        else:
                            print(f"[Erro Kafka] {msg.error()}")
                            break

                    topic = msg.topic()
                    payload = json.loads(msg.value().decode('utf-8'))
                    
                    if topic == TOPIC_PINGS:
                        if on_ping_received:
                            on_ping_received(payload)
                        continue
                        
                    # --- ABAIXO: Lógica para logs ---
                    log_data = payload
                    
                    # Notifica o servidor web para avisar o Front 
                    if on_log_received:
                        on_log_received(log_data)

                    # Envia para a Blockchain processar a regra de negócio e auditoria
                    block_closed = self.blockchain.add_log(log_data)

                    # Se a adição desse log fechou um bloco de 10, avisa o Front
                    if block_closed and on_block_mined:
                        last_block = self.blockchain.get_latest_block()
                        on_block_mined(last_block)

                except Exception as e:
                    print(f"\n[!!!] ERRO FATAL NA THREAD DO CONSUMIDOR: {e}")
                    traceback.print_exc() 
                    break # Interrompe o loop em caso de erro crítico

        except KeyboardInterrupt:
            print("\n[!] Encerrando consumidor...")
        finally:
            self.consumer.close()

    def stop(self):
        """Para o loop de escuta do consumidor."""
        self.running = False