import asyncio
from fastapi import WebSocket, HTTPException, WebSocketDisconnect
from messaging import rabbitmq_consumer, rabbitmq_producer

class AgentManager:
    '''
    redis 사용 고려
    '''
    def __init__(self):
        pass


    def set_producer(self, producer):
        self.producer: rabbitmq_producer.MessageProducer = producer
    
    def set_consumer(self, consumer):
        self.consumer: rabbitmq_consumer.MessageConsumer = consumer
