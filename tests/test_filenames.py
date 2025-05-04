import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# パスを追加して、プロジェクトのコードをインポートできるようにする
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'saitenGiri_new'))

from saitenGiri_new.src.utils.file_utils import (
    get_sorted_image_files, 
    folder_walker, 
    BASE_DIR
)


class TestFilenames(unittest.TestCase):
    """ファイル名の処理に関するテスト"""

    def setUp(self):
        """テスト用のディレクトリ構造を作成"""
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp(prefix="test_filenames_")
        
        # テスト用のファイルを作成
        self.create_test_files()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # テスト用の一時ディレクトリを削除
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """テスト用のファイルを作成する"""
        # 通常のファイル
        self.normal_files = [
            "答案01.jpg", "答案02.jpg", "答案10.jpg", "答案05.jpg",
            "test1.png", "test2.png", "test10.png", "test20.png",
        ]
        
        # 特殊文字を含むファイル
        self.special_files = [
            "file-with-dash.jpg",
            "file_with_underscore.jpg",
            "file with spaces.jpg",
            "file.with.dots.jpg",
            "file(with)parentheses.jpg",
        ]
        
        # 日本語ファイル名
        self.japanese_files = [
            "テスト画像01.jpg",
            "試験回答02.png",
            "採点用03.gif",
            "回答_特殊文字.jpg",
        ]
        
        # テスト用のディレクトリ作成
        self.normal_dir = os.path.join(self.test_dir, "normal")
        self.special_dir = os.path.join(self.test_dir, "special")
        self.japanese_dir = os.path.join(self.test_dir, "japanese")
        
        os.makedirs(self.normal_dir, exist_ok=True)
        os.makedirs(self.special_dir, exist_ok=True)
        os.makedirs(self.japanese_dir, exist_ok=True)
        
        # ファイルを作成する（中身は空）
        for filename in self.normal_files:
            with open(os.path.join(self.normal_dir, filename), 'w') as f:
                pass
                
        for filename in self.special_files:
            with open(os.path.join(self.special_dir, filename), 'w') as f:
                pass
                
        for filename in self.japanese_files:
            with open(os.path.join(self.japanese_dir, filename), 'w') as f:
                pass
    
    def test_sorted_image_files(self):
        """get_sorted_image_filesの動作確認"""
        # 通常のファイル名でソートが正しく行われるか
        sorted_files = get_sorted_image_files(os.path.join(self.normal_dir, "*.jpg"))
        
        # ファイル名を取得（パスを除く）
        sorted_filenames = [os.path.basename(f) for f in sorted_files]
        
        # 期待される順序
        expected = ["答案01.jpg", "答案02.jpg", "答案05.jpg", "答案10.jpg"]
        self.assertEqual(sorted_filenames, expected)
        
        # PNGファイル
        sorted_png = get_sorted_image_files(os.path.join(self.normal_dir, "*.png"))
        sorted_png_names = [os.path.basename(f) for f in sorted_png]
        expected_png = ["test1.png", "test2.png", "test10.png", "test20.png"]
        self.assertEqual(sorted_png_names, expected_png)
    
    def test_special_characters(self):
        """特殊文字を含むファイル名の処理"""
        special_files = get_sorted_image_files(os.path.join(self.special_dir, "*.jpg"))
        
        # すべてのファイルが正しく認識されていることを確認
        self.assertEqual(len(special_files), len(self.special_files))
        
        # 各ファイルが存在することを確認
        for filename in self.special_files:
            file_path = os.path.join(self.special_dir, filename)
            self.assertTrue(os.path.exists(file_path))
    
    def test_japanese_filenames(self):
        """日本語ファイル名の処理"""
        # 日本語ファイル名のJPGファイルを取得
        jpg_files = get_sorted_image_files(os.path.join(self.japanese_dir, "*.jpg"))
        jpg_names = [os.path.basename(f) for f in jpg_files]
        
        expected_jpg = ["テスト画像01.jpg", "回答_特殊文字.jpg"]
        self.assertEqual(set(jpg_names), set(expected_jpg))
        
        # 日本語ファイル名のPNGファイルを取得
        png_files = get_sorted_image_files(os.path.join(self.japanese_dir, "*.png"))
        png_names = [os.path.basename(f) for f in png_files]
        
        expected_png = ["試験回答02.png"]
        self.assertEqual(png_names, expected_png)
    
    def test_folder_walker(self):
        """folder_walker関数のテスト"""
        # 非再帰的に全ての画像ファイルを取得
        all_files = folder_walker(self.normal_dir, recursive=False, file_ext=".*")
        self.assertEqual(len(all_files), len(self.normal_files))
        
        # JPGファイルのみ取得
        jpg_files = folder_walker(self.normal_dir, recursive=False, file_ext=".jpg")
        jpg_count = len([f for f in self.normal_files if f.endswith(".jpg")])
        self.assertEqual(len(jpg_files), jpg_count)
        
        # 日本語ディレクトリのテスト
        japanese_files = folder_walker(self.japanese_dir, recursive=False, file_ext=".jpg")
        self.assertEqual(len(japanese_files), 2)  # テスト画像01.jpgと回答_特殊文字.jpg


if __name__ == "__main__":
    unittest.main()