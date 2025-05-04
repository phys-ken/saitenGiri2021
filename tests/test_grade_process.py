#!/usr/bin/env python3
"""
採点斬りアプリケーションの機能テスト用スクリプト
GUIを使わずに一連の処理（画像トリミング、採点、Excel出力）をテストします
"""

import os
import shutil
import sys
from pathlib import Path
import random

# プロジェクトのルートパスを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# アプリケーションモジュールのインポート
from saitenGiri_new.src.core.trimmer import ImageTrimmer
from saitenGiri_new.src.core.grader import Grader
from saitenGiri_new.src.core.marker import AnswerMarker
from saitenGiri_new.src.models.answer_sheet import Region
from saitenGiri_new.src.utils.file_utils import SETTING_DIR, ensure_directories


def setup_test_environment():
    """テスト環境のセットアップ（test_figフォルダの画像をsettingフォルダのinputに移動）"""
    print("=== テスト環境のセットアップを開始します ===")
    
    # inputディレクトリを確認・作成
    input_dir = SETTING_DIR / "input"
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
    
    # 既存ファイルをクリア
    for file in input_dir.glob("*.*"):
        if file.is_file():
            file.unlink()
            print(f"削除: {file}")
    
    # test_figフォルダからファイルをコピー
    test_fig_dir = project_root / "test_fig"
    if not test_fig_dir.exists():
        print(f"エラー: テスト画像ディレクトリが見つかりません: {test_fig_dir}")
        return False
    
    count = 0
    for file in test_fig_dir.glob("*.jpg"):
        dst_path = input_dir / file.name
        shutil.copy2(file, dst_path)
        count += 1
        print(f"コピー: {file} → {dst_path}")
    
    if count == 0:
        print("警告: テスト画像が見つかりませんでした")
        return False
    
    print(f"{count}個のテスト画像をコピーしました")
    return True


def create_sample_trimdata():
    """サンプルのトリミング領域データを作成"""
    print("=== サンプルのトリミング領域データを作成します ===")
    
    # サンプルのトリミング領域
    regions = [
        # 一般的に解答用紙での位置を想定した領域
        Region(tag="name", start_x=100, start_y=50, end_x=400, end_y=120),  # 名前欄
        Region(tag="Q_0001", start_x=100, start_y=150, end_x=300, end_y=250),  # 問題1
        Region(tag="Q_0002", start_x=100, start_y=270, end_x=300, end_y=370),  # 問題2
        Region(tag="Q_0003", start_x=100, start_y=390, end_x=300, end_y=490),  # 問題3
        Region(tag="Q_0004", start_x=100, start_y=510, end_x=300, end_y=610),  # 問題4
    ]
    
    # トリマーを初期化してCSVに保存
    trimmer = ImageTrimmer()
    success = trimmer.save_regions_to_csv(regions)
    
    if success:
        print(f"トリミング領域データを保存しました: {len(regions)}件")
    else:
        print("トリミング領域データの保存に失敗しました")
    
    return success


def run_trimming_test():
    """トリミング処理テスト"""
    print("=== トリミング処理をテストします ===")
    
    trimmer = ImageTrimmer()
    success = trimmer.trim_all_images()
    
    if success:
        print("トリミング処理が完了しました")
        # 処理結果の確認
        for region_name in ["name", "Q_0001", "Q_0002", "Q_0003", "Q_0004"]:
            region_dir = os.path.join(trimmer.output_dir, region_name)
            if os.path.exists(region_dir):
                file_count = len([f for f in os.listdir(region_dir) if os.path.isfile(os.path.join(region_dir, f))])
                print(f"- {region_name}: {file_count}個のファイル")
    else:
        print("トリミング処理に失敗しました")
    
    return success


def run_grading_test():
    """採点処理テスト"""
    print("=== 採点処理をテストします ===")
    
    grader = Grader()
    # 問題IDのリストを取得
    question_dirs = grader.get_question_directories()
    q_dirs = [d for d in question_dirs if d.startswith("Q_")]
    
    if not q_dirs:
        print("問題ディレクトリが見つかりません")
        return False
    
    print(f"採点対象の問題: {q_dirs}")
    
    # 各問題に対してランダムに採点
    for q_id in q_dirs:
        # 学生ファイル一覧を取得
        files = grader.get_student_files_for_question(q_id)
        if not files:
            print(f"警告: {q_id}に対するファイルが見つかりません")
            continue
        
        print(f"{q_id}の採点開始: {len(files)}件")
        
        # 各ファイルをランダムに採点
        for file in files:
            # 0, 1, 2, 3, skipのいずれかをランダムに選択
            score = random.choice([0, 1, 2, 3, "skip"])
            success = grader.grade_answer(q_id, file, score)
            if success:
                print(f"  - {file}: {score}点")
            else:
                print(f"  - {file}: 採点失敗")
    
    print("採点処理が完了しました")
    return True


def run_excel_output_test():
    """Excel出力テスト"""
    print("=== Excel出力をテストします ===")
    
    grader = Grader()
    success = grader.create_excel_report()
    
    if success:
        print(f"Excel出力が完了しました: {grader.excel_path}")
    else:
        print("Excel出力に失敗しました")
    
    return success


