"""
ファイル操作に関するユーティリティ関数を提供します。
"""
import os
import sys
import csv
import glob
import pathlib
import shutil
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path  

# アプリケーションディレクトリを取得する関数
def get_application_dir() -> Path:
    """アプリケーションディレクトリを取得します (exe対応)"""
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行可能ファイルのディレクトリ
        return Path(sys.executable).parent
    else:
        # 開発環境での実行
        return Path(__file__).resolve().parents[2]  # .../saitenGiri2021

# プロジェクトルート直下のsettingディレクトリへのパス
BASE_DIR = get_application_dir()
SETTING_DIR = BASE_DIR / "setting"
ANSWER_DATA_DIR = SETTING_DIR / "answerdata"


def resource_path(relative_path: str) -> str:
    """
    リソースファイルへの絶対パスを返します（.exe化対応）
    
    Args:
        relative_path (str): リソースへの相対パス
        
    Returns:
        str: 解決された絶対パス
    """
    try:
        if hasattr(sys, '_MEIPASS'):
            # PyInstallerで実行中
            base = Path(sys._MEIPASS)
            # リソースがある場合はそのパスを返す
            if (base / relative_path).exists():
                return str(base / relative_path)
            
        # 開発環境または_MEIPASSにファイルがない場合
        app_dir = get_application_dir()
        if (app_dir / relative_path).exists():
            return str(app_dir / relative_path)
        
        # それでも見つからない場合、相対パスをそのまま返す
        return relative_path
    
    except Exception as e:
        print(f"リソースパスの解決中にエラー: {e}")
        return relative_path


def ensure_directories() -> None:
    """
    settingディレクトリ以下にinput, output, answerdataを作成します
    """
    (SETTING_DIR / "input").mkdir(parents=True, exist_ok=True)
    (SETTING_DIR / "output").mkdir(parents=True, exist_ok=True)
    (SETTING_DIR / "answerdata").mkdir(parents=True, exist_ok=True)


def initialize_csv_file() -> None:
    """
    ini.csvをsettingディレクトリに作成し、ヘッダーを書き込みます
    """
    path = SETTING_DIR / 'ini.csv'
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y"])


def get_sorted_image_files(directory_path: str) -> List[str]:
    """
    指定されたディレクトリ内のすべての画像ファイルをソートして返します。
    
    Args:
        directory_path (str): 画像ファイルを探すディレクトリパス (glob形式可)
        
    Returns:
        List[str]: ソートされた画像ファイルパスのリスト
    """
    files = glob.glob(directory_path)
    # 特定の拡張子のファイルだけを採用
    image_files = [name for name in files if name.split(
        ".")[-1].lower() in ['jpg', "jpeg", "png", "gif"]]
    image_files.sort()
    return image_files


def folder_walker(folder_path: str, recursive: bool = False, file_ext: str = ".*") -> List[pathlib.Path]:
    """
    指定されたフォルダ内のファイルをリストアップします。
    
    Args:
        folder_path (str): 対象フォルダのパス
        recursive (bool, optional): 再帰的に検索するかどうか。Defaults to False.
        file_ext (str, optional): 対象ファイルの拡張子。Defaults to ".*".
        
    Returns:
        List[pathlib.Path]: ファイルパスのリスト
    """
    p = pathlib.Path(folder_path)
    if recursive:
        return list(p.glob("**/*" + file_ext))
    else:
        return list(p.glob("*" + file_ext))


def backup_file(source_path: str, target_path: str) -> None:
    """
    ファイルをバックアップします。
    
    Args:
        source_path (str): バックアップ元パス
        target_path (str): バックアップ先パス
    """
    try:
        shutil.copy2(source_path, target_path)
    except Exception as e:
        print(f"バックアップに失敗しました: {e}")