# LOTTO LAB 645 v2.0 — PC·휴대폰 공용 웹앱

**현재 상태**: 프로그램과 자동 수집 워크플로 구현 완료. **실제 웹 공개 및 주간 자동 갱신은 GitHub 저장소/Pages에 업로드하고 설정을 해야 시작됩니다.** 이 채팅만으로 서버에 배포되지는 않습니다.

## 바로 사용하기 (PC)

1. 압축을 해제합니다.
2. 쉬운 테스트: 같은 폴더의 `lotto_lab_645_v2_단일파일.html`을 Chrome/Edge로 엽니다. 숫자 생성·통계·CSV 파일은 사용할 수 있습니다. 인터넷 연결이 있고 공개 데이터 제공자가 정상 동작하면 역대 번호를 추가로 받아옵니다.
3. 완전한 웹앱 테스트: 터미널에서 `python -m http.server 8000` 을 실행한 뒤 `http://localhost:8000`에 접속합니다. PC 브라우저는 PWA를 설치할 수 있습니다. 모바일에서는 PC localhost 주소가 아닌 **실제 HTTPS 공개 사이트 URL**이 필요합니다.

## GitHub Pages 공개 배포 및 자동 갱신 (중요)

1. [GitHub](https://github.com/)에서 **새 공개 저장소**를 만듭니다 (예: `lotto-lab-645`).
2. 압축 안의 `index.html`, `app.js`, `styles.css`, `sw.js`, `manifest.webmanifest`, 아이콘, `data/`, `scripts/`, `.github/workflows/`를 **폴더 구조 그대로** 저장소의 `main` 브랜치 루트에 업로드/커밋합니다.
3. 저장소 **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)` → Save**를 선택합니다. 보통 `https://계정명.github.io/lotto-lab-645/` 형태로 접속할 수 있습니다. 실제 생성된 주소는 Settings → Pages에서 확인합니다.
4. 저장소 **Settings → Actions → General → Workflow permissions → Read and write permissions**를 허용해야 할 수 있습니다. 워크플로 파일 자체에 `contents: write`도 선언되어 있습니다. GitHub 조직 제한이 있으면 관리자의 승인이 필요합니다.
5. **Actions → Update official Lotto 6/45 results → Run workflow**를 한 번 실행합니다. 성공하면 `data/draws.json`이 공식 당첨번호 전체 회차로 확장됩니다. 실패 시 기존 데이터는 보존되며 Actions 실행 로그에서 원인을 확인합니다. 동행복권의 비공식 내부 조회 경로가 제한되거나 변경되면 코드를 수정해야 합니다.
6. 이후 주간 자동 실행 일정: 한국시간 **토 22:15**, **일 00:15**, **일 09:15**, **월 09:15**. GitHub Actions 예약 실행은 지연·누락될 수 있고, 장기간 비활성 저장소는 예약 실행이 중지될 수 있습니다. 새 회차 발표가 늦으면 다음 주기에 재시도합니다.
7. 갤럭시 Chrome에서 **메뉴(⋮) → 홈 화면에 추가 / 앱 설치**, iPhone Safari에서 **공유 → 홈 화면에 추가**를 사용합니다. HTTPS 접속에서 서비스워커와 홈 화면 설치가 동작합니다.

## 데이터의 신뢰성과 한계

- 서버 자동 수집: `www.dhlottery.co.kr/lt645/selectPstLt645Info.do` + `selectPstLt645InfoNew.do` (2026년 개편된 공식 공개 응답). 자체 검증 규칙: 범위, 중복, 토요일 날짜, 주간 순서, 연속 회차, 1247회 검증.
- 초기 상태는 제1243~1247회 **5개 회차 예시**입니다. 초기 실행에서 공개 커뮤니티 미러의 역대 데이터에 접근할 수도 있으며 그 경우 **미러임을 화면에 표시**합니다. 이 미러의 결과는 반드시 동행복권 공식 홈페이지에서 최종 대조하세요.
- 공식 서버가 응답하지 않으면 **갱신 실패**로 처리하며 오래된 자료를 최신인 것처럼 표시하지 않습니다. 브라우저 데이터 또는 파일은 그대로 유지됩니다.
- '자동 갱신'은 GitHub Pages가 설치되었다는 전제이며, 단일 HTML 파일을 더블클릭하는 것만으로 매주 백그라운드 수집이 작동하는 것은 아닙니다.
- 생성한 번호 및 사용자 업로드 기록은 **해당 기기와 해당 브라우저의 로컬 저장소**에만 저장됩니다. PC와 휴대폰 간 개인 기록 동기화는 없습니다. 데이터 CSV를 다운로드해 백업할 수 있습니다.
- 빈도/미출현/쌍/AC 등의 통계로 당첨 확률은 올라가지 않습니다. 로또 6/45 모든 서로 다른 6개 조합의 1등 확률은 1/8,145,060입니다.

## 파일 구성

- `index.html`, `styles.css`, `app.js`: 웹앱 본체
- `sw.js`, `manifest.webmanifest`, `icon-*`: PWA 설치 및 오프라인 캐시
- `data/draws.json`: 공식 수집 결과를 보존하는 JSON (현재 5회차 기본 예시)
- `scripts/update_data.py`: 공식 결과 갱신 도구
- `.github/workflows/update-lotto.yml`: GitHub Actions 주간 자동 실행 설정
- `tests/`: 검증 및 회귀 테스트

## 오류 대응

- 자동 갱신 실패: Actions 실행 기록에서 HTTP/JSON 오류 확인, 공식 사이트 개편 여부 확인
- 서버를 열었는데 5개 회차만 보임: Actions 초기 동기화를 실행하거나 전체 CSV를 업로드
- 웹앱 설치 버튼이 없음: HTTPS 및 Chrome/Safari 홈 화면 추가 기능을 사용
- CSV 파일 형식: `drwNo,drwNoDate,n1,n2,n3,n4,n5,n6,bonus`
