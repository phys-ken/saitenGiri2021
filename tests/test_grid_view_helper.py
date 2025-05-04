"""
GUIなしでグリッドビュー機能をテストするヘルパースクリプト
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from PIL import Image

# テスト対象のモジュールにパスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.image_utils import (
    calculate_whiteness, 
    resize_image_by_scale,
    create_thumbnail_for_grid,
    get_image_with_score_overlay
)


class GridViewSimulator:
    """
    グリッドビューの機能をGUIなしでシミュレートするクラス
    """
    
    def __init__(self):
        """初期化"""
        self.test_dir = tempfile.mkdtemp()
        self.image_files = []
        self.whiteness_dict = {}
        self.score_dict = {}
        self.thumbnail_size = 150
        self.sort_mode = "filename"
        
    def cleanup(self):
        """テストディレクトリを削除"""
        shutil.rmtree(self.test_dir)
    
    def create_test_images(self, count=10):
        """テスト用の画像を作成"""
        for i in range(count):
            # 白さが異なる画像を作成
            whiteness = (count - i) / count  # 1.0から徐々に減っていく
            
            # 白さに応じたグレースケール値
            gray_value = int(whiteness * 255)
            
            # 画像を作成
            img = Image.new('RGB', (200, 150), color=(gray_value, gray_value, gray_value))
            
            # ファイル名（逆順にして、ファイル名順と白さ順のソートが異なるようにする）
            filename = f"test_{count-i:02d}.jpg"
            filepath = os.path.join(self.test_dir, filename)
            
            # 画像を保存
            img.save(filepath)
            self.image_files.append(filepath)
            
            # 白さを計算して保存
            self.whiteness_dict[filepath] = whiteness
            
            # ランダムなスコア割り当て（テスト用）
            # 画像インデックスを3で割った余りを使用（0,1,2が繰り返される）
            self.score_dict[filepath] = str(i % 3)
    
    def get_sorted_files(self):
        """現在のソートモードに従ってファイルをソート"""
        if self.sort_mode == "filename":
            # ファイル名順
            return sorted(self.image_files, key=lambda x: os.path.basename(x))
        
        elif self.sort_mode == "whiteness":
            # 白さ順（白いものが先）
            return sorted(self.image_files, 
                         key=lambda x: self.whiteness_dict.get(x, 0.0),
                         reverse=True)
        
        elif self.sort_mode.startswith("score"):
            # 点数順
            def get_numeric_score(path):
                score = self.score_dict.get(path, "")
                if score == "skip":
                    return -1
                try:
                    return int(score) if score else 0
                except:
                    return 0
            
            reverse = self.sort_mode == "score_desc"
            return sorted(self.image_files, key=get_numeric_score, reverse=reverse)
        
        # デフォルト
        return self.image_files
    
    def create_grid_thumbnails(self):
        """ソートされたファイルからサムネイルを作成"""
        sorted_files = self.get_sorted_files()
        thumbnails = []
        
        for file_path in sorted_files:
            # 元画像を読み込み
            img = Image.open(file_path)
            
            # サムネイルを作成
            thumbnail = create_thumbnail_for_grid(img, self.thumbnail_size)
            
            # スコアがあればオーバーレイ
            score = self.score_dict.get(file_path, "")
            if score:
                thumbnail = get_image_with_score_overlay(thumbnail, score)
            
            thumbnails.append((file_path, thumbnail))
        
        return thumbnails
    
    def print_sort_results(self):
        """ソート結果を出力（デバッグ用）"""
        sorted_files = self.get_sorted_files()
        print(f"ソートモード: {self.sort_mode}")
        
        for i, file_path in enumerate(sorted_files):
            filename = os.path.basename(file_path)
            whiteness = self.whiteness_dict.get(file_path, 0.0)
            score = self.score_dict.get(file_path, "未採点")
            
            print(f"{i+1:2d}. {filename:15s} - 白さ: {whiteness:.3f}, 点数: {score}")


def main():
    """メイン関数"""
    print("グリッドビューシミュレーターを開始します...")
    
    # シミュレーターを初期化
    simulator = GridViewSimulator()
    
    try:
        # テスト用画像を作成
        print("テスト用画像を作成中...")
        simulator.create_test_images(10)
        
        # 各ソートモードでテスト
        for sort_mode in ["filename", "whiteness", "score_asc", "score_desc"]:
            simulator.sort_mode = sort_mode
            simulator.print_sort_results()
            print("")
            
        # サムネイルサイズを変更してテスト
        print("\nサムネイルサイズを変更してテスト中...")
        for size in [100, 150, 200]:
            simulator.thumbnail_size = size
            thumbnails = simulator.create_grid_thumbnails()
            print(f"サイズ {size}px: {len(thumbnails)}個のサムネイルを作成しました")
            
            # サムネイルが正しいサイズになっているか確認
            for _, thumb in thumbnails:
                assert thumb.width == size
                assert thumb.height == size
                
        print("\nすべてのテストが成功しました！")
        
    finally:
        # 一時ディレクトリを削除
        simulator.cleanup()


if __name__ == "__main__":
    main()