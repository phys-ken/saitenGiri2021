"""
採点斬りアプリケーションのエントリーポイント
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# 開発時のインポートを可能にするためのパス設定
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.main_window import MainWindow
from src.utils.file_utils import resource_path


def check_dependencies():
    """
    必要な依存ライブラリをチェックします
    """
    missing_deps = []
    
    # OpenCVチェック
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    # NumPyチェック
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    if missing_deps:
        # 依存関係が足りない場合は警告を表示
        deps_str = ", ".join(missing_deps)
        messagebox.showwarning(
            "ライブラリが不足しています", 
            f"以下のライブラリが見つかりません: {deps_str}\n\n"
            f"〇×△マーク機能を使用するには必要です。\n"
            f"次のコマンドでインストールしてください:\n"
            f"pip install {' '.join(missing_deps)}"
        )
        print(f"警告: 以下のライブラリが見つかりません: {deps_str}")
    
    return len(missing_deps) == 0


def main():
    """
    アプリケーションのメイン関数
    """
    # 現在の作業ディレクトリを保存
    original_dir = os.getcwd()
    
    try:
        # tkinterのルートウィンドウを作成
        root = tk.Tk()
        
        # アイコンの設定
        try:
            icon_path = resource_path("resources/icon.ico")
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"アイコンの読み込みに失敗しました: {e}")
        
        # 依存関係チェック (起動は妨げない)
        check_dependencies()
        
        # メインウィンドウを作成
        app = MainWindow(root)
        
        # アプリケーションを実行
        app.run()
        
    finally:
        # 作業ディレクトリを元に戻す
        os.chdir(original_dir)


if __name__ == "__main__":
    main()