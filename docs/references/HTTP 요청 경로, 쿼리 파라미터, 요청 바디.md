# 라우트에 경로 파라미터를 사용하는 주된 목적 
클라이언트를 식별하고, 클라이언트 별로 특정한 처리를 하기 위함입니다. 
이를 통해 서버는 클라이언트가 보낸 요청을 쉽게 구분하고, 적절한 데이터를 처리하거나 반환할 수 있습니다.

### 경로 파라미터의 주요 용도

1. **클라이언트 식별**:
   - 경로 파라미터를 사용하여 각 클라이언트를 고유하게 식별할 수 있습니다. 
   예를 들어, `user/{user_id}`와 같은 경로를 사용하면 `user_id`를 통해 각 사용자를 식별할 수 있습니다.
    이를 통해 서버는 특정 클라이언트와 관련된 데이터나 상태를 관리할 수 있습니다.

2. **데이터 접근 및 조작**:
   - 경로 파라미터는 특정 데이터를 식별하고 접근하는 데 사용됩니다. 
   예를 들어, `game/{game_id}` 경로를 통해 특정 게임 세션을 식별하고, 
   해당 게임 세션에 관련된 데이터를 가져오거나 수정할 수 있습니다.

3. **RESTful API 설계**:
   - RESTful API 설계에서 경로 파라미터는 자원을 명확하게 식별하는 데 사용됩니다. 
   예를 들어, `api/users/{user_id}/posts/{post_id}`와 같은 경로는 
   특정 사용자(`user_id`)의 특정 게시물(`post_id`)에 접근하는 것을 나타냅니다.

4. **상태 관리 및 세션 유지**:
   - 웹소켓 연결과 같은 상태가 있는 프로토콜에서도 경로 파라미터는 클라이언트의 상태를 관리하는 데 유용합니다. 
   예를 들어, 게임 서버에서 클라이언트가 특정 게임에 연결하려는 경우, `
   game/{game_id}/player/{player_id}`와 같은 경로를 사용하여 
   게임과 플레이어를 식별하고, 해당 세션을 관리할 수 있습니다.

### 예시

예를 들어, 클라이언트가 게임 서버에 연결할 때 게임 ID와 플레이어 ID를 포함하는 경우:

```python
@app.websocket("/game/{game_id}/player/{player_id}")
async def websocket_endpoint(websocket, game_id, player_id):
    # 클라이언트를 특정 게임 세션과 플레이어로 식별
    game = get_game_instance(game_id)
    if game:
        player = game.get_player(player_id)
        if player:
            await player.handle_websocket(websocket)
        else:
            await websocket.close()
    else:
        await websocket.close()
```
위 함수에서  websocket_endpoint 함수의 game_id, player_id 인자는 경로 파라미터를 받는 인자

이 예시에서:

1. `game_id`와 `player_id`는 클라이언트를 특정 게임과 플레이어로 식별합니다.
2. 서버는 경로 파라미터를 사용하여 게임 세션과 플레이어 객체를 가져오고, 해당 클라이언트와 관련된 처리를 수행합니다.

경로 파라미터를 사용하는 이러한 방식은 
서버가 다수의 클라이언트와 상호작용하는 상황에서 특히 유용하며, 
각 클라이언트의 요청을 명확히 구분하고 처리할 수 있게 합니다.

# 경로 파라미터, 쿼리 파라미터와 요청 바디의 용도 차이

서버는 클라이언트가 보낸 `table_id`와 `client_id`를  요청 바디의 JSON 형식으로 받는 것과 
라우트의 경로 파라미터, 쿼리 파라미터로 받는 것 모두 가능

### 두 가지 방법의 차이와 용도

1. **경로 파라미터 (Path Parameters)**:
 경로 파라미터는 리소스를 명확하게 식별하는 데 사용됩니다.
     경로 파라미터는 URL의 경로 부분에 포함되며, 웹 리소스를 식별하는 데 사용됩니다. 
     웹 서버는 URL 경로를 사용하여 특정 리소스나 서비스에 대한 요청을 라우팅합니다.
     예: https://example.com/users/123에서 123은 사용자 리소스를 식별하는 경로 파라미터입니다.

