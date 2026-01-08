import os
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import json
from urllib.parse import quote_plus

# 환경변수 로드
load_dotenv()

# DuckDuckGo는 requests로 직접 크롤링 (라이브러리 불필요)


@dataclass
class CompanySummaryResult:
    overview: Optional[str] = None
    talent_profile: Optional[str] = None
    recent_vision: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overview": self.overview,
            "talent_profile": self.talent_profile,
            "recent_vision": self.recent_vision,
        }


class CompanySummarizer:
    """
    회사 이름 / URL을 기반으로 회사 개요, 인재상, 최근 비전 등을 정리하는 핵심 클래스.

    OpenAI API와 웹검색 API(SerpAPI)를 사용하여 실제 정보를 수집하고 요약합니다.
    """

    def __init__(self):
        # OpenAI API 키 확인 (선택사항)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                print(f"OpenAI 초기화 오류: {e}")

        # SerpAPI 키 (선택사항)
        self.serpapi_key = os.getenv("SERPAPI_KEY")

    def summarize_company(
        self,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        회사 정보를 수집하고 요약합니다.
        OpenAI API가 있으면 요약을 생성하고, 없으면 수집한 정보를 그대로 표시합니다.
        """
        # 1. 웹 검색으로 회사 관련 정보 수집
        search_results = self._search_company_info(company_name, company_url)

        # 2. 회사 홈페이지 크롤링 (URL이 제공된 경우)
        website_content = None
        if company_url:
            website_content = self._fetch_website_content(company_url)

        # 3. OpenAI API가 있으면 요약 생성, 없으면 수집한 정보를 포맷팅
        if self.client:
            overview = self._generate_overview(
                company_name, search_results, website_content
            )
            talent_profile = self._generate_talent_profile(
                company_name, search_results, website_content
            )
            recent_vision = self._generate_recent_vision(company_name, search_results)
        else:
            # OpenAI 없이 수집한 정보를 그대로 포맷팅
            overview = self._format_search_results_as_overview(
                company_name, search_results, website_content
            )
            talent_profile = self._format_search_results_as_talent_profile(
                company_name, search_results, website_content
            )
            recent_vision = self._format_search_results_as_vision(
                company_name, search_results
            )

        result = CompanySummaryResult(
            overview=overview,
            talent_profile=talent_profile,
            recent_vision=recent_vision,
        )
        return result.to_dict()

    def _search_company_info(
        self, company_name: str, company_url: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        SerpAPI, DuckDuckGo 또는 일반 검색을 통해 회사 관련 정보를 수집합니다.
        SerpAPI 키가 있으면 우선 사용하고, 없으면 DuckDuckGo를 사용합니다.
        """
        results = []

        print(f"\n[검색 시작] 회사명: {company_name}")

        # SerpAPI가 있으면 사용 (우선순위 1)
        if self.serpapi_key:
            print("[1단계] SerpAPI 일반 검색 시도 중...")
            try:
                params = {
                    "q": f"{company_name} 회사 소개 인재상",
                    "api_key": self.serpapi_key,
                    "engine": "google",
                    "hl": "ko",
                    "gl": "kr",
                }
                response = requests.get(
                    "https://serpapi.com/search", params=params, timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    # 검색 결과 추출
                    if "organic_results" in data:
                        count = len(data["organic_results"][:5])
                        for item in data["organic_results"][:5]:  # 상위 5개만
                            results.append(
                                {
                                    "title": item.get("title", ""),
                                    "snippet": item.get("snippet", ""),
                                    "link": item.get("link", ""),
                                }
                            )
                        print(f"  ✓ 성공: {count}개의 검색 결과 수집")
                    else:
                        print("  ⚠ 검색 결과 없음")
                else:
                    print(f"  ✗ 실패: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ✗ SerpAPI 검색 오류: {e}")

            # 뉴스 검색 추가
            print("[2단계] SerpAPI 뉴스 검색 시도 중...")
            try:
                params = {
                    "q": f"{company_name} 최근 뉴스 비전 전략",
                    "api_key": self.serpapi_key,
                    "engine": "google",
                    "tbm": "nws",  # 뉴스 검색
                    "hl": "ko",
                    "gl": "kr",
                }
                response = requests.get(
                    "https://serpapi.com/search", params=params, timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if "news_results" in data:
                        count = len(data["news_results"][:3])
                        for item in data["news_results"][:3]:  # 최근 뉴스 3개
                            results.append(
                                {
                                    "title": item.get("title", ""),
                                    "snippet": item.get("snippet", ""),
                                    "link": item.get("link", ""),
                                    "date": item.get("date", ""),
                                }
                            )
                        print(f"  ✓ 성공: {count}개의 뉴스 결과 수집")
                    else:
                        print("  ⚠ 뉴스 검색 결과 없음")
                else:
                    print(f"  ✗ 실패: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ✗ 뉴스 검색 오류: {e}")

        # SerpAPI가 없으면 DuckDuckGo HTML 크롤링 사용 (무료, API 키 불필요)
        if not self.serpapi_key:
            print("[1단계] DuckDuckGo 일반 검색 시도 중...")
            try:
                search_query = f"{company_name} 회사 소개 인재상"
                ddg_results = self._search_duckduckgo_html(search_query, max_results=5)
                for result in ddg_results:
                    results.append(result)
                print(f"  ✓ 성공: {len(ddg_results)}개의 검색 결과 수집")
            except Exception as e:
                print(f"  ✗ DuckDuckGo 검색 오류: {e}")

            # 뉴스 검색
            print("[2단계] DuckDuckGo 뉴스 검색 시도 중...")
            try:
                news_query = f"{company_name} 최근 뉴스 비전 전략"
                news_results = self._search_duckduckgo_html(
                    news_query, max_results=3, is_news=True
                )
                for result in news_results:
                    results.append(result)
                print(f"  ✓ 성공: {len(news_results)}개의 뉴스 결과 수집")
            except Exception as e:
                print(f"  ✗ DuckDuckGo 뉴스 검색 오류: {e}")

        print(f"[검색 완료] 총 {len(results)}개의 결과 수집됨\n")
        return results

    def _search_duckduckgo_html(
        self, query: str, max_results: int = 5, is_news: bool = False
    ) -> List[Dict[str, Any]]:
        """
        DuckDuckGo HTML 페이지를 직접 크롤링하여 검색 결과를 수집합니다.
        """
        results = []
        try:
            # 쿼리 URL 인코딩
            encoded_query = quote_plus(query)

            # DuckDuckGo 검색 URL 구성
            # 임시
            # url = f"https://duckduckgo.com/html/?q={encoded_query}"
            url = f"https://duckduckgo.com/html/?q=미래시스템"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # 인코딩 명시
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")
            print(soup.prettify())
            # DuckDuckGo HTML 구조에 맞게 검색 결과 추출
            # 여러 가능한 클래스명 시도
            result_elements = (
                soup.find_all("div", class_="result")[:max_results]
                or soup.find_all("div", class_="web-result")[:max_results]
                or soup.find_all(
                    "div", {"class": lambda x: x and "result" in x.lower()}
                )[:max_results]
            )

            for element in result_elements:
                # 제목과 링크 추출 (여러 가능한 구조 시도)
                title_elem = (
                    element.find("a", class_="result__a")
                    or element.find("a", class_="result-link")
                    or element.find("h2", class_="result__title")
                    or element.find("a")
                )

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get("href", "")

                    # DuckDuckGo는 리다이렉트 URL을 사용하므로 실제 URL 추출
                    if link.startswith("/l/?kh=") or link.startswith("/l/?"):
                        # 실제 URL 추출 시도
                        try:
                            redirect_url = f"https://duckduckgo.com{link}"
                            redirect_response = requests.head(
                                redirect_url,
                                headers=headers,
                                allow_redirects=True,
                                timeout=5,
                            )
                            if redirect_response.url:
                                link = redirect_response.url
                        except:
                            # 리다이렉트 실패 시 원본 링크 사용
                            pass
                    elif not link.startswith("http"):
                        # 상대 경로인 경우
                        link = f"https://duckduckgo.com{link}"

                    # 스니펫 추출
                    snippet = ""
                    snippet_elem = (
                        element.find("a", class_="result__snippet")
                        or element.find("div", class_="result__snippet")
                        or element.find("span", class_="result__snippet")
                        or element.find("p", class_="result__snippet")
                    )
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)

                    if title:  # 제목이 있는 경우만 추가
                        result_dict = {
                            "title": title,
                            "snippet": snippet,
                            "link": link,
                        }

                        # 뉴스인 경우 날짜 정보 추가 시도
                        if is_news:
                            date_elem = element.find(
                                "span", class_="result__date"
                            ) or element.find("time")
                            if date_elem:
                                result_dict["date"] = date_elem.get_text(strip=True)
                            else:
                                result_dict["date"] = ""

                        results.append(result_dict)
                        if len(results) >= max_results:
                            break

        except Exception as e:
            print(f"    DuckDuckGo HTML 파싱 오류: {e}")

        return results

    def _fetch_website_content(self, url: str) -> Optional[str]:
        """
        회사 홈페이지의 주요 내용을 크롤링합니다.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 불필요한 태그 제거
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # 주요 텍스트 추출
            text = soup.get_text(separator=" ", strip=True)
            # 너무 긴 경우 앞부분만
            return text[:5000] if len(text) > 5000 else text

        except Exception as e:
            print(f"웹사이트 크롤링 오류: {e}")
            return None

    def _format_openai_error(self, error: Exception, section_name: str) -> str:
        """
        OpenAI API 오류를 사용자 친화적인 메시지로 변환합니다.
        """
        error_str = str(error)

        # 할당량 초과 오류
        if "insufficient_quota" in error_str or "429" in error_str:
            return f"""❌ {section_name} 생성 실패: OpenAI API 할당량 초과

현재 OpenAI API 계정의 크레딧이 부족하거나 할당량을 초과했습니다.

해결 방법:
1. OpenAI 대시보드에서 계정 상태 확인: https://platform.openai.com/account/usage
2. 결제 정보를 추가하거나 크레딧을 충전하세요
3. 또는 다른 OpenAI API 키를 사용하세요

자세한 정보: https://platform.openai.com/docs/guides/error-codes/api-errors"""

        # 인증 오류
        elif "invalid_api_key" in error_str or "401" in error_str:
            return f"""❌ {section_name} 생성 실패: OpenAI API 키 오류

API 키가 유효하지 않거나 만료되었습니다.

해결 방법:
1. .env 파일의 OPENAI_API_KEY가 올바른지 확인하세요
2. https://platform.openai.com/api-keys 에서 새 API 키를 발급받으세요"""

        # 기타 오류
        else:
            return f"""❌ {section_name} 생성 중 오류 발생

오류 내용: {error_str}

문제가 지속되면:
- 네트워크 연결을 확인하세요
- OpenAI 서비스 상태를 확인하세요: https://status.openai.com/
- API 키와 계정 상태를 확인하세요"""

    def _generate_overview(
        self,
        company_name: str,
        search_results: List[Dict],
        website_content: Optional[str],
    ) -> str:
        """
        OpenAI를 사용하여 회사 개요를 생성합니다.
        """
        # 컨텍스트 구성
        context = f"회사 이름: {company_name}\n\n"

        if search_results:
            context += "검색 결과:\n"
            for i, result in enumerate(search_results[:5], 1):
                context += f"{i}. {result.get('title', '')}\n"
                context += f"   {result.get('snippet', '')}\n\n"

        if website_content:
            context += f"\n회사 홈페이지 내용 (일부):\n{website_content[:2000]}\n"

        prompt = f"""다음 정보를 바탕으로 {company_name}의 회사 개요를 한국어로 작성해주세요.
회사 개요에는 다음 내용이 포함되어야 합니다:
- 회사의 주요 사업 분야
- 회사의 규모와 위치
- 회사의 주요 제품/서비스
- 회사의 특징이나 강점

정보:
{context}

회사 개요를 3-5문단으로 작성해주세요. 객관적이고 정확한 정보만 포함해주세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 회사 정보를 분석하고 요약하는 전문가입니다.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = self._format_openai_error(e, "회사 개요")
            return error_msg

    def _generate_talent_profile(
        self,
        company_name: str,
        search_results: List[Dict],
        website_content: Optional[str],
    ) -> str:
        """
        OpenAI를 사용하여 인재상을 생성합니다.
        """
        context = f"회사 이름: {company_name}\n\n"

        # 인재상 관련 검색 결과 필터링
        talent_results = [
            r
            for r in search_results
            if any(
                keyword in r.get("title", "").lower() + r.get("snippet", "").lower()
                for keyword in ["인재상", "채용", "인재", "인사", "인재상", "인재관"]
            )
        ]

        if talent_results:
            context += "인재상 관련 정보:\n"
            for result in talent_results[:3]:
                context += f"- {result.get('title', '')}: {result.get('snippet', '')}\n"

        if website_content and (
            "인재상" in website_content or "채용" in website_content
        ):
            # 인재상 관련 부분만 추출
            context += f"\n홈페이지 인재상 관련 내용:\n{website_content[:1500]}\n"

        prompt = f"""다음 정보를 바탕으로 {company_name}의 인재상과 인재상 키워드를 한국어로 작성해주세요.
인재상에는 다음 내용이 포함되어야 합니다:
- 회사가 선호하는 인재의 특성
- 인재상 키워드 (3-5개)
- 회사가 중시하는 가치관이나 역량

정보:
{context}

인재상을 2-4문단으로 작성하고, 마지막에 "인재상 키워드: [키워드1, 키워드2, ...]" 형식으로 정리해주세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 회사 인재상을 분석하는 전문가입니다.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = self._format_openai_error(e, "인재상")
            return error_msg

    def _generate_recent_vision(
        self, company_name: str, search_results: List[Dict]
    ) -> str:
        """
        OpenAI를 사용하여 최근 비전을 생성합니다.
        """
        # 뉴스/최근 기사 필터링
        news_results = [
            r
            for r in search_results
            if r.get("date")
            or "뉴스" in r.get("title", "").lower()
            or "기사" in r.get("title", "").lower()
        ]

        context = f"회사 이름: {company_name}\n\n"

        if news_results:
            context += "최근 뉴스/기사:\n"
            for result in news_results[:5]:
                date = result.get("date", "날짜 미상")
                context += f"- [{date}] {result.get('title', '')}\n"
                context += f"  {result.get('snippet', '')}\n\n"
        else:
            # 일반 검색 결과 중 비전/전략 관련
            vision_results = [
                r
                for r in search_results
                if any(
                    keyword in r.get("title", "").lower() + r.get("snippet", "").lower()
                    for keyword in ["비전", "전략", "목표", "방향", "미래"]
                )
            ]
            if vision_results:
                context += "비전/전략 관련 정보:\n"
                for result in vision_results[:3]:
                    context += (
                        f"- {result.get('title', '')}: {result.get('snippet', '')}\n"
                    )

        prompt = f"""다음 정보를 바탕으로 {company_name}의 최근 비전과 전략을 한국어로 작성해주세요.
최근 비전에는 다음 내용이 포함되어야 합니다:
- 회사의 최근 발표된 비전이나 목표
- 중장기 전략 방향
- 최근 주요 이슈나 변화

정보:
{context}

최근 비전을 3-5문단으로 작성해주세요. 최근 뉴스나 기사를 기반으로 한 구체적인 내용을 포함해주세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 회사 비전과 전략을 분석하는 전문가입니다.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = self._format_openai_error(e, "최근 비전")
            return error_msg

    def _format_search_results_as_overview(
        self,
        company_name: str,
        search_results: List[Dict],
        website_content: Optional[str],
    ) -> str:
        """
        OpenAI 없이 수집한 검색 결과를 회사 개요 형식으로 포맷팅합니다.
        """
        text = f"=== {company_name} 회사 개요 ===\n\n"

        if not search_results and not website_content:
            return (
                text
                + "검색 결과를 찾을 수 없습니다. 회사 홈페이지 URL을 입력하시면 더 많은 정보를 얻을 수 있습니다."
            )

        if search_results:
            text += "【검색 결과】\n\n"
            for i, result in enumerate(search_results[:5], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")

                text += f"{i}. {title}\n"
                if snippet:
                    text += f"   {snippet}\n"
                if link:
                    text += f"   링크: {link}\n"
                text += "\n"

        if website_content:
            text += "\n【회사 홈페이지 내용】\n\n"
            # 홈페이지 내용의 앞부분만 표시
            preview = website_content[:2000]
            if len(website_content) > 2000:
                preview += "... (내용이 길어 일부만 표시됩니다)"
            text += preview

        return text

    def _format_search_results_as_talent_profile(
        self,
        company_name: str,
        search_results: List[Dict],
        website_content: Optional[str],
    ) -> str:
        """
        OpenAI 없이 수집한 검색 결과를 인재상 형식으로 포맷팅합니다.
        """
        text = f"=== {company_name} 인재상 ===\n\n"

        # 인재상 관련 검색 결과 필터링
        talent_results = [
            r
            for r in search_results
            if any(
                keyword in r.get("title", "").lower() + r.get("snippet", "").lower()
                for keyword in ["인재상", "채용", "인재", "인사", "인재관"]
            )
        ]

        if talent_results:
            text += "【인재상 관련 검색 결과】\n\n"
            for i, result in enumerate(talent_results[:5], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")

                text += f"{i}. {title}\n"
                if snippet:
                    text += f"   {snippet}\n"
                if link:
                    text += f"   링크: {link}\n"
                text += "\n"
        else:
            text += "인재상 관련 검색 결과를 찾을 수 없습니다.\n\n"

        if website_content and (
            "인재상" in website_content or "채용" in website_content
        ):
            text += "\n【홈페이지 인재상 관련 내용】\n\n"
            # 인재상 관련 부분 찾기
            lines = website_content.split("\n")
            talent_lines = [
                line
                for line in lines
                if "인재상" in line or "채용" in line or "인재" in line
            ]
            if talent_lines:
                text += "\n".join(talent_lines[:10])  # 최대 10줄
            else:
                text += website_content[:1000]  # 관련 내용이 없으면 앞부분만

        if not talent_results and not (
            website_content
            and ("인재상" in website_content or "채용" in website_content)
        ):
            text += "\n💡 팁: 회사 홈페이지의 채용 페이지나 인재상 페이지 URL을 입력하시면 더 정확한 정보를 얻을 수 있습니다."

        return text

    def _format_search_results_as_vision(
        self,
        company_name: str,
        search_results: List[Dict],
    ) -> str:
        """
        OpenAI 없이 수집한 검색 결과를 최근 비전 형식으로 포맷팅합니다.
        """
        text = f"=== {company_name} 최근 비전 및 전략 ===\n\n"

        # 뉴스/최근 기사 필터링
        news_results = [
            r
            for r in search_results
            if r.get("date")
            or "뉴스" in r.get("title", "").lower()
            or "기사" in r.get("title", "").lower()
        ]

        if news_results:
            text += "【최근 뉴스/기사】\n\n"
            for i, result in enumerate(news_results[:5], 1):
                date = result.get("date", "날짜 미상")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")

                text += f"{i}. [{date}] {title}\n"
                if snippet:
                    text += f"   {snippet}\n"
                if link:
                    text += f"   링크: {link}\n"
                text += "\n"
        else:
            # 일반 검색 결과 중 비전/전략 관련
            vision_results = [
                r
                for r in search_results
                if any(
                    keyword in r.get("title", "").lower() + r.get("snippet", "").lower()
                    for keyword in ["비전", "전략", "목표", "방향", "미래"]
                )
            ]

            if vision_results:
                text += "【비전/전략 관련 정보】\n\n"
                for i, result in enumerate(vision_results[:5], 1):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")

                    text += f"{i}. {title}\n"
                    if snippet:
                        text += f"   {snippet}\n"
                    if link:
                        text += f"   링크: {link}\n"
                    text += "\n"
            else:
                text += "최근 비전/전략 관련 정보를 찾을 수 없습니다.\n\n"
                if search_results:
                    text += "【일반 검색 결과】\n\n"
                    for i, result in enumerate(search_results[:3], 1):
                        title = result.get("title", "")
                        snippet = result.get("snippet", "")
                        link = result.get("link", "")

                        text += f"{i}. {title}\n"
                        if snippet:
                            text += f"   {snippet}\n"
                        if link:
                            text += f"   링크: {link}\n"
                        text += "\n"

        return text
