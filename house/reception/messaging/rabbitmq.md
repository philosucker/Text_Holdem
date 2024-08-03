```python


connection = await aio_pika.connect_robust("amqp://admin:1867350@localhost:5672/")
async with connection:
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    '''
    aio_pika.connect_robust() :
        이 함수는 지정된 URL을 사용하여 RabbitMQ 서버에 비동기적으로 연결합니다.
        connect_robust()는 자동 재연결 기능을 포함한 연결을 제공합니다. 
        즉, 연결이 끊어졌을 때 자동으로 다시 연결을 시도합니다.

    async with connection :
        async with 구문은 비동기 컨텍스트 매니저를 사용하여 연결이 끝난 후에 리소스를 자동으로 정리합니다. 
        이 경우, RabbitMQ 연결을 안전하게 닫기 위한 용도로 사용됩니다.

    channel = await connection.channel() :
        연결된 RabbitMQ 서버에서 새 채널을 엽니다. 채널은 RabbitMQ와의 메시지 전송 작업을 수행하는 데 사용됩니다. 
            채널(Channel):
                하나의 연결(Connection) 내에서 여러 개의 채널을 열 수 있습니다.
                각 채널은 독립적으로 큐를 선언하고, 메시지를 전송하거나 수신할 수 있습니다.
                채널을 사용하는 이유는 성능을 최적화하고, 연결 내에서의 자원 사용을 줄이기 위함입니다.
                
            큐(Queue):
                채널은 여러 개의 큐를 선언하고 사용할 수 있습니다.
                큐는 메시지를 보관하는 논리적 공간이며, 특정 라우팅 키(routing key)나 교환(exchange)과 함께 사용됩니다.
                메시지 프로듀서(Producer)는 큐에 메시지를 전송하고, 메시지 소비자(Consumer)는 큐에서 메시지를 수신합니다.

    channel.set_qos(prefetch_count=1) :
        prefetch_count = 소비자가 한 번에 받아서 처리할 수 있는 메시지의 최대 수를 제한합니다.
        기능:
        이 값이 클수록 소비자는 더 많은 메시지를 한 번에 받아올 수 있습니다. 
        이는 메시지 처리의 효율성을 높일 수 있지만, 
        너무 높게 설정하면 한 소비자가 과도한 메시지를 받아 다른 소비자들에게 메시지가 전달되지 않을 수 있습니다.
        설정한 prefetch_count의 범위 내에서 메시지를 받아오며, 
        소비자가 메시지를 처리한 후에 새로운 메시지를 받을 수 있습니다.
        하나의 채널에서 여러 큐를 사용할 때 set_qos를 설정하면, 
        그 채널에서 소비하는 모든 큐에 동일한 prefetch_count가 적용됩니다

        각 큐에 대해 별도의 채널을 사용하여 각 채널에 다른 prefetch_count를 설정할 수 있습니다. 
        이를 통해 각 큐에 대한 메시지 소비를 독립적으로 조절할 수 있습니다.
        큐마다 prefetch를 다르게 설정하는 것은 유연하게 시스템 리소스를 관리하고, 
        우선순위가 높은 작업에 더 많은 리소스를 할당하는 데 유용합니다.
        하지만, prefetch 설정은 신중하게 고려해야 합니다. 
        너무 낮으면 시스템 자원이 유휴 상태가 될 수 있고, 
        너무 높으면 한 소비자가 과도한 메시지를 가져와 다른 큐의 처리가 지연될 수 있습니다.

        channel.set_qos(prefetch_count=1)는 주로 메시지를 소비할 때, 
        즉 수신 측에서 메시지를 처리할 때 사용됩니다. 
        따라서, 송신 측 코드에서는 channel.set_qos를 설정할 필요가 없습니다.

    채널을 여러 작업에 동시에 사용하는 경우, 
    특히 수신과 송신을 동일한 채널에서 처리하는 경우 
    다음과 같은 문제가 발생할 수 있습니다:

    데드락과 경합: 
    동일한 채널에서 송신과 수신이 동시에 발생하면, 
    리소스 경합이 발생할 수 있으며, 이로 인해 데드락이나 성능 저하가 발생할 수 있습니다.
    복잡성 증가: 
    코드의 복잡성이 증가하고, 버그 발생 가능성이 높아집니다. 
    예를 들어, 채널에서 처리해야 할 작업이 늘어나면 문제가 발생할 수 있습니다.
    따라서, 일반적으로는 송신과 수신을 별도의 채널에서 처리하는 것이 좋습니다. 
    이는 각각의 채널이 독립적으로 동작하고, 서로의 작업에 영향을 미치지 않도록 하기 위함입니다.
    '''


'''
RabbitMQ 서버에서는 큐(queue)를 통해 메시지를 송수신합니다.
RabbitMQ에서 메시지를 전송하고 수신할 때,
송신 측과 수신 측이 동일한 큐 이름을 사용해야 합니다. 이는 다음과 같은 이유 때문입니다:

큐의 일관성: 송신 측에서 메시지를 특정 큐로 전송하면, 
수신 측에서도 동일한 큐를 사용하여 메시지를 소비할 수 있어야 합니다. 
그렇지 않으면, 송신된 메시지를 수신 측에서 받을 수 없습니다.

큐 이름 매칭: RabbitMQ는 큐 이름을 기반으로 메시지를 전송하므로, 
동일한 이름의 큐를 선언해야 합니다. 
예를 들어, 송신 측에서 request_stack_size_queue라는 큐로 메시지를 전송하면, 
수신 측에서도 동일한 이름의 큐를 선언하고 소비해야 합니다.


RabbitMQ에서는 메시지가 큐에 직접 전송되지 않고, 교환기(Exchange)를 통해 라우팅됩니다. 
default_exchange는 RabbitMQ에서 기본으로 제공하는 익명 교환기입니다.
이 교환기는 큐 이름을 라우팅 키로 사용하여 메시지를 큐에 직접 전달합니다. 
따라서 routing_key=queue.name을 사용하여 메시지를 특정 큐로 라우팅합니다.
 
'''


update_stack_size_queue = await channel.declare_queue(
    "update_stack_size_queue", 
    durable=True,
    arguments={"x-max-priority": 1}  # 우선순위 큐 설정
)
    '''
    x-max-priority : 큐에 들어오는 메시지의 우선순위를 설정합니다.
    기능:
    RabbitMQ의 우선순위 큐는 메시지에 우선순위를 부여하여 높은 우선순위의 메시지가 먼저 소비되도록 합니다.
    '''


await request_stack_size_queue.consume(process_request_stack_size, no_ack=False)
    '''
    consume 메서드는 self.process_stk_size_query 함수에 메시지를 자동으로 전달합니다. 
    aio_pika 라이브러리의 consume 메서드는 내부적으로 메시지를 콜백 함수에 전달하도록 설계되어 있습니다.

    no_ack=False는 RabbitMQ가 각 메시지를 소비한 후, 
    수신 측 함수에서 해당 메시지를 처리한 후 
    Acknowledgment를 RabbitMQ에 보내야 함을 의미합니다.
    수신 측 함수의 async with message.process() 블록이 종료될 때 이를 자동으로 수행합니다. 
    수신된 메시지를 처리하는 함수에서 수신 메시지를 받는 aio_pika의 IncomingMessage 객체는 컨텍스트 매니저를 제공하며, 
    이를 통해 메시지를 처리한 후 자동으로 Acknowledgment를 보내거나, 
    필요에 따라 메시지를 NACK(Not Acknowledged) 처리할 수 있습니다.
    '''

try:
    await asyncio.Future()
finally:
    await connection.close()                  
    '''
    await asyncio.Future()는 무한 대기를 의미하며, 
    프로그램이 종료되지 않고 계속 실행되도록 유지합니다. 
    여기서는 메시지 소비 작업을 계속해서 대기하는 역할을 합니다.

    async with 블록이 끝날 때 자동으로 RabbitMQ 연결을 닫지만, 
    connection.close()를 호출하여 연결을 명시적으로 리소스를 해제하는 것은 좋은 습관입니다. 
    이를 통해 코드가 예상치 못한 방식으로 동작하지 않도록 보장할 수 있습니다.
    '''

async def process_request_stack_size(message: aio_pika.IncomingMessage):

    async with message.process():
        table_info = json.loads(message.body)
        # table_info = {"table_id" : str, "user_nick_list" : []}
        db = await connection.get_db().__anext__()
        nick_stk_dict = await message_service.request_stack_size(table_info, db)
        response = {
            "table_id": table_info["table_id"],
            "nick_stk_dict": nick_stk_dict
        }
        await rabbitmq_producer.send_message("request_stack_size_queue", response, priority=10)
    '''
    수신된 메시지를 처리하는 수신 측 함수인 process_request_stack_size 함수는 
    메시지가 request_stack_size_queue에 도착할 때마다 호출되는 콜백 함수의 역할을 합니다.

    함수에서 message는  RabbitMQ 큐로부터 수신한 메시지를 나타내는 aio_pika.IncomingMessage 객체입니다. 
    이 객체는 송신 측에서 보낸 실제 메시지의 내용을 포함하고 있으며, 메시지의 헤더, 본문, 속성 등의 정보를 담고 있습니다.

    message 객체의 역할
    메시지 본문 (message.body): 실제로 송신 측에서 보낸 데이터가 바이너리 형식으로 저장되어 있습니다. 
    예를 들어, JSON 형식으로 보낸 데이터가 여기 담길 수 있습니다.
    메시지 처리: message.process()를 통해 메시지에 대한 자동 Acknowledgment를 처리합니다. 
    이 구문을 사용하면 메시지가 제대로 처리되었을 때 RabbitMQ에 자동으로  Acknowledgment를 보냅니다.
    메시지 속성 및 헤더: message.headers, message.properties와 같은 속성을 통해 메시지의 메타데이터에 접근할 수 있습니다.


    async with message.process(): 구문은 메시지를 처리하는 동안 Acknowledgment가 필요함을 명시합니다. 
    이 구문 안에서 다음 작업이 이루어집니다:
    메시지 잠금: RabbitMQ는 이 메시지를 다른 소비자에게 전달하지 않습니다.
    예외 처리: 메시지 처리 중 예외가 발생하면, message.reject() 또는 message.nack()을 호출할 수 있습니다.
    정상 처리: 블록이 정상적으로 종료되면 message.ack()가 호출되어 Acknowledgment가 RabbitMQ로 전송됩니다. 
    이는 메시지가 성공적으로 처리되었음을 RabbitMQ에 알립니다. 이 설정은 메시지가 확실히 처리되었음을 보장할 수 있습니다.
    '''