2. **쿼리 파라미터 (query Parameters)**:
   쿼리 파라미터는 URL의 끝에 ? 뒤에 이어지며, 추가적인 정보나 필터링 옵션을 전달하는 데 사용됩니다. 
      이 파라미터들은 키-값 쌍으로 제공됩니다.
      예: https://example.com/search?q=python&page=2에서 q=python과 page=2는 쿼리 파라미터입니다.
           
3. **요청 바디의 JSON (Request Body JSON)**:
   보다 복잡한 구조의 데이터를 전달할 수 있습니다. 


### 선택 기준

#### URL은 길이에 제한이 있을 수 있으며, 지나치게 긴 URL은 처리가 어려울 수 있습니다. 
  반면, 요청 본문은 훨씬 더 많은 데이터를 포함할 수 있으며, 구조화된 데이터를 효율적으로 전송하는 데 적합합니다.

  경로 파라미터와 쿼리 파라미터는 URL의 일부로 사용되어 
  리소스를 식별하거나 필터링 정보를 제공하고, 
  헤더와 요청 본문은 요청의 메타데이터와 데이터를 제공하는 역할을 합니다
  
#### URL은 종종 로그, 브라우저 기록, 서버 로그 등에 저장될 수 있기 때문에 민감한 정보가 포함된 경우 보안 위험이 있습니다
  경로 파라미터와 쿼리 파라미터는 URL의 일부로 포함되기 때문에 브라우저의 히스토리, 서버 로그, 네트워크 로그 등에서 쉽게 노출될 수 있습니다
  
#### 헤더와 요청 바디는 브라우저의 주소창에 나타나지 않으며, 브라우저 캐시, 히스토리에도 저장되지 않습니다.
  하지만 네트워크 로그나 서버 로그에 기록하려면 기록될 수 있습니다. 민감한 정보가 로그에 남지 않도록 주의해야 합니다.
  

# FastAPI에서 HTTP 요청을 받을 때 경로 파라미터를 사용하려면, 경로 동작 함수의 데코레이터에 경로 파라미터를 명시하고, 해당 함수의 인자로 해당 파라미터를 정의하면 됩니다. 

경로 파라미터는 URL 경로의 일부로 사용되어, 클라이언트가 요청할 때 특정 리소스를 식별하는 데 사용됩니다.

### 경로 파라미터 설정 방법

1. **데코레이터에서 경로 파라미터 정의**: 경로 파라미터는 URL 경로에 중괄호 `{}`를 사용하여 정의됩니다.
2. **함수 인자로 경로 파라미터 받기**: 함수 인자에서 경로 파라미터의 이름과 타입을 정의합니다.

#### 예시: 기본적인 경로 파라미터 사용

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

위 예시에서:
- `@app.get("/items/{item_id}")`: 이 데코레이터는 경로 파라미터 `item_id`를 정의합니다.
- `item_id: int`: 경로 파라미터는 함수 인자로 전달되며, `int` 타입으로 지정되어 자동으로 변환됩니다.

#### 경로 파라미터 예시 URL

클라이언트가 `http://example.com/items/123`와 같은 URL로 요청을 보내면:
- `item_id`는 `123`이 됩니다.

FastAPI는 경로 파라미터를 자동으로 추출하고 지정된 타입으로 변환합니다. 만약 클라이언트가 잘못된 타입의 값을 전달하면, FastAPI는 자동으로 422 Unprocessable Entity 상태 코드를 반환하여 잘못된 요청임을 알립니다.

### 복수의 경로 파라미터 사용

경로 파라미터는 여러 개 정의할 수 있으며, FastAPI는 이를 각각 인자로 매핑합니다.

```python
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: int):
    return {"user_id": user_id, "item_id": item_id}
```

- 이 예시에서 `user_id`와 `item_id` 두 개의 경로 파라미터를 정의합니다.
- URL 예: `http://example.com/users/5/items/3`에서 `user_id`는 `5`, `item_id`는 `3`이 됩니다.

### 요약

- **경로 파라미터 정의**: FastAPI에서는 경로 파라미터를 URL 경로에 중괄호 `{}`를 사용하여 정의합니다.
- **함수 인자로 받기**: 경로 파라미터는 함수 인자로 전달되며, 타입 힌트를 통해 자동 변환 및 검증이 이루어집니다.

