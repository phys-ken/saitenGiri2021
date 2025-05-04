import os
import sys
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

# テスト対象のモジュールにパスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.image_utils import (
    calculate_whiteness, 
    resize_image_by_scale,
    create_thumbnail_for_grid,
    get_image_with_score_overlay
)


class TestGridViewFunctions(unittest.TestCase):
    """グリッドビュー関連の機能をテストする"""

    def setUp(self):
        """テストの準備"""
        # テスト用画像の作成
        self.test_image_path = os.path.join(os.path.dirname(__file__), "samples", "答案01.jpg")
        if not os.path.exists(self.test_image_path):
            # テスト画像がなければtests/samplesディレクトリのものを使う
            samples_dir = os.path.join(os.path.dirname(__file__), "samples")
            if not os.path.exists(samples_dir):
                os.makedirs(samples_dir)
            
            # サンプル画像を作成
            test_img = Image.new('RGB', (300, 200), color='white')
            # 画像に線を描画
            pixels = test_img.load()
            for i in range(100, 200):
                for j in range(50, 150):
                    pixels[i, j] = (0, 0, 0)
            
            test_img.save(self.test_image_path)
            self.test_image = test_img
        else:
            self.test_image = Image.open(self.test_image_path)

    def test_calculate_whiteness(self):
        """画像の白さを計算する機能をテスト"""
        # 白い画像の作成
        white_img = Image.new('RGB', (100, 100), color='white')
        whiteness = calculate_whiteness(white_img)
        self.assertAlmostEqual(whiteness, 1.0)
        
        # 黒い画像の作成
        black_img = Image.new('RGB', (100, 100), color='black')
        whiteness = calculate_whiteness(black_img)
        self.assertAlmostEqual(whiteness, 0.0)
        
        # グレーの画像
        gray_img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        whiteness = calculate_whiteness(gray_img)
        self.assertAlmostEqual(whiteness, 0.5, delta=0.05)

    def test_resize_image_by_scale(self):
        """倍率によるサイズ変更機能をテスト"""
        # 元のサイズを確認
        original_width, original_height = self.test_image.size
        
        # 2倍に拡大
        scaled_img = resize_image_by_scale(self.test_image, 2.0)
        self.assertEqual(scaled_img.width, original_width * 2)
        self.assertEqual(scaled_img.height, original_height * 2)
        
        # 0.5倍に縮小
        scaled_img = resize_image_by_scale(self.test_image, 0.5)
        self.assertEqual(scaled_img.width, original_width // 2)
        self.assertEqual(scaled_img.height, original_height // 2)

    def test_create_thumbnail_for_grid(self):
        """グリッド表示用のサムネイル生成をテスト"""
        target_size = 150
        thumbnail = create_thumbnail_for_grid(self.test_image, target_size)
        
        # サムネイルが指定サイズになっていることを確認
        self.assertEqual(thumbnail.width, target_size)
        self.assertEqual(thumbnail.height, target_size)
        
        # 異なるサイズでも確認
        target_size = 200
        thumbnail = create_thumbnail_for_grid(self.test_image, target_size)
        self.assertEqual(thumbnail.width, target_size)
        self.assertEqual(thumbnail.height, target_size)

    def test_get_image_with_score_overlay(self):
        """スコアオーバーレイ機能をテスト"""
        # スコアを表示した画像の作成
        score = "5"
        overlay_img = get_image_with_score_overlay(self.test_image, score)
        
        # 元の画像と同じサイズであることを確認
        self.assertEqual(overlay_img.width, self.test_image.width)
        self.assertEqual(overlay_img.height, self.test_image.height)
        
        # 異なるスコアでも確認
        score = "10"
        overlay_img = get_image_with_score_overlay(self.test_image, score)
        self.assertEqual(overlay_img.width, self.test_image.width)
        self.assertEqual(overlay_img.height, self.test_image.height)


if __name__ == '__main__':
    unittest.main()