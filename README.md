# onadaily
'그 사이트들' 출석체크 자동화 프로그램입니다.

## download
[다운로드](https://github.com/monkm1/onadaily/releases/latest)

## Usage
설정 파일(**onadaily.yaml**)을 메모장으로 엽니다.

### 일반 로그인 사용자
* 각 사이트 별로 자동 출첵을 사용하려면 *enable*을 *true*로 바꿉니다.
* 구글/카카오 로그인을 사용하지 않으면 *login*은 *default*로 놔두고, *id*와 *password*를 입력합니다.

#### 예시
```yaml
common:
  datadir: null # 일반 로그인'만' 사용한다면 이 부분은 입력하지 않아도 됩니다.
  profile: null
  entertoquit: true

onami:
  enable: true
  login: default
  id: thisisnotrealid # 여기에 id
  password: 1q2w3e4r! # 여기에 패스워드를 입력하세요.

...
```

---------------

### 구글/카카오 로그인 사용자
* 사이트 별로 자동 출첵을 사용하려면 *enable*을 *true*로 바꿉니다.
* 구글 크롬 기본 프로필에 사용하고자 하는 사이트 구글/카카오 자동로그인을 해놓습니다.
* *datadir*과 *profile*을 설명처럼 바꿉니다.
* *login*을 구글 로그인이면 *google*, 카카오면 *kakao*로 바꿉니다.

#### 예시
```yaml
common:
  datadir: "%localappdata%\\Google\\Chrome\\User Data" # 크롬의 User Data 경로
  profile: "default" # 기본 프로필이 아닌 다른 프로필을 사용해도 됩니다.
  entertoquit: true

onami:
  enable: true
  login: kakao # 카카오 로그인 사용
  id: null # id 와 password는 입력하지 않습니다.
  password: null

...
```
--------------
### 설정 파일 예시
#### 구글, 카카오, 일반 로그인 전부 사용하는 경우
```yaml
common:
  datadir: "%localappdata%\\Google\\Chrome\\User Data"
  profile: "default"
  entertoquit: true # if false, you cannot see the error message.

# Write id and password if login is 'default'.

onami:
  enable: true
  login: default
  id: thisisnotrealid
  password: 1q2w3e4r!

showdang:
  enable: true
  login: google
  id: null
  password: null

banana:
  enable: true
  login: kakao
  id: null
  password: null
```
압축을 풀고, onadaily.exe 로 실행합니다.