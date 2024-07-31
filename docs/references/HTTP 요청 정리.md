
### 1. 경로 파라미터 (Path Parameters)

#### 클라이언트 측:
- **URL만 사용**: 경로 파라미터는 URL의 일부로 포함됩니다.
- 예시: `https://api.example.com/users/123/posts`

#### 서버 측:
- **데코레이터**: 경로 파라미터를 중괄호 `{}`로 정의합니다.
  ```python
  @app.get("/users/{user_id}/posts")
  async def read_user_posts(user_id: int):
      return {"user_id": user_id}
  ```
- **경로 동작 함수**: 함수 인자로 경로 파라미터를 받습니다.

### 2. 쿼리 파라미터 (Query Parameters)

#### 클라이언트 측:
- **URL 뒤에 `?`**를 붙이고 `key=value` 쌍으로 쿼리 파라미터를 나열합니다.
- 여러 개의 쿼리 파라미터는 `&`로 구분합니다.
- 예시: `https://api.example.com/items?category=books&sort=price`

#### 서버 측:
- **데코레이터**: URL 패턴에 쿼리 파라미터를 포함하지 않고, 경로만 정의합니다.
  ```python
  @app.get("/items/")
  async def read_items(category: str = None, sort: str = None):
      return {"category": category, "sort": sort}
  ```
- **경로 동작 함수**: 함수 인자로 쿼리 파라미터를 받습니다. 기본값을 지정하거나 `Query`를 사용하여 정의할 수 있습니다.

### 3. 요청 바디 (Request Body)

#### 클라이언트 측:
- **URL 뒤에 데이터를 나열하지 않음**: 요청 바디는 URL 뒤에 한칸 띄고 나열하지 않습니다. 요청 바디는 HTTP 요청의 일부분으로, URL이나 쿼리 파라미터와는 별도로 처리됩니다.
- 데이터는 JSON, XML, 폼 데이터 등 다양한 형식으로 HTTP 요청의 바디에 포함됩니다.
- 예시 (JSON 데이터):
  ```json
  {
    "username": "user1",
    "password": "securepassword"
  }
  ```

#### 서버 측:
- **데코레이터**: URL과 무관하게 설정합니다.
- **경로 동작 함수**: 요청 바디의 데이터를 `Body` 객체나 Pydantic 모델로 받습니다.
  ```python
  from pydantic import BaseModel

  class User(BaseModel):
      username: str
      password: str

  @app.post("/login/")
  async def login(user: User):
      return {"username": user.username}
  ```

  또는:
  ```python
  from fastapi import Body

  @app.post("/login/")
  async def login(username: str = Body(...), password: str = Body(...)):
      return {"username": username}
  ```

### 요약

- **경로 파라미터**: 클라이언트는 URL에 포함하여 요청, 서버는 함수 인자로 처리.
- **쿼리 파라미터**: 클라이언트는 URL 뒤에 `?`로 나열, 서버는 함수 인자로 처리.
- **요청 바디**: 클라이언트는 URL 뒤가 아니라 HTTP 요청의 바디에 데이터를 포함, 서버는 `Body` 객체나 Pydantic 모델로 처리.

