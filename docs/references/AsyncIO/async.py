import asyncio
import time

async def f():
    print(f'{time.ctime()} hello')
    await asyncio.sleep(3)
    print(f'{time.ctime()} good bye')
    

'''
대부분의 asyncio 기반 코드는 run() 함수를 사용한다
이 함수의 역할을 이해해야 큰 애플리케이션을 잘 설계할 수 있다
'''
# asyncio.run(f()) 

def blocking():
    time.sleep(5)
    print(f'{time.ctime()} hello from a thread')
'''
아래 코드는 run() 함수 내부의 거의 모든 동작에 대한 예제다.
'''
loop = asyncio.get_event_loop()
task = loop.create_task(f())

loop.run_in_executor(None, blocking)
loop.run_until_complete(task)

pending = asyncio.all_tasks(loop=loop)
for task in pending:
    task.cancel()
group = asyncio.gather(*pending, return_exceptions = True)
loop.run_until_complete(group)
loop.close()