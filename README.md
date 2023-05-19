# onadaily
'그 사이트들' 출석체크 자동화 프로그램입니다. 이 프로그램을 사용함으로써 발생하는 모든 불이익은 사용자의 책임입니다.

## Download
[다운로드](https://github.com/monkm1/onadaily/releases/latest)

## Usage
설정 파일(**onadaily.yaml**)을 메모장으로 엽니다.

### 일반 로그인 사용자
* 각 사이트 별로 자동 출첵을 사용하려면 *enable*을 *true*로 바꿉니다.
* 소셜 로그인을 사용하지 않으면 *login*은 *default*로 놔두고, *id*와 *password*를 입력합니다.
* __아이디와 비밀번호를 "(쌍따옴표)로 감싸 입력하세요.__

#### 예시
```yaml
common:
  datadir: null # 일반 로그인'만' 사용한다면 이 부분은 입력하지 않아도 됩니다.
  profile: null
  entertoquit: true # true 이면, 종료할 때 enter 키를 눌러야 합니다.
  waittime: 5 # 웹 페이지가 로딩될때까지의 대기 시간(초)입니다. 이 시간이 지나면 오류로 처리됩니다.
  showhotdeal: false # true 이면, 할인 정보를 출력합니다.
  headless: false # true 이면, 크롬 창을 숨기고 동작합니다. 소셜 로그인과 같이 사용할 수 없습니다.
  order: # 출석 체크 순서입니다.
    - showdang
    - dingdong
    - banana
    - onami
  autoretry: true # true 이면 실패 시 자동으로 재시도합니다.
  retrytime: 3 # autoretry가 true 일 때 재시도하는 최대 횟수입니다.
onami:
  enable: true
  login: default
  id: "thisisnotrealid" # 여기에 id
  password: "1q2w3e4r!" # 여기에 패스워드를 입력하세요.

...
```

---------------

### 소셜 로그인 사용자
* 사이트 별로 자동 출첵을 사용하려면 *enable*을 *true*로 바꿉니다.
* 구글 크롬 기본 프로필에 사용하고자 하는 사이트 소셜 자동로그인을 해놓습니다.
* 사용하는 크롬 프로필 창은 꺼진 상태로 진행해야 합니다.
* *datadir*과 *profile*을 주석처럼 바꿉니다.
* *login*을 구글 로그인이면 *google*, 카카오면 *kakao*로 바꿉니다.
* 사이트 별로 네이버, 페이스북, 트위터 로그인을 사용할 수 있습니다. (*naver*, *facebook*, *twitter* 사용)

#### 예시
```yaml
common:
  datadir: null # 일반 로그인'만' 사용한다면 이 부분은 입력하지 않아도 됩니다.
  profile: null
  entertoquit: true # true 이면, 종료할 때 enter 키를 눌러야 합니다.
  waittime: 5 # 웹 페이지가 로딩될때까지의 대기 시간(초)입니다. 이 시간이 지나면 오류로 처리됩니다.
  showhotdeal: false # true 이면, 할인 정보를 출력합니다.
  headless: false # true 이면, 크롬 창을 숨기고 동작합니다. 소셜 로그인과 같이 사용할 수 없습니다.
  order: # 출석 체크 순서입니다.
    - showdang
    - dingdong
    - banana
    - onami
  autoretry: true # true 이면 실패 시 자동으로 재시도합니다.
  retrytime: 3 # autoretry가 true 일 때 재시도하는 최대 횟수입니다.
onami:
  enable: true
  login: kakao # 카카오 로그인 사용
  id: null # id 와 password는 입력하지 않습니다.
  password: null

...
```
--------------
### 설정 파일 예시
#### 소셜 로그인, 일반 로그인 전부 사용하는 경우
```yaml
common:
  datadir: '%localappdata%\Google\Chrome\User Data' # 일반 로그인'만' 사용한다면 이 부분은 입력하지 않아도 됩니다.
  profile: 'profile 0'
  entertoquit: true # true 이면, 종료할 때 enter 키를 눌러야 합니다.
  waittime: 5 # 웹 페이지가 로딩될때까지의 대기 시간(초)입니다. 이 시간이 지나면 오류로 처리됩니다.
  showhotdeal: false # true 이면, 할인 정보를 출력합니다.
  headless: false # true 이면, 크롬 창을 숨기고 동작합니다. 소셜 로그인과 같이 사용할 수 없습니다.
  order: # 출석 체크 순서입니다.
    - showdang
    - dingdong
    - banana
    - onami
  autoretry: true # true 이면 실패 시 자동으로 재시도합니다.
  retrytime: 3 # autoretry가 true 일 때 재시도하는 최대 횟수입니다.

onami:
  enable: true
  login: default
  id: "thisisnotrealid"
  password: "1q2w3e4r!"

showdang:
  enable: true
  login: google
  id: null
  password: null

banana:
  enable: true
  login: facebook
  id: null
  password: null

dingdong:
  enable: false
  login: kakao
  id: null
  password: null
```
onadaily.exe 로 실행합니다.
