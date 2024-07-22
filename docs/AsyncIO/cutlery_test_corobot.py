# Example B-1. Cutlery management using asyncio
import sys
import asyncio
from attr import attrs, attrib


# Instead of a ThreadBot, we now have a CoroBot. 
# This code sample uses only one thread, 
# and that thread will be managing all 10 separate CoroBot object instances
# one for each table in the restaurant.
class CoroBot():
    def __init__(self):
        self.cutlery = Cutlery(knives=0, forks=0)
        # Instead of queue.Queue, we’re using the asyncio enabled queue.
        self.tasks = asyncio.Queue()

    async def manage_table(self):
        while True:
            task = await self.tasks.get() # 여기가 중요한 부분이다
            # 서로 다른 CoroBot 인스턴스 간에 컨텍스트 전환을 할 수 있는 유일한 위치는
            # 바로 await 키워드가 있는 곳이다.
            # 이 함수의 나머지 부분에서는 컨텍스트 전환이 일어날 수 없다
            # 이로 인해 주방 식기 재고를 수정할 때 Race Condition이 발생하지 않는다
            # await 키워드가 있는 곳에서만 컨텍스트 전환이 일어나므로 관측가능하다
            # 이를 통해 병행 애플리케이션에서 경합조건의 가능성을 훨씬 쉽게 유추할 수 있다
            if task == 'prepare table':
                kitchen.give(to=self.cutlery, knives=4, forks=4)
            elif task == 'clear table':
                self.cutlery.give(to=kitchen, knives=4, forks=4)
            elif task == 'shutdown':
                return

@attrs
class Cutlery:
    knives = attrib(default=0)
    forks = attrib(default=0)

    def give(self, to: 'Cutlery', knives=0, forks=0):
        self.change(-knives, -forks)
        to.change(knives, forks)

    def change(self, knives, forks):
        self.knives += knives
        self.forks += forks


kitchen = Cutlery(knives=100, forks=100)
bots = [CoroBot() for i in range(10)]

for b in bots:
    for i in range(int(sys.argv[1])):
        b.tasks.put_nowait('prepare table')
        b.tasks.put_nowait('clear table')
    b.tasks.put_nowait('shutdown')
print('Kitchen inventory before service:', kitchen)

loop = asyncio.get_event_loop()
tasks = []
for b in bots:
    t = loop.create_task(b.manage_table())
    tasks.append(t)

task_group = asyncio.gather(*tasks)
loop.run_until_complete(task_group)
print('Kitchen inventory after service:', kitchen)


# 터미널 실행 코드
# python cutlery_test_corobot.py 100000