def run_marker_test():
    """採点結果書き込みテスト"""
    print("=== 採点結果書き込みをテストします ===")
    
    # 出力ディレクトリを作成
    output_dir = os.path.join(SETTING_DIR, "kaitoYousi")
    os.makedirs(output_dir, exist_ok=True)
    
    # グレーダーの出力ディレクトリと同じパスを使用
    grader_output_dir = str(SETTING_DIR / "output")
    
    # マーカーを初期化（すべて絶対パスで指定）
    marker = AnswerMarker(
        input_dir=str(SETTING_DIR / "input"),
        output_dir=output_dir,
        grading_data_path=str(SETTING_DIR / "trimData.csv")
    )
    
    # 採点データをファイルシステムから明示的にロード
    grades = marker.load_grades_from_filesystem(grader_output_dir)
    if not grades:
        print("採点データが見つかりませんでした")
        return False
        
    print(f"採点データを読み込みました: {len(grades)}件")
    marker.grades = grades  # 明示的に採点データを設定
    
    # 領域データを読み込む
    regions = marker.load_grading_data()
    if not regions:
        print("採点領域データが存在しません")
        return False
    
    # 解答用紙を取得
    image_files = []
    input_dir = str(SETTING_DIR / "input")
    try:
        for file in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file)
            if os.path.isfile(file_path) and file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                image_files.append(file_path)
    except Exception as e:
        print(f"解答用紙の取得中にエラーが発生しました: {e}")
        return False
    
    if not image_files:
        print("解答用紙が存在しません")
        return False
    
    print(f"解答用紙を{len(image_files)}個見つけました")
    
    # nameデータを見つける（最初がnameと仮定）
    name_region = None
    for region in regions:
        if region[0] == "name":
            name_region = region
            break
    
    # 採点フォントサイズを決定（適当な値を設定）
    font_size = 50
    
    # 各解答用紙を処理
    output_files = []
    try:
        for image_path in image_files:
            filename = os.path.basename(image_path)
            print(f"処理中: {filename}")
            
            # 画像を読み込む
            from PIL import Image, ImageDraw, ImageFont
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # 採点用フォントを読み込む
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("AppleGothic.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # 合計点を計算
            total_score = 0
            
            # 各領域に得点を書き込む
            for region in regions:
                tag, left, top, right, bottom = region
                
                # nameは処理しない
                if tag == "name":
                    continue
                
                # 得点を取得
                score_text = "?"  # デフォルト値
                if filename in marker.grades and tag in marker.grades[filename]:
                    score = marker.grades[filename][tag]
                    score_text = str(score)
                    
                    # 数値の場合は合計点に加算
                    try:
                        if score != "skip" and isinstance(score, (int, str)) and str(score).isdigit():
                            total_score += int(score)
                    except:
                        pass
                
                # 得点を画像に書き込む
                position = (int(right - font_size/2), int(top))
                draw.text(position, score_text, font=font, fill="red")
                draw.rectangle(
                    (position[0], position[1], position[0] + font_size, position[1] + font_size),
                    outline="red"
                )
            
            # 合計点を書き込む
            if name_region:
                _, left, top, right, bottom = name_region
                position = (int(right - font_size/2), int(top))
                draw.text(position, str(total_score), font=font, fill="red")
                draw.rectangle(
                    (position[0], position[1], position[0] + font_size*1.5, position[1] + font_size),
                    outline="red"
                )
            
            # 採点済み画像を保存
            output_path = os.path.join(output_dir, filename)
            img.save(output_path, quality=95)
            output_files.append(output_path)
            print(f"{filename}の採点マークを完了しました")
        
        print(f"全ての採点マークを完了しました: {len(output_files)}件")
        return True
    except Exception as e:
        print(f"採点結果書き込み中にエラーが発生しました: {e}")
        return False


def check_folder_structure():
    """フォルダ構造のチェック"""
    print("=== フォルダ構造をチェックします ===")
    
    required_folders = [
        SETTING_DIR,
        SETTING_DIR / "input",
        SETTING_DIR / "output",
        SETTING_DIR / "kaitoYousi"
    ]
    
    for folder in required_folders:
        if folder.exists():
            print(f"✓ {folder}: 存在します")
        else:
            print(f"✗ {folder}: 存在しません")
            try:
                folder.mkdir(parents=True, exist_ok=True)
                print(f"  → フォルダを作成しました: {folder}")
            except Exception as e:
                print(f"  → フォルダの作成に失敗しました: {e}")
                return False
    
    return True


def main():
    """メイン処理"""
    print("==================================================")
    print("採点斬りアプリケーション 機能テスト")
    print("==================================================")
    
    # 元のディレクトリを保存
    original_dir = os.getcwd()
    
    try:
        # ディレクトリ構造の確認
        ensure_directories()
        
        # フォルダ構造のチェックと初期化
        if not check_folder_structure():
            print("フォルダ構造の確認と初期化に失敗しました")
            return 1
        
        # テスト環境のセットアップ
        if not setup_test_environment():
            print("テスト環境のセットアップに失敗しました")
            return 1
        
        # トリミング領域データを作成
        if not create_sample_trimdata():
            print("トリミング領域データの作成に失敗しました")
            return 1
        
        # トリミング処理テスト
        if not run_trimming_test():
            print("トリミング処理テストに失敗しました")
            return 1
        
        # 採点処理テスト
        if not run_grading_test():
            print("採点処理テストに失敗しました")
            return 1
        
        # Excel出力テスト
        if not run_excel_output_test():
            print("Excel出力テストに失敗しました")
            return 1
        
        # 採点結果書き込みテスト
        if not run_marker_test():
            print("採点結果書き込みテストに失敗しました")
            return 1
        
        print("==================================================")
        print("全てのテストが正常に完了しました！")
        print("==================================================")
        return 0
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # 元のディレクトリに戻る
        os.chdir(original_dir)


if __name__ == "__main__":
    sys.exit(main())