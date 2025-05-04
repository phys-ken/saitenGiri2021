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
  
# プロジェクトルート直下のsettingディレクトリへのパス
BASE_DIR = Path(__file__).resolve().parents[2]  # .../saitenGiri_new
SETTING_DIR = BASE_DIR / "setting"


def resource_path(relative_path: str) -> str:
    """
    リソースファイルへの絶対パスを返します（.exe化対応）
    
    Args:
        relative_path (str): リソースへの相対パス
        
    Returns:
        str: 解決された絶対パス
    """
    if hasattr(sys, '_MEIPASS'):
        base = Path(sys._MEIPASS)
    else:
        base = BASE_DIR
    return str(base / relative_path)


def ensure_directories() -> None:
    """
    settingディレクトリ以下にinput, outputを作成します
    """
    (SETTING_DIR / "input").mkdir(parents=True, exist_ok=True)
    (SETTING_DIR / "output").mkdir(parents=True, exist_ok=True)


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