이러한 방식으로 FastAPI는 경로 파라미터를 쉽게 처리할 수 있으며, 이를 통해 RESTful API 설계에서 유연하고 강력한 경로 정의가 가능합니다.

# FastAPI에서 쿼리 파라미터를 받으려면, 경로 동작 함수에 해당 쿼리 파라미터를 인자로 설정해주면 됩니다.

FastAPI는 인자 이름과 URL 쿼리 파라미터를 자동으로 매핑하며, 인자의 타입 힌트를 통해 데이터를 적절한 타입으로 변환합니다.

### 기본적인 사용법

쿼리 파라미터를 경로 동작 함수에 인자로 설정할 때, 기본값을 지정할 수 있으며, 기본값이 없을 경우 해당 파라미터는 필수로 간주됩니다.

#### 예시 1: 기본값이 있는 선택적 쿼리 파라미터

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(q: str = None):
    return {"query": q}
```

- `q: str = None`: `q`라는 이름의 쿼리 파라미터를 받으며, 기본값이 `None`이므로 선택적입니다.
- 쿼리 파라미터가 제공되지 않으면 기본값인 `None`이 사용됩니다.

#### 예시 2: 필수 쿼리 파라미터

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/search/")
async def search_items(keyword: str = Query(...)):
    return {"search_keyword": keyword}
```

- `keyword: str = Query(...)`: `keyword`라는 이름의 필수 쿼리 파라미터를 받습니다.
- `Query(...)`는 필수 파라미터를 설정하며, 파라미터가 제공되지 않으면 422 상태 코드를 반환합니다.

#### 예시 3: 기본값과 타입이 있는 쿼리 파라미터

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

- `skip: int = 0`: 정수형 쿼리 파라미터 `skip`을 받으며, 기본값은 0입니다.
- `limit: int = 10`: 정수형 쿼리 파라미터 `limit`을 받으며, 기본값은 10입니다.

이러한 방식으로 FastAPI는 쿼리 파라미터를 처리하며, 요청에서 전달된 쿼리 파라미터를 경로 동작 함수의 인자로 자동으로 매핑하고 변환합니다.

### 요약

- 경로 동작 함수에 쿼리 파라미터를 인자로 설정하면, FastAPI는 해당 인자 이름과 일치하는 쿼리 파라미터를 요청에서 추출합니다.
- 타입 힌트를 통해 자동으로 타입 변환이 이루어지며, 기본값을 설정할 수 있습니다.
- 필수 파라미터로 설정하려면 기본값을 설정하지 않거나 `Query(...)`를 사용할 수 있습니다.

이러한 기능을 통해 FastAPI는 쿼리 파라미터의 처리와 검증을 자동으로 수행하여 개발자의 편의성을 높입니다.

# FastAPI에서 서버에 HTTP 요청 시 요청 바디를 포함하려면, 서버 쪽 경로 동작 함수에서 `Body` 함수를 사용해야 한다

### 1. 기본적인 요청 바디 사용

```python
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/items/")
async def create_item(item: dict = Body(...)):
    return {"item": item}
```

위 예시에서:
- `Body(...)`는 요청 바디를 정의하는 데 사용됩니다. 
FastAPI는 `Body` 함수에 기본값을 지정하지 않은 경우 해당 파라미터가 필수임을 의미하는 `...`을 사용합니다.
- `item: dict`는 요청 바디의 데이터를 사전(dict)으로 받겠다는 것을 의미합니다.

### 2. Pydantic 모델 사용
보다 구조화된 데이터 검증과 정의를 위해 Pydantic 모델을 사용할 수 있습니다:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

@app.post("/items/")
async def create_item(item: Item):
    return {"item": item}
