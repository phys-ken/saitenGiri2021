#!/usr/bin/env python3
"""
採点斬りアプリケーションをPyInstallerでexe化するためのビルドスクリプト
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_title():
    # タイトル表示（日本語）
    print("\n")
    print("=" * 50)
    print("  採点斬りアプリケーション ビルドツール")
    print("=" * 50)
    print("\n")

def main():
    print_title()
    
    # カレントディレクトリをプロジェクトルートに設定
    os.chdir(Path(__file__).parent)
    
    # ビルドディレクトリの作成
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    # 既存のビルドディレクトリをクリーンアップ
    for dir_path in [build_dir, dist_dir]:
        if dir_path.exists():
            print(f"{dir_path}ディレクトリを削除中...")
            shutil.rmtree(dir_path)
    
    # PyInstallerコマンドの構築
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=採点斬り2021",
        "--icon=resources/icon.ico",
        "--add-data=resources;resources",  # リソースフォルダを含める
        "main.py"
    ]
    
    # PyInstallerの実行
    print("PyInstallerを実行中...")
    result = subprocess.run(pyinstaller_cmd, check=False)
    
    if result.returncode != 0:
        print("ビルド中にエラーが発生しました。")
        return 1
    
    print("\nビルドが完了しました！")
    print(f"実行ファイルの場所: {dist_dir / '採点斬り2021.exe'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())