"""
採点結果を画像に書き込むモジュール
"""
import os
import glob
import csv
import subprocess
import sys
import shutil
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Union, Tuple

from ..models.grade_data import GradeData, GradingSession
from ..utils.file_utils import resource_path, get_sorted_image_files, SETTING_DIR

# OpenCV関連の画像読み書きヘルパー関数
def _cv_imread(path):
    """
    日本語パスに対応したOpenCV画像読み込み関数
    """
    try:
        # NumPy配列として読み込んでからOpenCVの形式に変換
        img = np.fromfile(path, np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"画像読み込み中にエラー: {e}")
        return None

def _cv_imwrite(filename, img, params=None):
    """
    日本語パスに対応したOpenCV画像書き込み関数
    """
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)
        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(f"画像保存中にエラー: {e}")
        return False


class AnswerMarker:
    """採点結果を解答用紙に書き込むクラス"""
    
    def __init__(self, 
                 input_dir: str = None, 
                 output_dir: str = None,
                 grading_data_path: str = None,
                 font_size: Optional[int] = None):
        """
        初期化処理
        
        Args:
            input_dir: 元の解答用紙が保存されているディレクトリパス
            output_dir: 採点結果を書き込んだ解答用紙を保存するディレクトリパス
            grading_data_path: 採点領域データを含むCSVファイルパス
            font_size: フォントサイズ（Noneの場合は自動計算）
        """
        # デフォルト値の設定
        self.input_dir = input_dir or str(SETTING_DIR / "input")
        self.output_dir = output_dir or str(SETTING_DIR / "export")
        self.grading_data_path = grading_data_path or str(SETTING_DIR / "trimData.csv")
        self.font_size = font_size
        self.grades = {}  # 採点データ格納用辞書
    
    def load_grading_data(self) -> List[Tuple[str, int, int, int, int]]:
        """
        採点領域のデータをCSVから読み込みます
        
        Returns:
            List[Tuple[str, int, int, int, int]]: 採点領域データのリスト [タグ, 左, 上, 右, 下]
        """
        if not os.path.isfile(self.grading_data_path):
            return []
        
        regions = []
        try:
            with open(self.grading_data_path) as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダー行をスキップ
                for row in reader:
                    if len(row) >= 5:
                        tag, left, top, right, bottom = row
                        regions.append((tag, int(left), int(top), int(right), int(bottom)))
        except Exception as e:
            print(f"CSVの読み込み中にエラーが発生しました: {e}")
            return []
        
        return regions
    
    def load_grades_from_filesystem(self, output_dir: str = None) -> Dict[str, Dict[str, Union[int, str]]]:
        """
        採点データをファイルシステムから読み込みます
        
        Args:
            output_dir: 切り取り画像が保存されているディレクトリパス
            
        Returns:
            Dict[str, Dict[str, Union[int, str]]]: {ファイル名: {問題ID: スコア}} 形式の採点データ辞書
        """
        # デフォルト値の設定
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(self.output_dir)), "output")
            if not os.path.exists(output_dir):
                # デフォルト設定の場合は、クラス初期化時の設定を参照
                base_dir = os.path.dirname(os.path.dirname(self.output_dir))
                output_dir = os.path.join(base_dir, "output")
                
                # それでも存在しない場合は、SETTING_DIRを使用
                if not os.path.exists(output_dir):
                    output_dir = str(SETTING_DIR / "output")
        
        result = {}
        
        if not os.path.exists(output_dir):
            print(f"採点データディレクトリが存在しません: {output_dir}")
            return result
        
        # 問題ディレクトリを取得（nameディレクトリは除外）
        question_dirs = [d for d in os.listdir(output_dir) 
                         if os.path.isdir(os.path.join(output_dir, d)) and d != "name"]
        
        for question_id in question_dirs:
            question_dir = os.path.join(output_dir, question_id)
            
            # 各スコアディレクトリを処理
            for score_dir in [d for d in os.listdir(question_dir) 
                              if os.path.isdir(os.path.join(question_dir, d))]:
                score_path = os.path.join(question_dir, score_dir)
                
                # スコアを解析
                try:
                    score = int(score_dir) if score_dir.isdigit() else score_dir
                except ValueError:
                    score = score_dir
                
                # 各ファイルを処理
                for file_path in get_sorted_image_files(os.path.join(score_path, "*")):
                    filename = os.path.basename(file_path)
                    
                    # 結果辞書に追加
                    if filename not in result:
                        result[filename] = {}
                    result[filename][question_id] = score
        
        return result
    
    def mark_all_answer_sheets(self, options: Optional[Dict[str, bool]] = None) -> bool:
        """
        すべての解答用紙に採点結果を書き込みます
        
        Args:
            options: 出力オプション設定
                - question_scores: 設問ごとの得点表示
                - total_score: 合計得点表示
                - symbols: 〇×△マーク表示
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # デフォルトのオプション（すべて有効）
        if options is None:
            options = {
                'question_scores': True,
                'total_score': True,
                'symbols': False
            }
        
        # 1つもオプションが選択されていない場合はエラー
        if not any(options.values()):
            print("有効な出力オプションが選択されていません")
            return False
        
        # 領域データを読み込む
        regions = self.load_grading_data()
        if not regions:
            print("採点領域データが存在しません")
            return False
        
        # 採点データを読み込む
        self.grades = self.load_grades_from_filesystem()
        if not self.grades:
            print("採点データが存在しません")
            return False
        
        # 出力ディレクトリを作成
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 解答用紙を取得
        image_files = get_sorted_image_files(os.path.join(self.input_dir, "*"))
        if not image_files:
            print("解答用紙が存在しません")
            return False
        
        # nameデータを見つける（最初がnameと仮定）
        name_region = None
        for region in regions:
            if (region[0] == "name"):
                name_region = region
                break
        
        # 採点フォントサイズを決定
        if self.font_size is None:
            # 最初の画像とname領域から適切なフォントサイズを計算
            if name_region:
                self.font_size = self._calculate_font_size(image_files[0], name_region)
        
        # 各解答用紙を処理
        try:
            for image_path in image_files:
                self._mark_answer_sheet(image_path, regions, name_region, options)
            
            # 〇×△マークを付ける場合
            if options.get('symbols', False):
                # 採点結果付きの画像にマークを付ける
                return self.mark_all_answer_sheets_with_symbols()
            
            return True
        except Exception as e:
            print(f"採点結果書き込み中にエラーが発生しました: {e}")
            return False
    
    def _calculate_font_size(self, image_path: str, name_region: Tuple) -> int:
        """
        画像と領域から適切なフォントサイズを計算します
        
        Args:
            image_path: 画像パス
            name_region: 名前領域データ
            
        Returns:
            int: 計算されたフォントサイズ
        """
        try:
            # 名前領域の幅と高さを計算
            _, left, top, right, bottom = name_region
            width = right - left
            height = bottom - top
            
            # 領域サイズに基づいてフォントサイズを決定
            if height >= width:
                return int(width / 2)
            else:
                return int(height / 2)
        except Exception:
            # エラー時はデフォルト値を返す
            return 30
    
    def _mark_answer_sheet(self, image_path: str, regions: List[Tuple], 
                          name_region: Optional[Tuple], 
                          options: Dict[str, bool]) -> None:
        """
        1つの解答用紙に採点結果を書き込みます
        
        Args:
            image_path: 解答用紙の画像パス
            regions: 採点領域のリスト
            name_region: 名前領域データ（合計点表示用）
            options: 出力オプション設定
        """
        filename = os.path.basename(image_path)
        
        # 画像を読み込む
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # 採点用フォントを読み込む
        try:
            font = ImageFont.truetype("arial.ttf", self.font_size)
        except:
            try:
                font = ImageFont.truetype("AppleGothic.ttf", self.font_size)
            except:
                font = ImageFont.load_default()
        
        # 合計点を計算
        total_score = 0
        
        # 設問ごとの得点を表示する場合
        if options.get('question_scores', True):
            # 各領域に得点を書き込む
            for region in regions:
                tag, left, top, right, bottom = region
                
                # nameは処理しない
                if tag == "name":
                    continue
                
                # 得点を取得
                score_text = "?"  # デフォルト値
                if filename in self.grades and tag in self.grades[filename]:
                    score = self.grades[filename][tag]
                    score_text = str(score)
                    
                    # skipの場合は表示しない
                    if score_text == "skip":
                        continue
                    
                    # 数値の場合は合計点に加算
                    if isinstance(score, int):
                        total_score += score
                
                # 得点を画像に書き込む
                position = (int(right - self.font_size/2), int(top))
                draw.text(position, score_text, font=font, fill="red")
                draw.rectangle(
                    (position[0], position[1], position[0] + self.font_size, position[1] + self.font_size),
                    outline="red"
                )
        
        # 合計点を表示する場合
        if options.get('total_score', True) and name_region:
            _, left, top, right, bottom = name_region
            position = (int(right - self.font_size/2), int(top))
            draw.text(position, str(total_score), font=font, fill="red")
            draw.rectangle(
                (position[0], position[1], position[0] + self.font_size*1.5, position[1] + self.font_size),
                outline="red"
            )
        
        # 採点済み画像を保存
        output_path = os.path.join(self.output_dir, filename)
        img.save(output_path, quality=95)
        print(f"{filename}の採点マークを完了しました")
        
    def launch_external_marker(self, image_path: str) -> bool:
        """
        外部の○×マーカーを起動します（marubatu.exeの機能）
        
        Args:
            image_path: 編集する画像パス
            
        Returns:
            bool: 処理成功時True、失敗時False
        """
        try:
            # marubatu.exeのパスを取得
            marubatu_path = resource_path("marubatu.exe")
            
            # 外部プロセスとして起動
            subprocess.Popen([marubatu_path, image_path])
            return True
        except Exception as e:
            print(f"マーカー起動中にエラーが発生しました: {e}")
            return False

    def mark_all_answer_sheets_with_symbols(self) -> bool:
        """
        すべての解答用紙に〇×△マークを書き込みます
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # 採点済み画像ディレクトリの存在確認
        if not os.path.exists(self.output_dir):
            print(f"採点済み画像フォルダが存在しません: {self.output_dir}")
            return False
            
        # 領域データを読み込む
        regions_data = []
        try:
            df = []
            with open(self.grading_data_path, "r") as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーをスキップ
                for row in reader:
                    if len(row) >= 5:
                        tag = row[0]
                        x_s, y_s, x_g, y_g = map(int, row[1:5])
                        regions_data.append({
                            "tag": tag,
                            "x_s": x_s, "y_s": y_s, 
                            "x_g": x_g, "y_g": y_g
                        })
        except Exception as e:
            print(f"領域データの読み込み中にエラー: {e}")
            return False
            
        if not regions_data:
            print("有効な領域データがありません")
            return False
            
        # 問題ID一覧を取得（nameは除外）
        question_ids = [r["tag"] for r in regions_data if r["tag"] != "name"]
        if not question_ids:
            print("問題データがありません")
            return False

        print(f"処理対象の問題: {question_ids}")
        
        # 採点済み画像一覧の取得
        try:
            image_files = get_sorted_image_files(os.path.join(self.output_dir, "*"))
        except Exception as e:
            print(f"画像ファイルの取得中にエラー: {e}")
            return False
            
        if not image_files:
            print("採点済み画像がありません")
            return False
            
        print(f"処理対象の画像: {len(image_files)}件")
        
        # 採点データを再読み込み（既にself.gradesに格納済みの場合は不要）
        if not self.grades:
            self.grades = self.load_grades_from_filesystem()
            
        if not self.grades:
            print("採点データが見つかりません")
            return False
        
        # 各採点済み画像にマークを付ける
        processed_count = 0
        for img_path in image_files:
            filename = os.path.basename(img_path)
            
            # 画像を読み込む
            img = _cv_imread(img_path)
            if img is None:
                print(f"{filename}の読み込みに失敗しました")
                continue
                
            # 各問題領域にマークを付ける
            for region in regions_data:
                tag = region["tag"]
                if tag == "name":
                    continue
                    
                # この問題について採点データを持っていない場合はスキップ
                if filename not in self.grades or tag not in self.grades[filename]:
                    continue
                
                # skipの場合はマークを付けない
                if self.grades[filename][tag] == "skip":
                    print(f"{filename}の{tag}はskipなのでマークを付けません")
                    continue
                    
                # 領域の座標を取得
                x_s, y_s = region["x_s"], region["y_s"]
                x_g, y_g = region["x_g"], region["y_g"]
                
                # 中心座標を計算
                x = round(x_s + (x_g - x_s) / 2)
                y = round(y_s + (y_g - y_s) / 2)
                
                # マーカーサイズの決定
                if x_g - x_s < y_g - y_s:
                    size = (x_g - x_s) / 3
                else:
                    size = (y_g - y_s) / 3
                
                # 採点結果を取得して〇×△マークを判定
                score = self.grades[filename][tag]
                if isinstance(score, int):
                    if score == 0:
                        # 0点の場合は×
                        img = cv2.drawMarker(
                            img, (x, y), (0, 0, 255), 
                            thickness=8, 
                            markerType=cv2.MARKER_TILTED_CROSS, 
                            markerSize=int(size)
                        )
                    elif score == 3:  # 満点と仮定
                        # 満点の場合は〇
                        img = cv2.circle(
                            img, (x, y), int(size), 
                            (0, 0, 255), thickness=3, 
                            lineType=cv2.LINE_AA
                        )
                    else:
                        # 部分点の場合は△
                        img = cv2.drawMarker(
                            img, (x, y), (0, 0, 255), 
                            thickness=3, 
                            markerType=cv2.MARKER_TRIANGLE_UP, 
                            markerSize=int(size)
                        )
            
            # マーク付き画像を保存
            output_path = img_path  # 同じ場所に上書き保存
            if _cv_imwrite(output_path, img):
                print(f"{filename}に〇×△マークを付けました")
                processed_count += 1
            else:
                print(f"{filename}の保存に失敗しました")
        
        print(f"合計{processed_count}個の画像に〇×△マークを付けました")
        return processed_count > 0