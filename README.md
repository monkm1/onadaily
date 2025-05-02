# Onadaily
'그 사이트들' 출석체크 자동화 프로그램입니다. 이 프로그램을 사용함으로써 발생하는 모든 불이익은 사용자의 책임입니다.

## Download
[다운로드](https://github.com/monkm1/onadaily/releases/latest)

## Usage
프로그램을 1회 실행합니다. 설정 파일이 생성됩니다.
설정 파일(**onadaily.yaml**)을 메모장으로 엽니다.

### 일반 로그인 사용자
* 각 사이트 별로 자동 출첵을 사용하려면 *enable*을 *true*로 바꿉니다.
* 소셜 로그인을 사용하지 않으면 *login*은 *default*로 놔둡니다.

#### 아이디와 비밀번호
* __아이디와 비밀번호는 프로그램 실행 중 입력합니다.__
* 프로그램에서 입력한 아이디와 비밀번호는 OS의 암호화 저장소에 저장됩니다.
  * Windows의 경우, 자격 증명 관리자에 저장됩니다.
* 아이디와 비밀번호를 다시 입력하려면, 설정 파일을 열고 각 사이트의 *id*, *password* 항목을 지우세요.
* 설정 파일에 직접 입력하려면 *credential_storage*를 *lagacy*로 바꾸세요. (__권장하지 않습니다.__)

#### 예시
```yaml
common:
  entertoquit: true # true 이면, 종료할 때 enter 키를 눌러야 합니다.
  waittime: 5 # 웹 페이지가 로딩될때까지의 대기 시간(초)입니다. 이 시간이 지나면 오류로 처리됩니다.
  showhotdeal: false # true 이면, 할인 정보를 출력합니다.
  headless: false # true 이면, 크롬 창을 숨기고 동작합니다. 소셜 로그인과 같이 사용할 수 없습니다.
  order: # 출석 체크 순서입니다.
    - showdang
    - dingdong
    - banana
    - onami
    - domae
  autoretry: true # true 이면 실패 시 자동으로 재시도합니다.
  retrytime: 3 # autoretry가 true 일 때 재시도하는 최대 횟수입니다.
  keywordnoti: [] # 특정 단어가 할인에 포함되어 있을때 알립니다. showhotdeal이 true 일때만 동작합니다. ex) keywordnoti: ["로션", "메이드"]
  credential_storage: keyring
  # 아이디/비밀번호 저장소입니다. keyring, lagacy 중 하나를 선택합니다. lagacy는 이 파일 각 사이트 id/pasword에 직접 입력합니다.
  # 주의: lagacy는 보안이 취약합니다. keyring을 추천합니다.
  namespace: Onadaily # 고급 사용자용: keyring을 사용할 때 저장소 이름입니다. 이 이름으로 저장소에 접근합니다.

onami:
  enable: true
  login: default
  id: null
  password: null

...
```

---------------

### 소셜 로그인 사용자
* 사이트 별로 자동 출첵을 사용하려면 *enable*을 *true*로 바꿉니다.
* *login*을 구글 로그인이면 *google*, 카카오면 *kakao*로 바꿉니다.
* 사이트 별로 네이버, 페이스북, 트위터 로그인을 사용할 수 있습니다. (*naver*, *facebook*, *twitter* 사용)
* 프로그램이 실행되면, 로그인을 진행합니다.(최초 1회)
* *waittime* 을 충분히 주지 않으면 로그인 중에 실패할 수 있습니다.

#### 예시
```yaml
common:
  entertoquit: true # true 이면, 종료할 때 enter 키를 눌러야 합니다.
  waittime: 60 # 웹 페이지가 로딩될때까지의 대기 시간(초)입니다. 이 시간이 지나면 오류로 처리됩니다.
  showhotdeal: false # true 이면, 할인 정보를 출력합니다.
  headless: false # true 이면, 크롬 창을 숨기고 동작합니다. 소셜 로그인과 같이 사용할 수 없습니다.
  order: # 출석 체크 순서입니다.
    - showdang
    - dingdong
    - banana
    - onami
    - domae
  autoretry: true # true 이면 실패 시 자동으로 재시도합니다.
  retrytime: 3 # autoretry가 true 일 때 재시도하는 최대 횟수입니다.
  keywordnoti: [] # 특정 단어가 할인에 포함되어 있을때 알립니다. showhotdeal이 true 일때만 동작합니다. ex) keywordnoti: ["로션", "메이드"]
  credential_storage: keyring
  # 아이디/비밀번호 저장소입니다. keyring, lagacy 중 하나를 선택합니다. lagacy는 이 파일 각 사이트 id/pasword에 직접 입력합니다.
  # 주의: lagacy는 보안이 취약합니다. keyring을 추천합니다.
  namespace: Onadaily # 고급 사용자용: keyring을 사용할 때 저장소 이름입니다. 이 이름으로 저장소에 접근합니다.
onami:
  enable: true
  login: kakao # 카카오 로그인 사용
  id: null
  password: null

...
```
--------------
### 설정 파일 예시
#### 소셜 로그인, 일반 로그인 전부 사용하는 경우
```yaml
common:
  entertoquit: true # true 이면, 종료할 때 enter 키를 눌러야 합니다.
  waittime: 5 # 웹 페이지가 로딩될때까지의 대기 시간(초)입니다. 이 시간이 지나면 오류로 처리됩니다.
  showhotdeal: false # true 이면, 할인 정보를 출력합니다.
  headless: false # true 이면, 크롬 창을 숨기고 동작합니다. 소셜 로그인과 같이 사용할 수 없습니다.
  order: # 출석 체크 순서입니다.
    - showdang
    - dingdong
    - banana
    - onami
    - domae
  autoretry: true # true 이면 실패 시 자동으로 재시도합니다.
  retrytime: 3 # autoretry가 true 일 때 재시도하는 최대 횟수입니다.
  keywordnoti: [] # 특정 단어가 할인에 포함되어 있을때 알립니다. showhotdeal이 true 일때만 동작합니다. ex) keywordnoti: ["로션", "메이드"]
  credential_storage: keyring
  # 아이디/비밀번호 저장소입니다. keyring, lagacy 중 하나를 선택합니다. lagacy는 이 파일 각 사이트 id/pasword에 직접 입력합니다.
  # 주의: lagacy는 보안이 취약합니다. keyring을 추천합니다.
  namespace: Onadaily # 고급 사용자용: keyring을 사용할 때 저장소 이름입니다. 이 이름으로 저장소에 접근합니다.

onami:
  enable: true
  login: default
  id: null
  password: null

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

domae:
  enable: true
  login: default
  id: null
  password: null
```
onadaily.exe 로 실행합니다.
