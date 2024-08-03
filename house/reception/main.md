```python
@asynccontextmanager
async def lifespan():

    @asynccontextmanager는 비동기 컨텍스트 관리자 생성기 함수입니다.
    비동기 컨텍스트 관리자 함수는 yield를 사용하여 진입 및 종료 지점을 정의합니다.
    @asynccontextmanager 데코레이터를 사용한 lifespan 함수는 
    FastAPI 애플리케이션의 수명 주기 동안 특정 작업을 수행하기 위해 사용됩니다.
    @asynccontextmanager를 사용하여 lifespan 함수를 정의할 때, 
    yield를 사용하면 함수의 앞부분은 애플리케이션이 시작될 때 실행되고,
    yield 다음에 오는 코드는 애플리케이션이 종료될 때 실행됩니다.


task1.cancel()
task2.cancel()
try:
    await task1
    await task2
except asyncio.CancelledError:
    pass
 
    비동기 태스크를 cancel() 메서드를 통해 취소하면, 
    asyncio.CancelledError 예외가 발생하며 태스크가 종료됩니다. 
    그러나, 태스크가 즉시 종료되는 것은 아니며, 
    태스크 내부에서 이 예외를 처리하고 필요한 정리 작업을 할 수 있도록 시간을 줍니다.
    예를 들어, 파일 닫기, 데이터베이스 연결 종료, 네트워크 연결 정리 등이 필요할 수 있습니다.

    await task를 사용하여 태스크가 완전히 종료될 때까지 기다리면, 
    태스크가 제대로 종료되고 모든 리소스가 해제되었는지 확인할 수 있습니다.

    태스크가 취소되면 asyncio.CancelledError 예외가 발생합니다.
    await task와 함께 try-except 블록을 사용하면 이 예외를 명시적으로 처리할 수 있습니다. 
    이를 통해 예외 상황에서도 애플리케이션이 안정적으로 종료될 수 있습니다.
    만약 await task를 사용하지 않으면, 태스크가 제대로 종료되지 않은 상태에서 애플리케이션이 종료될 수 있으며, 
    이는 리소스 누수나 다른 문제를 초래할 수 있습니다.