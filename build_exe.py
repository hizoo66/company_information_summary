"""
PyInstaller를 사용하여 exe 파일을 생성하는 스크립트
"""
import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "CompanyInfoSummary"
MAIN_SCRIPT = "src/gui.py"
ICON_FILE = None  # 아이콘 파일이 있으면 경로 지정

# 빌드 옵션
build_options = [
    f"--name={APP_NAME}",
    "--onefile",  # 단일 exe 파일로 생성
    "--windowed",  # 콘솔 창 숨김 (GUI만 표시)
    "--clean",
    "--noconfirm",  # 기존 빌드 덮어쓰기
    f"--add-data=.env;.",  # .env 파일 포함 (Windows)
    # "--add-data=.env;." if os.name == 'nt' else "--add-data=.env:.",
]

# 아이콘이 있으면 추가
if ICON_FILE and os.path.exists(ICON_FILE):
    build_options.append(f"--icon={ICON_FILE}")

# 숨겨진 import 추가 (필요한 경우)
build_options.extend([
    "--hidden-import=tkinter",
    "--hidden-import=openai",
    "--hidden-import=requests",
    "--hidden-import=bs4",
    "--hidden-import=dotenv",
])

build_options.append(MAIN_SCRIPT)

print("=" * 60)
print(f"{APP_NAME} exe 파일 빌드를 시작합니다...")
print("=" * 60)

try:
    PyInstaller.__main__.run(build_options)
    print("\n빌드 완료!")
    print(f"exe 파일 위치: dist/{APP_NAME}.exe")
except Exception as e:
    print(f"\n빌드 중 오류 발생: {e}")
    print("\nPyInstaller가 설치되어 있는지 확인하세요:")
    print("  pip install pyinstaller")
