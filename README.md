# 회사 정보 자동 요약 도구

회사 이름과 홈페이지 링크를 입력하면, 자동으로 회사 개요, 인재상, 최근 비전 등을 수집하고 요약해주는 GUI 프로그램입니다.

## 주요 기능

- **회사 개요**: 회사의 주요 사업 분야, 규모, 제품/서비스 등
- **인재상**: 회사가 선호하는 인재의 특성과 키워드
- **최근 비전**: 최근 뉴스와 기사를 기반으로 한 회사의 비전과 전략

## 사용 방법

### 1. 환경 설정

1. 프로젝트 루트에 `.env` 파일을 생성합니다.
2. `env_example.txt` 파일을 참고하여 다음 내용을 입력합니다:

```
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_KEY=your_serpapi_key_here  # 선택사항
```

**API 키 발급 방법:**
- **OpenAI API 키** (필수): https://platform.openai.com/api-keys
- **SerpAPI 키** (선택): https://serpapi.com/ (무료 티어 제공)

### 2. 패키지 설치

```bash
# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. 프로그램 실행

```bash
# GUI 버전 실행
python src/gui.py

# 또는 CLI 버전 실행
python src/main.py
```

### 4. 사용

1. GUI 창이 열리면 회사 이름을 입력합니다.
2. (선택) 회사 홈페이지 URL을 입력합니다.
3. "분석 시작" 버튼을 클릭합니다.
4. 결과가 탭별로 표시됩니다:
   - **회사 개요**: 회사의 전반적인 정보
   - **인재상**: 인재상과 키워드
   - **최근 비전**: 최근 뉴스 기반 비전

## exe 파일 생성

프로그램을 exe 파일로 빌드하려면:

```bash
# PyInstaller 설치 (이미 requirements.txt에 포함됨)
pip install pyinstaller

# exe 빌드
python build_exe.py
```

빌드된 exe 파일은 `dist/CompanyInfoSummary.exe`에 생성됩니다.

**참고**: exe 파일을 다른 컴퓨터에서 실행하려면, 같은 폴더에 `.env` 파일을 함께 배포해야 합니다.

## 기술 스택

- **GUI**: Tkinter
- **LLM**: OpenAI API (gpt-4o-mini)
- **웹 검색**: SerpAPI (선택사항)
- **웹 크롤링**: requests + BeautifulSoup
- **빌드**: PyInstaller

## 주의사항

- OpenAI API 사용 시 비용이 발생할 수 있습니다. (gpt-4o-mini는 저렴한 모델입니다)
- SerpAPI는 무료 티어가 있지만, 제한이 있을 수 있습니다.
- 네트워크 연결이 필요합니다.

## 라이선스

MIT License
