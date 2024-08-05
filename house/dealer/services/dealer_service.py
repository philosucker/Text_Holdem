import asyncio
from fastapi import WebSocket


from messaging import rabbitmq_consumer, rabbitmq_producer
from ..core import dealer

class DealerManager:

    def __init__(self):

        self.active_connections: dict[str, dict[str, WebSocket]] = {}
        self.dealer_instances : dict[str, dealer.Dealer] = {}
        self.tables_info :dict[str, dict]= {}

        self.producer = None 
        self.consumer = None
        self.table_queue = asyncio.Queue()

    def set_producer(self, producer):
        self.producer: rabbitmq_producer.MessageProducer = producer
    
    def set_consumer(self, consumer):
        self.consumer: rabbitmq_consumer.MessageConsumer = consumer

    async def add_connection(self, table_id: str, client_id: str, websocket: WebSocket): # from dealer_router
        if table_id not in self.active_connections:
            self.active_connections[table_id] = {}
        if client_id not in self.active_connections[table_id]:
            self.active_connections[table_id][client_id] = websocket
        self.active_connections[table_id][client_id] = websocket 
        if table_id in self.dealer_instances:
            dealer_instance = self.dealer_instances[table_id]
            dealer_instance.reconnection_handler({client_id : websocket})
                
    async def table_loop(self):
        while True:
            
            # 큐가 비어 있으면, inbox에 메시지가 들어올 때까지 대기 
            data = await self.consumer.table_ready_inbox.get()
            '''
            data = {
            "table_id" : str
            "rings" : int
            "stakes" : str
            new_players : dict[str, int]  # {"nick_4" : 1000, "nick_5": 800, "nick_6" : 1500}
            continuing_players : dict[str, int]  # {"nick_1" : 100, "nick_2": 2000, "nick_3" : 500}
            determined_positions : dict[str, str] # {"nick_1" : "BB", "nick_2": "CO", "nick_3" : D}
            }
            '''
            table_id = data["table_id"]
            connections = self.active_connections.get(table_id, {})
            '''
            table_ready 메시지는 왔으나 웹소켓 연결이 불완전한 경우 floor로 돌려보낸다.
            아니면 await self.consumer.table_ready_inbox.put(data)를 해야할까..
            '''
            if not connections:
                await self.producer.table_failed(data)
                continue
            elif len(connections) != (len(data["new_players"]) + len(data["continuing_players"])):
                valid_keys = connections.keys()
                data["new_players"] = {k: v for k, v in data["new_players"].items() if k in valid_keys}
                data["continuing_players"] = {k: v for k, v in data["continuing_players"].items() if k in valid_keys}
                data["determined_positions"] = {k: v for k, v in data["determined_positions"].items() if k in valid_keys}
                await self.producer.table_failed(data)
                continue
            
            self.tables_info[table_id] = data
            table_info = self.tables_info[table_id]
            dealer_instance = dealer.Dealer(table_info, connections)
            self.dealer_instances[table_id] = dealer_instance
            task = asyncio.create_task(await dealer_instance.go_street())
            await self.table_queue.put(task)
            await asyncio.sleep(0.5)
            
    async def result_processor(self):
        while True:
            # 큐에서 완료된 작업을 가져와 결과를 처리
            task = await self.table_queue.get()
            result = await task 
            await self.producer.game_log(result) 
            
            dealer_instance = self.dealer_instances.pop(result["table_id"], None)
            if dealer_instance:
                for websocket in self.active_connections["table_id"].values():
                    websocket.close()
                del self.tables_info["table_id"]
                del self.active_connections["table_id"]
            await asyncio.sleep(0.5)
