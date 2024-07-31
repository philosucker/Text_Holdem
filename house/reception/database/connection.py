import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from database import manipulation
from dotenv import load_dotenv

load_dotenv(dotenv_path="./house/.env")


'''
DB_URL = "mysql+aiomysql://root@db:3306/demo?charset=utf8" # aiomysql 설치 후

DB_URL : SQLAlchemy가 데이터베이스에 연결할 때 사용할 URL입니다.
mysql+pymysql: SQLAlchemy와 pymysql을 사용하여 MySQL 데이터베이스에 연결한다는 의미입니다.
root: 데이터베이스의 사용자명입니다. 여기서는 비밀번호 없이 root 사용자로 연결합니다.
db: Docker Compose에서 정의된 MySQL 서비스의 이름입니다. 이는 Docker 네트워크 내에서의 호스트명입니다.
3306: MySQL의 기본 포트 번호입니다. # 호스트 머신의 33306번 포트를 도커의 3306번 포트에 연결했다.
demo: 연결할 데이터베이스의 이름입니다.
charset=utf8: 데이터베이스의 문자 인코딩을 UTF-8로 설정합니다.
'''

DATABASE_URL = os.getenv("SQL_USER_DATABASE_URL")

'''
create_engine(DB_URL, echo=True): SQLAlchemy 엔진을 생성합니다.
DB_URL: 앞서 정의한 데이터베이스 URL입니다.
echo=True: SQLAlchemy가 실행하는 SQL 쿼리를 로그로 출력합니다. 이는 디버깅에 유용합니다.

create_engine() : SQLModel은 SQLAlchemy 엔진을 사용해 데이터베이스를 연결합니다. 
이를 위해 create_engine() 메서드를 사용합니다.
create_engine()은 데이터베이스 URL을 인수로 사용합니다. 
URL은 sqlite:///database.db 또는 sqlite:///database.sqlite와 같은 형식입니다.
인자로 echo=True를 설정하면 실행된 SQL 명령이 출력됩니다.

SQLModel.metadata.create_all() : create_engine() 메서드만으로는 데이터베이스 파일을 만들 수 없습니다.
create_all() 메서드를 사용해 create_engine() 메서드의 인스턴스를 호출해야 합니다.
SQLModel.metadata.create_all(engine_url)을 호출할 때, 
SQLModel은 데이터베이스뿐만 아니라 현재 활성화된 모든 모델을 탐색하여 테이블을 생성합니다.
따라서 from models.events import Event를 하지 않아도 문제는 없습니다.
하지만 명시적으로 모델을 임포트하면, 
해당 모델이 반드시 포함된다는 보장을 얻을 수 있습니다. 
이는 특히 대규모 프로젝트에서 중요한 관례입니다.
'''

connect_args = {"check_same_thread": False}
'''
connect_args = {"check_same_thread": False} : 
SQLite 데이터베이스 연결 시 사용하는 인수로, 
동일한 스레드에서만 데이터베이스 연결을 사용할 수 있는 기본 동작을 무시하고 
다른 스레드에서도 동일한 연결을 사용할 수 있도록 허용합니다. 
이 설정은 SQLite를 사용하면서 FastAPI와 같은 비동기 웹 프레임워크에서 데이터베이스 연결을 공유해야 할 때 유용합니다.
'''
engine = create_async_engine(DATABASE_URL, echo=True)

'''
sessionmaker: 세션을 생성하는 팩토리입니다. 세션 객체를 만듭니다. 세션은 데이터베이스와의 상호작용을 위해 필요합니다.

    SQLAlchemy와 같은 ORM(Object-Relational Mapping) 라이브러리에서 세션(Session)은 
    데이터베이스 연결과 트랜잭션을 관리하는 역할을 합니다.
        세션(Session)의 역할
            연결 관리(Connection Management):
            세션은 데이터베이스와의 연결을 유지하고 관리합니다. 필요한 경우 데이터베이스 연결을 열고, 작업이 끝나면 연결을 닫습니다.
            
            객체 상태 관리(Object State Management):
            세션은 객체의 상태(새로 생성됨, 수정됨, 삭제됨)를 추적합니다. 이를 통해 변경된 내용을 데이터베이스에 커밋하거나 롤백할 수 있습니다.
            
            트랜잭션 관리(Transaction Management):
            세션은 트랜잭션을 관리합니다. 트랜잭션은 데이터베이스 작업의 논리적 단위로, 여러 작업을 하나의 단위로 묶어 관리합니다. 
            세션을 통해 트랜잭션을 시작하고, 커밋하거나 롤백할 수 있습니다.

    세션을 사용하여 데이터베이스에 객체를 추가하거나 변경할 수 있습니다. 예를 들어, 새로운 레코드를 추가하거나 기존 레코드를 수정할 수 있습니다.
    세션의 commit 메서드를 호출하여 변경 내용을 데이터베이스에 반영합니다. 이 시점에서 트랜잭션이 종료되고, 모든 변경 사항이 데이터베이스에 영구적으로 저장됩니다.
    오류가 발생하면 세션의 rollback 메서드를 호출하여 모든 변경 사항을 취소할 수 있습니다. 이는 트랜잭션이 시작된 이후의 모든 변경 사항을 무효화합니다.
    작업이 완료되면 세션을 종료합니다. 이는 세션이 사용하는 모든 리소스를 해제하고, 데이터베이스 연결을 닫습니다.
    
autocommit=False: 자동 커밋을 비활성화합니다. 이는 트랜잭션이 명시적으로 커밋될 때까지 데이터를 커밋하지 않습니다.
autoflush=False: 자동 플러시를 비활성화합니다. 이는 세션이 커밋되기 전에 변경된 객체를 데이터베이스에 자동으로 기록하지 않습니다.
bind=db_engine: 앞서 생성한 데이터베이스 엔진에 세션을 바인딩합니다.
'''

