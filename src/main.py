import textwrap
import sys

from summarizer import CompanySummarizer


def prompt_user_inputs() -> tuple[str, str | None]:
    """
    Simple interactive prompt for company name and optional URL.
    """
    print("=== 회사 정보 자동 요약 도구 (CLI 버전) ===")
    company_name = input("회사 이름을 입력하세요: ").strip()
    company_url = input("회사 공식 홈페이지 링크(선택, 없으면 엔터): ").strip()
    if not company_url:
        company_url = None
    return company_name, company_url


def print_section(title: str, content: str | None) -> None:
    if not content:
        return
    print()
    print(f"--- {title} ---")
    print(textwrap.fill(content, width=100))


def main() -> None:
    company_name, company_url = prompt_user_inputs()

    if not company_name:
        print("회사 이름은 필수입니다. 프로그램을 종료합니다.")
        return

    try:
        summarizer = CompanySummarizer()
    except ValueError as e:
        print(f"오류: {e}")
        print("\n.env 파일에 OPENAI_API_KEY를 설정해주세요.")
        sys.exit(1)

    # NOTE:
    # 현재 버전은 구조만 잡아둔 상태이며,
    # 실제 웹 검색/크롤링 + 요약(LLM 호출 등) 로직은 `summarizer.py` 안에서 점진적으로 구현하면 됩니다.
    result = summarizer.summarize_company(
        company_name=company_name,
        company_url=company_url,
    )

    print()
    print("=" * 80)
    print(f"[{company_name}] 분석 결과")
    print("=" * 80)

    print_section("회사 개요", result.get("overview"))
    print_section("인재상 / 인재상 키워드", result.get("talent_profile"))
    print_section("최근 기사 기반 비전 / 전략", result.get("recent_vision"))

    print()
    print("완료되었습니다. (이 결과를 기반으로 자소서/면접 준비에 활용해 보세요!)")


if __name__ == "__main__":
    main()
