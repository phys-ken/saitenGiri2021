"""
画像のトリミング（切り抜き）処理を行うモジュール
"""
import os
import shutil
import csv
import glob
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from pathlib import Path

from ..models.answer_sheet import Region, AnswerSheet
from ..utils.file_utils import ensure_directories, get_sorted_image_files, SETTING_DIR, ANSWER_DATA_DIR


class ImageTrimmer:
    """画像トリミング処理クラス"""
    
    def __init__(self, input_dir: str = None, output_dir: str = None, answer_dir: str = None):
        """
        初期化処理
        
        Args:
            input_dir: 入力画像ディレクトリパス
            output_dir: 出力画像ディレクトリパス
            answer_dir: 模範解答画像ディレクトリパス
        """
        self.input_dir = input_dir if input_dir else str(SETTING_DIR / "input")
        self.output_dir = output_dir if output_dir else str(SETTING_DIR / "output")
        self.answer_dir = answer_dir if answer_dir else str(ANSWER_DATA_DIR)
        ensure_directories()  # 必要なディレクトリを作成
    
    def load_regions_from_csv(self, csv_path: str = None) -> List[Region]:
        """
        CSVファイルから切り取り領域のデータを読み込みます
        
        Args:
            csv_path: 領域データが保存されたCSVファイルパス。Noneの場合はデフォルトパスを使用
            
        Returns:
            List[Region]: 読み込まれた領域データのリスト
        """
        path = Path(csv_path) if csv_path else SETTING_DIR / 'trimData.csv'
        if not path.is_file():
            print(f"切り取り領域データファイルが見つかりません: {path}")
            return []
        
        regions = []
        try:
            with open(path, encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダー行をスキップ
                for row in reader:
                    if len(row) >= 5:
                        print(f"読み込み: {row}")  # デバッグ出力
                        tag, start_x, start_y, end_x, end_y = row
                        regions.append(Region(
                            tag=tag,
                            start_x=int(start_x),
                            start_y=int(start_y),
                            end_x=int(end_x),
                            end_y=int(end_y)
                        ))
        except Exception as e:
            print(f"CSVの読み込み中にエラーが発生しました ({path}): {e}")
            return []
        
        print(f"領域データを{len(regions)}件読み込みました")
        return regions
    
    def save_regions_to_csv(self, regions: List[Region], csv_path: str = None) -> bool:
        """
        領域データをCSVに保存します
        
        Args:
            regions: 保存する領域データのリスト
            csv_path: 保存先CSVファイルパス
            
        Returns:
            bool: 保存成功時True、失敗時False
        """
        path = Path(csv_path) if csv_path else SETTING_DIR / 'trimData.csv'
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y"])
                for region in regions:
                    writer.writerow([
                        region.tag, 
                        region.start_x, 
                        region.start_y, 
                        region.end_x, 
                        region.end_y
                    ])
            return True
        except Exception as e:
            print(f"CSVの保存中にエラーが発生しました: {e}")
            return False
    
    def trim_all_images(self) -> bool:
        """
        入力ディレクトリ内のすべての画像を切り取ります
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # 出力ディレクトリをクリアする
        self._clear_output_directory()
        
        # 領域データを明示的にtrimData.csvから読み込む
        trim_path = str(SETTING_DIR / 'trimData.csv')
        regions = self.load_regions_from_csv(trim_path)
        if not regions:
            print(f"切り取り領域データが存在しません: {trim_path}")
            return False
        
        # 出力ディレクトリがなければ作成
        try:
            # 出力ディレクトリはもう作られているはず
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 各領域用のディレクトリを作成
            for region in regions:
                region_dir = os.path.join(self.output_dir, region.tag)
                os.makedirs(region_dir, exist_ok=True)
                print(f"ディレクトリ作成: {region_dir}")
            
        except Exception as e:
            print(f"出力ディレクトリの作成中にエラーが発生しました: {e}")
            return False
        
        # 画像ファイル一覧を取得
        try:
            image_files = get_sorted_image_files(os.path.join(self.input_dir, "*"))
        except Exception as e:
            print(f"入力ディレクトリ {self.input_dir} の読み込みエラー: {e}")
            image_files = []
            
            # 直接glob関数を使用してみる
            try:
                image_files = sorted([f for f in glob.glob(os.path.join(self.input_dir, "*.*")) 
                                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
                print(f"glob検索結果: {len(image_files)}件のファイルを見つけました")
            except Exception as e2:
                print(f"glob検索でもエラー: {e2}")
                
        if not image_files:
            print("処理対象の画像ファイルがありません")
            return False
        
        print(f"合計{len(image_files)}個の画像ファイルを処理します")
        
        # 各画像を処理
        try:
            for image_path in image_files:
                self._process_image(image_path, regions)
            
            # nameフォルダの処理（最大高さのリサイズ）
            self._resize_name_folder()
            
            # 模範解答の処理（模範解答フォルダ内に画像がある場合）
            self.trim_sample_answers(regions)
            
            # 各問題フォルダに未割り当ての画像があるか確認
            processed_count = 0
            for region in regions:
                region_dir = os.path.join(self.output_dir, region.tag)
                if os.path.exists(region_dir):
                    files = [f for f in os.listdir(region_dir) if os.path.isfile(os.path.join(region_dir, f))]
                    processed_count += len(files)
                    print(f"{region.tag}: {len(files)}個のファイルを処理しました")
            
            print(f"合計{processed_count}個の切り抜き画像を生成しました")
            
            return True
        except Exception as e:
            print(f"画像処理中にエラーが発生しました: {e}")
            return False
    
    def _process_image(self, image_path: str, regions: List[Region]) -> None:
        """
        1つの画像を処理し、指定された領域で切り取ります
        
        Args:
            image_path: 画像ファイルパス
            regions: 切り取る領域のリスト
        """
        try:
            # 画像を読み込む
            img = Image.open(image_path)
            filename = os.path.basename(image_path)
            print(f"処理中: {filename}")
            
            # 各領域で画像を切り取って保存
            for region in regions:
                # 出力ディレクトリを作成
                output_dir = os.path.join(self.output_dir, region.tag)
                os.makedirs(output_dir, exist_ok=True)
                
                # 画像を切り取る
                img_trimmed = img.crop((
                    region.start_x, region.start_y, 
                    region.end_x, region.end_y
                ))
                
                # 切り取った画像を保存
                output_path = os.path.join(output_dir, filename)
                # ファイル形式をJPGに統一
                if img_trimmed.mode == 'RGBA':
                    # RGBAモード（透過画像）の場合、白地に変換
                    background = Image.new('RGB', img_trimmed.size, (255, 255, 255))
                    background.paste(img_trimmed, mask=img_trimmed.split()[3])
                    background.save(output_path, quality=95)
                else:
                    img_trimmed.save(output_path, quality=95)
                print(f"{region.tag}から{filename}を切り取りました")
        except Exception as e:
            print(f"{image_path}の処理中にエラーが発生しました: {e}")
            raise
    
    def _resize_name_folder(self, max_height: int = 50) -> None:
        """
        nameフォルダ内の画像を指定された最大高さにリサイズします
        
        Args:
            max_height: 最大高さピクセル
        """
        name_dir = os.path.join(self.output_dir, "name")
        if not os.path.exists(name_dir):
            print(f"nameフォルダが見つかりません: {name_dir}")
            return
        
        try:
            image_files = get_sorted_image_files(os.path.join(name_dir, "*"))
        except Exception as e:
            print(f"nameフォルダの検索中にエラー: {e}")
            # 直接glob関数を使用
            image_files = sorted([f for f in glob.glob(os.path.join(name_dir, "*.*")) 
                               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
            
        if not image_files:
            print(f"nameフォルダに画像がありません: {name_dir}")
            return
        
        print(f"nameフォルダの画像をリサイズします: {len(image_files)}個のファイル")
        
        # 最初の画像からサイズ比を計算
        try:
            img = Image.open(image_files[0])
            width, height = img.size
            
            # 高さが最大高さを超えている場合にリサイズ
            if height > max_height:
                resize_ratio = height / max_height
                
                # すべての画像をリサイズ
                for img_path in image_files:
                    img = Image.open(img_path)
                    new_size = (int(width / resize_ratio), int(height / resize_ratio))
                    resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                    resized_img.save(img_path, quality=95)
                    print(f"nameフォルダの画像をリサイズしました: {os.path.basename(img_path)}")
        except Exception as e:
            print(f"nameフォルダのリサイズ中にエラーが発生しました: {e}")
            
    def get_trim_region_count(self) -> int:
        """
        現在設定されている切り取り領域の数を返します
        
        Returns:
            int: 切り取り領域の数
        """
        regions = self.load_regions_from_csv()
        return len(regions)
    
    def _clear_output_directory(self) -> None:
        """
        出力ディレクトリのデータをクリアします
        """
        try:
            # 出力ディレクトリが存在しない場合は作成
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                print(f"出力ディレクトリを作成しました: {self.output_dir}")
                return
            
            # 出力ディレクトリ内のすべてのサブディレクトリをクリア
            for item in os.listdir(self.output_dir):
                item_path = os.path.join(self.output_dir, item)
                if os.path.isdir(item_path):
                    # サブディレクトリを削除して再作成
                    shutil.rmtree(item_path)
                    os.makedirs(item_path)
                    print(f"出力ディレクトリをクリアしました: {item_path}")
            
            print("全ての出力ディレクトリをクリアしました")
        except Exception as e:
            print(f"出力ディレクトリのクリア中にエラー: {e}")
    
    def trim_sample_answers(self, regions: Optional[List[Region]] = None) -> bool:
        """
        模範解答画像を指定された領域で切り取ります
        
        Args:
            regions: 切り取る領域のリスト（Noneの場合はCSVから読み込み）
            
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # 模範解答ディレクトリが存在するか確認
        if not os.path.exists(self.answer_dir):
            print(f"模範解答ディレクトリが見つかりません: {self.answer_dir}")
            return False
            
        # 模範解答画像の一覧を取得
        try:
            image_files = get_sorted_image_files(os.path.join(self.answer_dir, "*"))
        except Exception as e:
            print(f"模範解答ディレクトリ {self.answer_dir} の読み込みエラー: {e}")
            # 直接glob関数を使用
            try:
                image_files = sorted([f for f in glob.glob(os.path.join(self.answer_dir, "*.*")) 
                                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
            except Exception:
                print(f"模範解答画像が見つかりませんでした")
                return False
            
        if not image_files:
            print("処理対象の模範解答画像がありません")
            return False
            
        # 領域データがない場合はCSVから読み込む
        if regions is None:
            trim_path = str(SETTING_DIR / 'trimData.csv')
            regions = self.load_regions_from_csv(trim_path)
            if not regions:
                print(f"切り取り領域データが存在しません: {trim_path}")
                return False

        # 模範解答用の出力ディレクトリを作成
        answer_output_dir = os.path.join(self.answer_dir, "output")
        os.makedirs(answer_output_dir, exist_ok=True)
        
        # 既存の出力フォルダをクリア
        for item in os.listdir(answer_output_dir):
            item_path = os.path.join(answer_output_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                
        # 各領域用のディレクトリを作成
        for region in regions:
            region_dir = os.path.join(answer_output_dir, region.tag)
            os.makedirs(region_dir, exist_ok=True)
            
        # 各画像を処理
        try:
            for image_path in image_files:
                # 各領域で画像を切り取って保存
                img = Image.open(image_path)
                filename = os.path.basename(image_path)
                
                for region in regions:
                    # 出力ディレクトリを作成
                    output_dir = os.path.join(answer_output_dir, region.tag)
                    
                    # 画像を切り取る
                    img_trimmed = img.crop((
                        region.start_x, region.start_y, 
                        region.end_x, region.end_y
                    ))
                    
                    # 切り取った画像を保存
                    output_path = os.path.join(output_dir, filename)
                    # ファイル形式をJPGに統一
                    if img_trimmed.mode == 'RGBA':
                        # RGBAモード（透過画像）の場合、白地に変換
                        background = Image.new('RGB', img_trimmed.size, (255, 255, 255))
                        background.paste(img_trimmed, mask=img_trimmed.split()[3])
                        background.save(output_path, quality=95)
                    else:
                        img_trimmed.save(output_path, quality=95)
                    print(f"模範解答: {region.tag}から{filename}を切り取りました")
                    
            return True
        except Exception as e:
            print(f"模範解答画像の処理中にエラーが発生しました: {e}")
            return False
    
    def has_sample_answers(self) -> bool:
        """
        模範解答画像があるかどうか確認します
        
        Returns:
            bool: 模範解答画像がある場合はTrue、ない場合はFalse
        """
        if not os.path.exists(self.answer_dir):
            return False
        
        try:
            files = get_sorted_image_files(os.path.join(self.answer_dir, "*"))
            return len(files) > 0
        except:
            return False