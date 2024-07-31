    '''
    OAuth2 인증방식은 여러가지가 있는데 
    사용자가 사용자명과 패스워드를 입력해 로그인을 해서 토큰을 받는다면
    이는 OAuth2 의 password그랜트 타입에 해당한다.
    이 타입을 구현하려면 OAuth2PasswordBearer을 사용하면 된다.
    OAuth2PasswordBearer는 FastAPI에서 OAuth2를 사용하는 경우 
    토큰을 추출하기 위한 유틸리티 클래스다.
    '''
    
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/from_user/sign_in")
    # OAuth2PasswordBearer의 tokenUrl은 클라이언트가 토큰을 얻기 위해 사용할 URL을 지정한다. 
    # 이는 주로 문서화 목적으로 사용되며, 실제 토큰 발급 로직은 해당 URL에 구현되어 있다.
    '''
    클라이언트는 Authorization 헤더에 Bearer <token> 형식으로 토큰을 포함시켜 요청을 보낸다.
    token: str = Depends(oauth2_scheme) 를 사용하면
    FastAPI는 OAuth2PasswordBearer 인스턴스를 호출하여 HTTP 요청헤더에서 'Authorization' 헤더를 찾아 
    Bearer 뒤에 오는 실제 토큰 값을 추출하여 이를 token 변수에 할당한다.

    Bearer 토큰은 OAuth2 인증 방식에서 사용되는 토큰 유형 중 하나로, 클라이언트가 서버에 인증된 요청을 할 때 사용된다.
    Bearer 토큰은 다음과 같은 형식으로 사용된다:
    HTTP 요청 헤더:
    Authorization: Bearer <token>

    이를 통해 인증된 사용자만 접근할 수 있는 보호된 엔드포인트를 구현할 수 있다.
    '''
    
        # verifiy_access_token에서 처리하는 예외는 토큰 만료기한과 토큰 자체의 문제다.
        # get_current_user 함수는 verify_access_token의 검증 결과를 이용해 사용자 정보를 추출한다
        # get_current_user 함수에서 발생할 수 있는 모든 예외를 포괄적으로 처리
        
        # credentials_exception은 HTTPException을 미리 정의해두고 나중에 예외를 발생시킬때 재사용하기 위해 쓴다