```

위 예시에서:
- `Item` 클래스는 Pydantic의 `BaseModel`을 상속받아 정의되었습니다. 
각 필드는 요청 바디에 포함될 수 있는 데이터의 타입과 기본값을 정의합니다.
- `item: Item`은 요청 바디를 `Item` 모델로 파싱하고 검증합니다.
 FastAPI는 요청 바디의 JSON 데이터를 자동으로 `Item` 모델 인스턴스로 변환해 줍니다.

### 요약

- **Body 사용**: 요청 바디를 정의하는 데 사용되며, 기본 데이터 타입(dict, list 등)을 받을 수 있습니다.
- **Pydantic 모델 사용**: 더 정교한 데이터 스키마와 검증을 위해 사용됩니다.
 데이터의 구조와 타입을 명확히 정의할 수 있으며, FastAPI가 이를 기반으로 요청 데이터를 검증합니다.

FastAPI는 이러한 방식으로 요청 바디를 처리하며, 이를 통해 클라이언트로부터 전송된 데이터를 안전하고 구조화된 방식으로 다룰 수 있습니다.


# 경로 파라미터와 쿼리 파라미터를 함께 사용하는 것은 RESTful API 설계에서 자주 활용되는 패턴입니다. 
두 가지 파라미터를 조합하면 특정 리소스를 명확하게 식별하고, 그 리소스에 대해 추가적인 필터링이나 정렬 등의 작업을 수행할 수 있습니다. 각 파라미터 유형이 가진 특성을 활용하여 다양한 요구사항을 충족시킬 수 있습니다.

### 경로 파라미터와 쿼리 파라미터의 역할

- **경로 파라미터 (Path Parameters)**:
  - 주로 리소스를 식별하는 데 사용됩니다. 예를 들어, 특정 사용자, 제품, 게시물 등의 고유한 식별자를 나타냅니다.
  - URL 경로의 일부로 사용되며, 필수적이고 고정된 정보를 전달하는 데 적합합니다.

- **쿼리 파라미터 (Query Parameters)**:
  - 리소스를 필터링, 정렬, 검색, 페이징(pagination)하는 데 사용됩니다. 선택적이고 가변적인 정보 전달에 적합합니다.
  - URL의 `?` 뒤에 위치하며, 키-값 쌍으로 다양한 옵션을 전달할 수 있습니다.

### 함께 사용하는 경우

1. **특정 리소스에 대한 필터링/검색**:
   - 예를 들어, 특정 사용자의 게시물을 조회할 때, 경로 파라미터로 사용자를 식별하고, 쿼리 파라미터로 게시물의 카테고리나 날짜 범위 등을 필터링할 수 있습니다.
   - **예시**: `/users/{user_id}/posts?category=tech&date=2024-07-29`
   - 여기서 `user_id`는 특정 사용자를 식별하고, `category`와 `date`는 게시물을 필터링하는 데 사용됩니다.
   
user_id = 123
url = f"https://api.example.com/users/{user_id}/posts?category=tech&date=2024-07-29"
response = requests.get(url)

2. **특정 리소스의 세부 정보 요청**:
   - 특정 제품이나 항목의 상세 정보에 대한 요청 시, 경로 파라미터로 제품을 식별하고, 쿼리 파라미터로 세부 정보의 타입을 지정할 수 있습니다.
   - **예시**: `/products/{product_id}?details=full`
   - `product_id`로 제품을 식별하고, `details` 쿼리 파라미터로 상세 정보 수준을 지정합니다.

3. **페이징(pagination)**:
   - 목록이나 컬렉션의 특정 부분을 조회할 때, 경로 파라미터로 컬렉션을 식별하고, 쿼리 파라미터로 페이지 번호와 페이지 크기를 지정할 수 있습니다.
   - **예시**: `/articles?page=2&page_size=10`
   - `page`와 `page_size`는 쿼리 파라미터로 페이지네이션을 처리합니다.

4. **특정 리소스에 대한 작업 수행**:
   - 특정 리소스에 대해 작업을 수행할 때, 경로 파라미터로 리소스를 식별하고, 쿼리 파라미터로 작업에 대한 추가 옵션을 전달할 수 있습니다.
   - **예시**: `/orders/{order_id}/status?update=shipped`
   - `order_id`로 주문을 식별하고, `update` 쿼리 파라미터로 상태 업데이트 정보를 전달합니다.

### 결론

경로 파라미터와 쿼리 파라미터를 함께 사용하면 RESTful API에서 리소스를 명확히 식별하고, 그 리소스에 대해 보다 세부적인 조작을 할 수 있습니다. 경로 파라미터는 고유하고 필수적인 정보를, 쿼리 파라미터는 선택적이고 가변적인 정보를 전달하는 데 사용됩니다. 이를 통해 API 요청을 더욱 유연하고 풍부하게 만들 수 있습니다.
