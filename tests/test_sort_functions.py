import os
import sys
import unittest
from pathlib import Path
from PIL import Image
import shutil
import tempfile

# テスト対象のモジュールにパスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.image_utils import calculate_whiteness


class TestSortFunctions(unittest.TestCase):
    """
    画像のソート機能をテストするクラス
    実際のグリッドビューのソートロジックをシミュレート
    """

    def setUp(self):
        """テストの準備"""
        # 一時ディレクトリの作成
        self.test_dir = tempfile.mkdtemp()
        self.samples_dir = os.path.join(os.path.dirname(__file__), "samples")
        
        # テスト用の画像ファイル
        self.test_images = []
        self.whiteness_dict = {}  # 画像の白さを保存する辞書
        self.score_dict = {}  # テスト用のスコアデータ
        
        # テスト用の画像を作成
        for i in range(5):
            # 白さが異なる画像を作成（iが大きいほど黒い領域が多い）
            img = Image.new('RGB', (100, 100), color='white')
            pixels = img.load()
            for x in range(i * 20):
                for y in range(i * 20):
                    pixels[x, y] = (0, 0, 0)
            
            # ファイル名
            filename = f"test{i+1}.jpg"
            filepath = os.path.join(self.test_dir, filename)
            
            # 画像を保存
            img.save(filepath)
            self.test_images.append(filepath)
            
            # 白さを計算して保存
            self.whiteness_dict[filepath] = calculate_whiteness(img)
            
            # スコア（テスト用。順序が分かりやすいように設定）
            self.score_dict[filepath] = str((5 - i) % 5)  # 5,4,3,2,1の順
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir)
    
    def test_filename_sort(self):
        """ファイル名順のソートをテスト"""
        # ファイル名順にソート
        sorted_files = sorted(self.test_images, key=lambda x: os.path.basename(x))
        
        # ソート結果を検証
        for i, filepath in enumerate(sorted_files):
            self.assertEqual(os.path.basename(filepath), f"test{i+1}.jpg")
    
    def test_whiteness_sort(self):
        """白さ順のソートをテスト"""
        # 白さ順にソート（白いものが先）
        sorted_files = sorted(self.test_images, 
                             key=lambda x: self.whiteness_dict.get(x, 0.0),
                             reverse=True)
        
        # 白さの値が降順になっているか確認
        for i in range(len(sorted_files) - 1):
            current = self.whiteness_dict[sorted_files[i]]
            next_val = self.whiteness_dict[sorted_files[i+1]]
            self.assertGreaterEqual(current, next_val)
    
    def test_score_sort_asc(self):
        """点数の昇順ソートをテスト"""
        # 点数順（昇順）にソート
        def get_numeric_score(path):
            score = self.score_dict.get(path, "")
            if score == "skip":
                return -1
            try:
                return int(score) if score else 0
            except:
                return 0
                
        sorted_files = sorted(self.test_images, key=get_numeric_score)
        
        # ソート結果を検証
        for i in range(len(sorted_files) - 1):
            current = get_numeric_score(sorted_files[i])
            next_val = get_numeric_score(sorted_files[i+1])
            self.assertLessEqual(current, next_val)
    
    def test_score_sort_desc(self):
        """点数の降順ソートをテスト"""
        # 点数順（降順）にソート
        def get_numeric_score(path):
            score = self.score_dict.get(path, "")
            if score == "skip":
                return -1
            try:
                return int(score) if score else 0
            except:
                return 0
                
        sorted_files = sorted(self.test_images, key=get_numeric_score, reverse=True)
        
        # ソート結果を検証
        for i in range(len(sorted_files) - 1):
            current = get_numeric_score(sorted_files[i])
            next_val = get_numeric_score(sorted_files[i+1])
            self.assertGreaterEqual(current, next_val)


if __name__ == '__main__':
    unittest.main()