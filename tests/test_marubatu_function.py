#!/usr/bin/env python3
"""
〇×△マーク機能のテストスクリプト
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from saitenGiri_new.src.core.marker import AnswerMarker
from saitenGiri_new.src.utils.file_utils import SETTING_DIR

def main():
    """
    テスト実行のメイン関数
    """
    print("==================================================")
    print("〇×△マーク機能テスト")
    print("==================================================")
    
    # 必要なディレクトリの確認
    kaito_dir = SETTING_DIR / "kaitoYousi"
    if not kaito_dir.exists():
        print(f"採点済み画像フォルダが見つかりません: {kaito_dir}")
        print("先に「採点済み画像を出力」機能を実行してください")
        return 1
    
    # 採点済み画像の確認
    image_count = sum(1 for _ in kaito_dir.glob("*.jpg"))
    if image_count == 0:
        print("採点済み画像が見つかりません")
        print("先に「採点済み画像を出力」機能を実行してください")
        return 1
    
    print(f"採点済み画像: {image_count}件")
    
    # マーカーを初期化
    marker = AnswerMarker(
        input_dir=str(SETTING_DIR / "input"),
        output_dir=str(SETTING_DIR / "kaitoYousi"),
        grading_data_path=str(SETTING_DIR / "trimData.csv")
    )
    
    # 〇×△マーク付け処理を実行
    print("〇×△マーク付けを実行中...")
    success = marker.mark_all_answer_sheets_with_symbols()
    
    if not success:
        print("〇×△マーク付けに失敗しました")
        return 1
    
    # 結果確認
    output_dir = SETTING_DIR / "kaitoYousi" / "marubatu"
    result_count = sum(1 for _ in output_dir.glob("*.jpg"))
    
    print(f"〇×△マークを付けた画像: {result_count}件")
    print(f"保存場所: {output_dir}")
    
    if result_count == image_count:
        print("==================================================")
        print("テスト成功: すべての画像に〇×△マークを付けました")
        print("==================================================")
        return 0
    else:
        print("==================================================")
        print("テスト警告: 一部の画像の処理に失敗した可能性があります")
        print("==================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())