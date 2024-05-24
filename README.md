# Text_Holdem


## test application for Texas Holdem game Text version

### 현재 디렉토리 구조

./testapp  
├── main.py  
├── database  
│   └── connection.py  
│   └── crud.py  
├── models  
│   ├── events.py  
│   └── users.py  
├── routes  
│   ├── events.py  
│   └── users.py  
└── test_main.py  
  
#### 진척상황
- FastAPI 애플리케이션-mongoDB 연동
- 클라이언트 측에서 필요한 일부 기능 구현
  - 유저 등록, 유저 로그인, 유저 이벤트 생성/변경/삭제,조회

#### 현재 이슈 05.24.2024
- pytest 실패, 원인분석 중
- 테스트 내용
  - 가상 클라이언트 9개로 각각 유저 등록, 로그인, 이벤트 생성 및 변경 요청 처리를 하는 pytest가 작동하지 않음

#### 에러 메시지
```python
  (holdem) (base) philosucker@philosucker-Lenovo-IdeaPad-S340-15API:~/testapp$ pytest tests/test_main.py
======================================= test session starts =======================================
platform linux -- Python 3.12.3, pytest-8.2.1, pluggy-1.5.0
benchmark: 4.0.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/philosucker/testapp
configfile: pytest.ini
plugins: asyncio-0.23.7, anyio-4.3.0, benchmark-4.0.0
asyncio: mode=Mode.AUTO
collected 2 items                                                                                 

tests/test_main.py FF                                                                       [100%]

============================================ FAILURES =============================================
________________________________ test_user_registration_and_events ________________________________

async_client = <httpx.AsyncClient object at 0x7f37c8aaee70>

    @pytest.mark.anyio
    async def test_user_registration_and_events(async_client):
>       tokens = await create_users_and_login(async_client)

tests/test_main.py:57: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/test_main.py:31: in create_users_and_login
    await client.post("/user/signup", json=user_data)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1892: in post
    return await self.request(
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1574: in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1661: in send
    response = await self._send_handling_auth(
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1689: in _send_handling_auth
    response = await self._send_handling_redirects(
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1726: in _send_handling_redirects
    response = await self._send_single_request(request)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1763: in _send_single_request
    response = await transport.handle_async_request(request)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_transports/asgi.py:164: in handle_async_request
    await self.app(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/applications.py:123: in __call__
    await self.middleware_stack(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/errors.py:186: in __call__
    raise exc
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/errors.py:164: in __call__
    await self.app(scope, receive, _send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/cors.py:85: in __call__
    await self.app(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/exceptions.py:65: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:64: in wrapped_app
    raise exc
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:53: in wrapped_app
    await app(scope, receive, sender)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:756: in __call__
    await self.middleware_stack(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:776: in app
    await route.handle(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:297: in handle
    await self.app(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:77: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:64: in wrapped_app
    raise exc
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:53: in wrapped_app
    await app(scope, receive, sender)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:72: in app
    response = await func(request)
../.conda/envs/holdem/lib/python3.12/site-packages/fastapi/routing.py:278: in app
    raw_response = await run_endpoint_function(
../.conda/envs/holdem/lib/python3.12/site-packages/fastapi/routing.py:191: in run_endpoint_function
    return await dependant.call(**values)
routes/users.py:18: in sign_user_up
    user_exist = await User.find_one(User.email == user.email)
../.conda/envs/holdem/lib/python3.12/site-packages/beanie/odm/queries/find.py:1042: in __await__
    document = yield from self._find_one().__await__()  # type: ignore
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <beanie.odm.queries.find.FindOne object at 0x7f37c7826cc0>

    async def _find_one(self):
        if self.fetch_links:
            return await self.document_model.find_many(
                *self.find_expressions,
                session=self.session,
                fetch_links=self.fetch_links,
                projection_model=self.projection_model,
                nesting_depth=self.nesting_depth,
                nesting_depths_per_field=self.nesting_depths_per_field,
                **self.pymongo_kwargs,
            ).first_or_none()
>       return await self.document_model.get_motor_collection().find_one(
            filter=self.get_filter_query(),
            projection=get_projection(self.projection_model),
            session=self.session,
            **self.pymongo_kwargs,
        )
E       RuntimeError: Task <Task pending name='Task-3' coro=<test_user_registration_and_events() running at /home/philosucker/testapp/tests/test_main.py:57> cb=[_run_until_complete_cb() at /home/philosucker/.conda/envs/holdem/lib/python3.12/asyncio/base_events.py:182]> got Future <Future pending cb=[_chain_future.<locals>._call_check_cancel() at /home/philosucker/.conda/envs/holdem/lib/python3.12/asyncio/futures.py:387]> attached to a different loop

../.conda/envs/holdem/lib/python3.12/site-packages/beanie/odm/queries/find.py:1007: RuntimeError
________________________________________ test_performance _________________________________________

async_client = <httpx.AsyncClient object at 0x7f37c8aaee70>

    @pytest.mark.anyio
    async def test_performance(async_client):
        import time
        start_time = time.time()
>       await test_user_registration_and_events(async_client)

tests/test_main.py:91: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/test_main.py:57: in test_user_registration_and_events
    tokens = await create_users_and_login(async_client)
tests/test_main.py:31: in create_users_and_login
    await client.post("/user/signup", json=user_data)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1892: in post
    return await self.request(
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1574: in request
    return await self.send(request, auth=auth, follow_redirects=follow_redirects)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1661: in send
    response = await self._send_handling_auth(
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1689: in _send_handling_auth
    response = await self._send_handling_redirects(
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1726: in _send_handling_redirects
    response = await self._send_single_request(request)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1763: in _send_single_request
    response = await transport.handle_async_request(request)
../.conda/envs/holdem/lib/python3.12/site-packages/httpx/_transports/asgi.py:164: in handle_async_request
    await self.app(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/applications.py:123: in __call__
    await self.middleware_stack(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/errors.py:186: in __call__
    raise exc
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/errors.py:164: in __call__
    await self.app(scope, receive, _send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/cors.py:85: in __call__
    await self.app(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/middleware/exceptions.py:65: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:64: in wrapped_app
    raise exc
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:53: in wrapped_app
    await app(scope, receive, sender)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:756: in __call__
    await self.middleware_stack(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:776: in app
    await route.handle(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:297: in handle
    await self.app(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:77: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:64: in wrapped_app
    raise exc
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/_exception_handler.py:53: in wrapped_app
    await app(scope, receive, sender)
../.conda/envs/holdem/lib/python3.12/site-packages/starlette/routing.py:72: in app
    response = await func(request)
../.conda/envs/holdem/lib/python3.12/site-packages/fastapi/routing.py:278: in app
    raw_response = await run_endpoint_function(
../.conda/envs/holdem/lib/python3.12/site-packages/fastapi/routing.py:191: in run_endpoint_function
    return await dependant.call(**values)
routes/users.py:18: in sign_user_up
    user_exist = await User.find_one(User.email == user.email)
../.conda/envs/holdem/lib/python3.12/site-packages/beanie/odm/queries/find.py:1042: in __await__
    document = yield from self._find_one().__await__()  # type: ignore
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <beanie.odm.queries.find.FindOne object at 0x7f37c57f14f0>

    async def _find_one(self):
        if self.fetch_links:
            return await self.document_model.find_many(
                *self.find_expressions,
                session=self.session,
                fetch_links=self.fetch_links,
                projection_model=self.projection_model,
                nesting_depth=self.nesting_depth,
                nesting_depths_per_field=self.nesting_depths_per_field,
                **self.pymongo_kwargs,
            ).first_or_none()
>       return await self.document_model.get_motor_collection().find_one(
            filter=self.get_filter_query(),
            projection=get_projection(self.projection_model),
            session=self.session,
            **self.pymongo_kwargs,
        )
E       RuntimeError: Task <Task pending name='Task-4' coro=<test_performance() running at /home/philosucker/testapp/tests/test_main.py:91> cb=[_run_until_complete_cb() at /home/philosucker/.conda/envs/holdem/lib/python3.12/asyncio/base_events.py:182]> got Future <Future pending cb=[_chain_future.<locals>._call_check_cancel() at /home/philosucker/.conda/envs/holdem/lib/python3.12/asyncio/futures.py:387]> attached to a different loop

../.conda/envs/holdem/lib/python3.12/site-packages/beanie/odm/queries/find.py:1007: RuntimeError
======================================== warnings summary =========================================
../.conda/envs/holdem/lib/python3.12/site-packages/pydantic/_internal/_config.py:284
../.conda/envs/holdem/lib/python3.12/site-packages/pydantic/_internal/_config.py:284
../.conda/envs/holdem/lib/python3.12/site-packages/pydantic/_internal/_config.py:284
../.conda/envs/holdem/lib/python3.12/site-packages/pydantic/_internal/_config.py:284
  /home/philosucker/.conda/envs/holdem/lib/python3.12/site-packages/pydantic/_internal/_config.py:284: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.7/migration/
    warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)

../.conda/envs/holdem/lib/python3.12/site-packages/passlib/utils/__init__.py:854
  /home/philosucker/.conda/envs/holdem/lib/python3.12/site-packages/passlib/utils/__init__.py:854: DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13
    from crypt import crypt as _crypt

tests/test_main.py::test_user_registration_and_events
  /home/philosucker/.conda/envs/holdem/lib/python3.12/site-packages/httpx/_client.py:1426: DeprecationWarning: The 'app' shortcut is now deprecated. Use the explicit style 'transport=ASGITransport(app=...)' instead.
    warnings.warn(message, DeprecationWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
===================================== short test summary info =====================================
FAILED tests/test_main.py::test_user_registration_and_events - RuntimeError: Task <Task pending name='Task-3' coro=<test_user_registration_and_events() runni...
FAILED tests/test_main.py::test_performance - RuntimeError: Task <Task pending name='Task-4' coro=<test_performance() running at /home/philo...
================================== 2 failed, 6 warnings in 1.42s ==================================
```
