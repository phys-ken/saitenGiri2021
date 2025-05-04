import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# パスを追加して、プロジェクトのコードをインポートできるようにする
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'saitenGiri_new'))

from saitenGiri_new.src.core.grader import Grader
from saitenGiri_new.src.utils.file_utils import SETTING_DIR


class TestTempFileGeneration(unittest.TestCase):
    """一時ファイル(temp_から始まるファイル)の生成を特定するためのテスト"""

    def setUp(self):
        """テスト用のディレクトリ構造を作成"""
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp(prefix="test_saiten_")
        
        # ディレクトリ構造を作成
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # テスト用のname/フォルダとQ_0001フォルダを作成
        self.name_dir = os.path.join(self.output_dir, "name")
        os.makedirs(self.name_dir, exist_ok=True)
        
        self.question_dir = os.path.join(self.output_dir, "Q_0001")
        os.makedirs(self.question_dir, exist_ok=True)
        
        # Q_0001/0フォルダ（スコア用）を作成
        self.score_dir = os.path.join(self.question_dir, "0")
        os.makedirs(self.score_dir, exist_ok=True)
        
        # テスト用の画像を用意
        test_img_dir = os.path.join(os.path.dirname(__file__), '..', 'test_fig')
        if os.path.exists(test_img_dir):
            test_img = os.path.join(test_img_dir, '答案01.jpg')
            if os.path.exists(test_img):
                # nameフォルダとQ_0001フォルダにテスト画像をコピー
                shutil.copy(test_img, os.path.join(self.name_dir, '答案01.jpg'))
                shutil.copy(test_img, os.path.join(self.score_dir, '答案01.jpg'))
        
        # 元のカレントディレクトリを保存
        self.original_dir = os.getcwd()
        
        # Excelファイルの保存先
        self.excel_path = os.path.join(self.test_dir, "test_report.xlsx")
        
        print(f"テストディレクトリ構造を作成しました: {self.test_dir}")

    def tearDown(self):
        """テスト後の後片付け"""
        # 元のディレクトリに戻る
        os.chdir(self.original_dir)
        
        # テスト用の一時ディレクトリを削除
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        print("テストディレクトリを削除しました")

    def find_temp_files(self, directory=None):
        """指定ディレクトリ内のtemp_から始まるファイルを検索"""
        if directory is None:
            directory = os.getcwd()
            
        temp_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith("temp_"):
                    temp_files.append(os.path.join(root, file))
        
        return temp_files

    def test_excel_report_generation(self):
        """Excelレポート生成時の一時ファイル生成を検証"""
        # テスト前に一時ファイルがないことを確認
        before_temp_files = self.find_temp_files()
        print(f"テスト前の一時ファイル: {before_temp_files}")
        
        # Graderオブジェクトを作成
        grader = Grader(output_dir=self.output_dir, excel_path=self.excel_path)
        
        # レポート生成前のディレクトリ内容を記録
        print(f"レポート生成前のファイル一覧:")
        self.print_directory_content(self.test_dir)
        
        # レポート生成を実行
        print("Excelレポートを生成します")
        grader.create_excel_report()
        
        # レポート生成後のディレクトリ内容を記録
        print(f"レポート生成後のファイル一覧:")
        self.print_directory_content(self.test_dir)
        
        # 生成後の一時ファイルを検索
        after_temp_files = self.find_temp_files()
        print(f"テスト後の一時ファイル: {after_temp_files}")
        
        # 検証結果のレポート
        if after_temp_files != before_temp_files:
            print("新しい一時ファイルが生成されました:")
            for temp_file in after_temp_files:
                if temp_file not in before_temp_files:
                    print(f"- {temp_file}")
                    
            # 生成された一時ファイルのサイズを確認
            for temp_file in after_temp_files:
                if temp_file not in before_temp_files and os.path.exists(temp_file):
                    print(f"ファイル {temp_file} のサイズ: {os.path.getsize(temp_file)} バイト")

    def print_directory_content(self, directory):
        """ディレクトリ内のファイルとサブディレクトリを表示"""
        for root, dirs, files in os.walk(directory):
            print(f"ディレクトリ: {root}")
            if files:
                print("  ファイル:")
                for file in files:
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path) if os.path.exists(file_path) else "不明"
                    print(f"    - {file} (サイズ: {size} バイト)")


if __name__ == "__main__":
    unittest.main()