"""
採点済み答案出力機能のテスト

以下のテストを行います：
1. settingフォルダを削除し、test_figsから画像をinputフォルダにコピー
2. すべての出力オプション（設問得点・合計得点・〇×マーク）の可能な組み合わせを適用した画像を生成
3. テスト結果をsetting/test/exportに保存
"""
import os
import sys
import shutil
import time
from pathlib import Path
import itertools

# プロジェクトルートへのパスを設定
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'saitenGiri_new'))

# アプリケーションのモジュールをインポート
from saitenGiri_new.src.utils.file_utils import SETTING_DIR, get_sorted_image_files
from saitenGiri_new.src.core.trimmer import ImageTrimmer
from saitenGiri_new.src.core.grader import Grader
from saitenGiri_new.src.core.marker import AnswerMarker


def setup_test_environment():
    """テスト環境をセットアップします"""
    print("="*50)
    print("テスト環境のセットアップを開始します")
    print("="*50)
    
    # settingフォルダが存在する場合は削除
    if SETTING_DIR.exists():
        print(f"既存のsettingフォルダを削除します: {SETTING_DIR}")
        shutil.rmtree(SETTING_DIR)
    
    # 必要なフォルダを作成
    print("フォルダ構造を作成します...")
    os.makedirs(SETTING_DIR / "input", exist_ok=True)
    os.makedirs(SETTING_DIR / "output", exist_ok=True)
    os.makedirs(SETTING_DIR / "export", exist_ok=True)
    os.makedirs(SETTING_DIR / "test" / "export", exist_ok=True)
    
    # test_figsから画像をコピー
    test_figs_dir = Path(project_root) / "test_fig"
    if not test_figs_dir.exists():
        print(f"エラー: テスト画像フォルダが見つかりません: {test_figs_dir}")
        return False
    
    print(f"テスト画像をコピーします: {test_figs_dir} -> {SETTING_DIR / 'input'}")
    for img_file in test_figs_dir.glob("*.jpg"):
        shutil.copy(img_file, SETTING_DIR / "input")
    
    # テスト用のtrimData.csvを作成
    print("テスト用のtrimData.csvを作成します")
    with open(SETTING_DIR / "trimData.csv", "w") as f:
        f.write("tag,x_start,y_start,x_end,y_end\n")
        f.write("name,20,20,200,80\n")
        f.write("Q_0001,20,100,200,160\n")
        f.write("Q_0002,20,180,200,240\n")
        f.write("Q_0003,20,260,200,320\n")
        f.write("Q_0004,20,340,200,400\n")
    
    print("テスト環境のセットアップが完了しました")
    return True


def trim_test_images():
    """テスト用の画像を切り取ります"""
    print("="*50)
    print("テスト用画像の切り取りを開始します")
    print("="*50)
    
    trimmer = ImageTrimmer(
        input_dir=str(SETTING_DIR / "input"),
        output_dir=str(SETTING_DIR / "output")
    )
    success = trimmer.trim_all_images()
    
    if success:
        print("テスト用画像の切り取りが完了しました")
    else:
        print("エラー: テスト用画像の切り取りに失敗しました")
    
    return success


def grade_test_images():
    """テスト用の画像を採点します"""
    print("="*50)
    print("テスト用画像の採点を開始します")
    print("="*50)
    
    # 採点データを手動で作成
    questions = ["Q_0001", "Q_0002", "Q_0003", "Q_0004"]
    scores = [0, 1, 2, 3, "skip"]  # skipを含むスコアの配列
    
    # 各質問ディレクトリを作成
    for q in questions:
        for score in scores:
            score_dir = SETTING_DIR / "output" / q / str(score)
            os.makedirs(score_dir, exist_ok=True)
    
    # 適当な採点結果をファイルに割り当て
    image_files = get_sorted_image_files(str(SETTING_DIR / "input" / "*"))
    image_names = [os.path.basename(img) for img in image_files]
    
    for i, img_name in enumerate(image_names):
        # 画像ごとに異なる採点結果を設定
        q1_score = scores[i % len(scores)]
        q2_score = scores[(i + 1) % len(scores)]
        q3_score = scores[(i + 2) % len(scores)]
        q4_score = scores[(i + 3) % len(scores)]
        
        # 各問題の採点ディレクトリにコピー
        for q, score in zip(questions, [q1_score, q2_score, q3_score, q4_score]):
            src_path = SETTING_DIR / "input" / img_name
            dst_path = SETTING_DIR / "output" / q / str(score) / img_name
            shutil.copy(src_path, dst_path)
    
    print("テスト用画像の採点が完了しました")
    return True


def test_all_export_options():
    """
    すべての出力オプションの組み合わせをテストします
    """
    print("="*50)
    print("採点済み答案出力オプションのテストを開始します")
    print("="*50)
    
    # 可能なオプションの組み合わせを生成
    options = ['question_scores', 'total_score', 'symbols']
    
    # テスト結果ディレクトリ
    test_dir = SETTING_DIR / "test" / "export"
    os.makedirs(test_dir, exist_ok=True)
    
    # 1つも選択しない場合は無効なので、少なくとも1つ以上の選択肢からすべての組み合わせを生成
    valid_combinations = []
    for r in range(1, len(options) + 1):
        valid_combinations.extend(itertools.combinations(options, r))
    
    for combo_id, combo in enumerate(valid_combinations, 1):
        print(f"テスト {combo_id}/{len(valid_combinations)}: {', '.join(combo)}")
        
        # 出力オプションの辞書を作成
        export_options = {opt: (opt in combo) for opt in options}
        
        # 出力ディレクトリ名を作成（オプションの組み合わせを表す）
        dir_name = f"test_{'-'.join(opt[0] for opt in combo)}"  # 例: test_q-t, test_q-s, ...
        export_dir = test_dir / dir_name
        os.makedirs(export_dir, exist_ok=True)
        
        # マーカーインスタンス作成
        marker = AnswerMarker(
            input_dir=str(SETTING_DIR / "input"), 
            output_dir=str(export_dir), 
            grading_data_path=str(SETTING_DIR / "trimData.csv")
        )
        
        # 採点画像の出力
        print(f"出力オプション: {export_options}")
        success = marker.mark_all_answer_sheets(export_options)
        
        if success:
            print(f"テスト {combo_id}: 成功 - 出力先: {export_dir}")
        else:
            print(f"テスト {combo_id}: 失敗")
    
    print("="*50)
    print("すべての出力オプションのテストが完了しました")
    print("テスト結果ディレクトリ:", test_dir)
    print("="*50)


def main():
    """メイン実行関数"""
    print("="*50)
    print("採点済み答案出力機能のテストを開始します")
    print("="*50)
    
    # テスト環境のセットアップ
    if not setup_test_environment():
        print("テスト環境のセットアップに失敗しました。テストを中止します。")
        return
    
    # 画像の切り取り
    if not trim_test_images():
        print("画像の切り取りに失敗しました。テストを中止します。")
        return
    
    # 画像の採点
    if not grade_test_images():
        print("画像の採点に失敗しました。テストを中止します。")
        return
    
    # すべての出力オプションをテスト
    test_all_export_options()
    
    print("="*50)
    print("採点済み答案出力機能のテストが完了しました")
    print("="*50)


if __name__ == "__main__":
    main()