'''
세션은 데이터베이스와의 논리적인 연결로, 데이터베이스 작업을 그룹화하고 트랜잭션을 관리합니다.
세션은 데이터베이스에 대한 여러 작업(예: 쿼리, 삽입, 업데이트, 삭제)을 그룹화하고, 
이러한 작업들을 트랜잭션 단위로 처리할 수 있게 해줍니다.
    세션의 역할
    트랜잭션 관리: 세션은 트랜잭션을 관리합니다. 여러 SQL 명령어를 하나의 트랜잭션으로 묶어 데이터베이스 일관성을 유지할 수 있습니다.
    연결 관리: 세션은 데이터베이스 연결을 효율적으로 관리합니다. 필요한 경우 연결을 열고, 사용이 끝나면 닫습니다.
    변경 추적: 세션은 객체의 변경 사항을 추적하고, 이를 데이터베이스에 반영합니다.
    쿼리 실행: 세션을 통해 데이터베이스에 쿼리를 실행하고, 결과를 반환받을 수 있습니다.

Session 클래스는 SQL 엔진의 인스턴스(여기서는 engine_url)를 인수로 사용합니다.

세션 생성 및 사용: Session 클래스를 사용하여 세션을 생성하고, 
FastAPI 라우트 함수에서 Depends를 사용해 세션을 주입하여 데이터베이스 작업을 수행합니다.
    1. 의존성 주입 (Dependency Injection):
        Depends는 FastAPI에서 의존성을 주입하는 데 사용되는 함수입니다.
        Depends(get_session)를 사용하여 라우트 함수에 get_session을 의존성으로 주입합니다.
        FastAPI는 Depends를 통해 get_session 함수를 호출하고, 
        생성된 세션 객체를 라우트 함수의 인자로 전달합니다.

    2. 세션 주입:
        데이터베이스 세션을 라우트 함수에 주입합니다.
        세션은 데이터베이스와의 연결을 관리하며, 데이터베이스 작업(쿼리, 삽입, 삭제 등)을 수행할 수 있도록 합니다.
        각 라우트 함수(retrieve_all_events, create_event, delete_event)에서 
        session 인자를 사용하여 데이터베이스 작업을 수행합니다.
        예를 들어, retrieve_all_events 함수는 세션을 사용하여 이벤트 목록을 조회하고, 
        create_event 함수는 새로운 이벤트를 데이터베이스에 추가하며, 
        delete_event 함수는 특정 이벤트를 삭제합니다.

get_session 함수는 Session 객체를 생성하여 데이터베이스와의 세션을 관리합니다. 
create_engine()으로 생성된 engine_url을 Session 클래스의 인자로 사용하여 세션을 생성합니다. 
yield 키워드를 사용하여 생성된 세션을 반환하고, 세션의 생명주기가 끝나면 자동으로 세션을 닫습니다.

세션 클래스의 주요 메서드 (routes/event.py에서 사용):
add(): 처리 대기 중인 DB 객체를 메모리에 추가합니다.
commit(): 현재 세션에 있는 트랜잭션을 모두 커밋합니다.
get(): DB에서 단일 로우를 추출합니다.
'''
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
'''
SQLAlchemy의 선언적 베이스 클래스를 생성합니다.
이 클래스는 모든 모델 클래스가 상속받을 기본 클래스가 됩니다.
'''
Base = declarative_base()

'''
비동기 엔진을 사용하더라도, 
SQLAlchemy의 Base.metadata.create_all 같은 메서드는 동기적으로 설계되어 있습니다. 
이를 비동기 컨텍스트에서 실행하려면 run_sync를 사용해야 합니다. 
run_sync는 동기 함수를 비동기 컨텍스트에서 실행할 수 있게 해줍니다.

Base.metadata.create_all을 비동기 컨텍스트에서 실행하여 데이터베이스에 테이블을 생성합니다.

Base.metadata.create_all은 SQLAlchemy에서 선언된 모든 테이블을 포함합니다. 
테이블은 Base 클래스를 상속받아 정의된 모든 ORM 모델 클래스의 메타데이터에 포함됩니다.
'''
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


'''
get_db: 데이터베이스 세션을 제공하는 제너레이터 함수입니다.
with db_session() as session: 컨텍스트 매니저를 사용하여 세션을 생성하고, 블록이 종료되면 자동으로 세션을 종료합니다.
yield session: 세션을 호출자에게 반환합니다. 
이 함수는 주로 FastAPI의 종속성 주입 시스템과 함께 사용됩니다. 
FastAPI 엔드포인트 함수는 이 제너레이터를 호출하여 세션을 사용하고, 요청 처리가 끝나면 세션이 자동으로 종료됩니다.
'''
async def get_db():
    async with AsyncSessionLocal() as session:
        yield manipulation.Database(session)

async def close_db():
    await engine.dispose()




