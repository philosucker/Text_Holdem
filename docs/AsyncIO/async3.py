import asyncio

async def main(f: asyncio.Future):
    await asyncio.sleep(1)
    f.set_result(("I Have finished"))

loop = asyncio.get_event_loop()

future = asyncio.Future() # 이 인스턴스는 기본적으로 loop에 연결되지만
# 어떠한 코루틴에도 연결되지 않았고 연결되지도 않는다
print(future.done()) # future인스턴스에는 done이라는 메서드가 있어 상태를 확인할 수 있다

# loop.create_task(main(future)) # main() 코루틴을 스케쥴링한다. 
fut = loop.create_task(main(future)) # main() 코루틴을 스케쥴링한다. 
# 동시에 future 인스턴스르 매개변수로 전달한다
# main 코루틴이 하는 일은 잠깐 자고 일어나서 futue 인스턴스의 상태를 변경하는 것이다
# loop.run_until_complete(future) # task 인스턴스가 아닌 future 인스턴스에 대해 run_until_complete를 사용한다
loop.run_until_complete(fut) # task 인스턴스가 아닌 future 인스턴스에 대해 run_until_complete를 사용한다
print(future.done())
print(future.result())