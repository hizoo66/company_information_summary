import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from typing import Optional
from summarizer import CompanySummarizer


class CompanyInfoGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("회사 정보 자동 요약 도구")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        try:
            self.summarizer = CompanySummarizer()
            # OpenAI API가 없어도 동작 가능 (검색 결과만 표시)
        except Exception as e:
            messagebox.showwarning(
                "알림",
                f"초기화 중 오류가 발생했습니다:\n{str(e)}\n\n"
                "OpenAI API 키가 없어도 검색 결과는 확인할 수 있습니다.",
            )
            self.summarizer = None

        self._create_widgets()

    def _create_widgets(self):
        # 상단 프레임 - 입력 영역
        input_frame = ttk.LabelFrame(self.root, text="회사 정보 입력", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # 회사 이름 입력
        ttk.Label(input_frame, text="회사 이름:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.company_name_entry = ttk.Entry(input_frame, width=50)
        self.company_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        # 회사 URL 입력
        ttk.Label(input_frame, text="회사 홈페이지 (선택):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.company_url_entry = ttk.Entry(input_frame, width=50)
        self.company_url_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        input_frame.columnconfigure(1, weight=1)

        # 분석 버튼
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.analyze_button = ttk.Button(
            button_frame, text="분석 시작", command=self._start_analysis
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(button_frame, mode="indeterminate", length=200)
        self.progress.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(button_frame, text="대기 중...")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 결과 영역 - 탭으로 구성
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 회사 개요 탭
        self.overview_text = scrolledtext.ScrolledText(
            notebook, wrap=tk.WORD, width=80, height=20, font=("맑은 고딕", 10)
        )
        notebook.add(self.overview_text, text="회사 개요")

        # 인재상 탭
        self.talent_text = scrolledtext.ScrolledText(
            notebook, wrap=tk.WORD, width=80, height=20, font=("맑은 고딕", 10)
        )
        notebook.add(self.talent_text, text="인재상")

        # 최근 비전 탭
        self.vision_text = scrolledtext.ScrolledText(
            notebook, wrap=tk.WORD, width=80, height=20, font=("맑은 고딕", 10)
        )
        notebook.add(self.vision_text, text="최근 비전")

    def _start_analysis(self):
        if self.summarizer is None:
            messagebox.showerror(
                "설정 오류",
                "API 키가 설정되지 않아 분석을 시작할 수 없습니다.\n"
                ".env 파일에 OPENAI_API_KEY를 설정해주세요.",
            )
            return

        company_name = self.company_name_entry.get().strip()
        company_url = self.company_url_entry.get().strip() or None

        if not company_name:
            messagebox.showwarning("입력 오류", "회사 이름을 입력해주세요.")
            return

        # UI 비활성화
        self.analyze_button.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="분석 중...")

        # 결과 영역 초기화
        self.overview_text.delete(1.0, tk.END)
        self.talent_text.delete(1.0, tk.END)
        self.vision_text.delete(1.0, tk.END)

        # 별도 스레드에서 분석 실행
        thread = threading.Thread(
            target=self._analyze_company, args=(company_name, company_url), daemon=True
        )
        thread.start()

    def _analyze_company(self, company_name: str, company_url: Optional[str]):
        try:
            result = self.summarizer.summarize_company(
                company_name=company_name, company_url=company_url
            )

            # UI 업데이트는 메인 스레드에서
            self.root.after(0, self._update_results, result)

        except Exception as e:
            error_msg = f"분석 중 오류가 발생했습니다: {str(e)}"
            self.root.after(0, self._show_error, error_msg)

    def _update_results(self, result: dict):
        self.progress.stop()
        self.analyze_button.config(state=tk.NORMAL)
        self.status_label.config(text="완료!")

        # 결과 표시
        if result.get("overview"):
            self.overview_text.insert(1.0, result["overview"])

        if result.get("talent_profile"):
            self.talent_text.insert(1.0, result["talent_profile"])

        if result.get("recent_vision"):
            self.vision_text.insert(1.0, result["recent_vision"])

    def _show_error(self, error_msg: str):
        self.progress.stop()
        self.analyze_button.config(state=tk.NORMAL)
        self.status_label.config(text="오류 발생")
        messagebox.showerror("오류", error_msg)


def main():
    root = tk.Tk()
    app = CompanyInfoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
