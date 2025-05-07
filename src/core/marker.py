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
from typing import Dict, List, Optional, Union, Tuple, Any

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
        if (output_dir is None):
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
    
    def mark_all_answer_sheets(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        すべての解答用紙に採点結果を書き込みます
        
        Args:
            options: 出力オプション設定
                - question_scores: 設問ごとの得点表示
                - total_score: 合計得点表示
                - symbols: 〇×△マーク表示
                - transparency: マークの透過度 (0-100%)
                - score_position: 得点表示位置 ('right', 'center', 'left')
                - score_color: 得点表示色 ('red', 'same', 'black')
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # デフォルトのオプション（すべて有効）
        if options is None:
            options = {
                'question_scores': True,
                'total_score': True,
                'symbols': False,
                'transparency': 50,
                'score_position': 'right',
                'score_color': 'red'
            }
        
        # 1つもオプションが選択されていない場合はエラー
        if not any([
            options.get('question_scores', False),
            options.get('total_score', False),
            options.get('symbols', False)
        ]):
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
        
        # 〇×△マークを使用する場合はOpenCV版の処理を行う
        if options.get('symbols', False):
            return self._mark_sheets_with_opencv(image_files, regions, options)
        
        # マークなしの場合は従来のPIL版の処理を行うが、枠は付けない
        else:
            return self._mark_sheets_with_pil(image_files, regions, options)
    
    def _mark_sheets_with_pil(self, image_files, regions, options) -> bool:
        """
        PILを使用して、採点結果を解答用紙に書き込みます（マークなし）
        
        Args:
            image_files: 画像ファイルのリスト
            regions: 採点領域のリスト
            options: 出力オプション設定
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        try:
            # nameデータを見つける
            name_region = None
            for region in regions:
                if (region[0] == "name"):
                    name_region = region
                    break
            
            # 採点フォントサイズを決定
            if self.font_size is None and name_region:
                self.font_size = self._calculate_font_size(image_files[0], name_region)
            if self.font_size is None:
                self.font_size = 30  # デフォルト値
            
            # 各解答用紙を処理
            for image_path in image_files:
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
                        
                        # 得点表示位置の決定
                        score_position = options.get('score_position', 'right')
                        if score_position == 'right':
                            position = (int(right - self.font_size), int(top))
                        elif score_position == 'left':
                            position = (int(left), int(top))
                        else:  # center - 領域の中央
                            position = (int((left + right) / 2 - self.font_size/2), int((top + bottom) / 2 - self.font_size/2))
                        
                        # 得点表示色の決定
                        score_color_option = options.get('score_color', 'red')
                        if score_color_option == 'red':
                            fill_color = "red"
                        elif score_color_option == 'black':
                            fill_color = "black"
                        else:  # 'same'
                            # PILでは単純化のため赤を使用
                            fill_color = "red"
                        
                        # 得点を画像に書き込む（枠なし）
                        draw.text(position, score_text, font=font, fill=fill_color)
                
                # 合計点を表示する場合
                if options.get('total_score', True) and name_region:
                    tag, left, top, right, bottom = name_region
                    
                    # 得点表示位置の決定
                    score_position = options.get('score_position', 'right')
                    if score_position == 'right':
                        position = (int(right - self.font_size), int(top))
                    elif score_position == 'left':
                        position = (int(left), int(top))
                    else:  # center - 領域の中央
                        position = (int((left + right) / 2 - self.font_size/2), int((top + bottom) / 2 - self.font_size/2))
                    
                    # 得点表示色の決定
                    score_color_option = options.get('score_color', 'red')
                    if score_color_option == 'red':
                        fill_color = "red"
                    elif score_color_option == 'black':
                        fill_color = "black"
                    else:  # 'same'
                        # PILでは単純化のため赤を使用
                        fill_color = "red"
                    
                    # 合計点を画像に書き込む（枠なし）
                    draw.text(position, str(total_score), font=font, fill=fill_color)
                
                # 採点済み画像を保存
                output_path = os.path.join(self.output_dir, filename)
                img.save(output_path, quality=95)
                print(f"{filename}の採点マークを完了しました")
            
            return True
        except Exception as e:
            print(f"採点結果書き込み中にエラーが発生しました: {e}")
            return False
    
    def _mark_sheets_with_opencv(self, image_files, regions, options) -> bool:
        """
        OpenCVを使用して、採点結果を解答用紙に書き込みます（〇×△マークあり）
        
        Args:
            image_files: 画像ファイルのリスト
            regions: 採点領域のリスト
            options: 出力オプション設定
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # 領域データを辞書形式に変換
        regions_data = []
        name_region = None
        
        for region in regions:
            tag, left, top, right, bottom = region
            region_dict = {
                "tag": tag,
                "x_s": left, "y_s": top, 
                "x_g": right, "y_g": bottom
            }
            regions_data.append(region_dict)
            
            if tag == "name":
                name_region = region_dict
        
        if not regions_data:
            print("有効な領域データがありません")
            return False
        
        # 問題ID一覧を取得（nameは除外）
        question_ids = [r["tag"] for r in regions_data if r["tag"] != "name"]
        if not question_ids:
            print("問題データがありません")
            return False
        
        # 問題ごとの最高得点を取得
        max_scores = self._get_max_scores()
        print(f"各問題の最高得点: {max_scores}")
        
        # 文字の濃さ設定を取得（0-100）
        concentration = options.get('transparency', 50)  # 「文字の濃さ」として解釈
        # 範囲チェック（0〜100の範囲にする）
        concentration = max(0, min(100, concentration))
        
        # OpenCVで使用する濃さの値を計算
        # 0%（薄い）の場合はalpha=0.2（ほぼ透明）、100%（濃い）の場合はalpha=1.0（完全に不透明）
        alpha = 0.2 + (concentration / 100.0) * 0.8
        
        # マーク色の設定（より鮮やかな色に変更）
        RED_COLOR = (0, 0, 255)      # ×（RGB: #FF0000）
        BLUE_COLOR = (255, 0, 0)     # 〇（RGB: #0000FF）
        GREEN_COLOR = (0, 128, 0)    # △（RGB: #008000）
        
        # 各解答用紙を処理
        processed_count = 0
        for image_path in image_files:
            filename = os.path.basename(image_path)
            
            # 画像を読み込む
            img = _cv_imread(image_path)
            if img is None:
                print(f"{filename}の読み込みに失敗しました")
                continue
                
            # マーカー用のレイヤーを作成
            mark_overlay = img.copy()
            
            # 文字表示用のレイヤーを作成
            text_overlay = img.copy()
            
            # 合計点を計算
            total_score = 0
            
            # 各問題領域を処理
            for region in regions_data:
                tag = region["tag"]
                
                # nameは一旦スキップ（後で合計点を表示）
                if tag == "name":
                    continue
                
                # この問題について採点データを持っていない場合はスキップ
                if filename not in self.grades or tag not in self.grades[filename]:
                    continue
                
                # skipの場合はマークを付けない
                if self.grades[filename][tag] == "skip":
                    continue
                
                # 得点を取得
                score = self.grades[filename][tag]
                
                # 数値の場合は合計点に加算
                if isinstance(score, int):
                    total_score += score
                
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
                
                # フォントサイズをマークサイズに合わせる
                font_size = size / 18  # マークサイズに合わせる
                
                # マーク色とマークの種類を決定
                if isinstance(score, int) and options.get('symbols', False):
                    # 問題の最高点を取得（該当問題IDがなければ0）
                    max_score = max_scores.get(tag, 0)
                    
                    # 得点によってマークを判定
                    if score == 0:
                        # 0点の場合は×（赤）
                        mark_color = RED_COLOR
                        cv2.drawMarker(
                            mark_overlay, (x, y), mark_color, 
                            thickness=8, 
                            markerType=cv2.MARKER_TILTED_CROSS, 
                            markerSize=int(size)
                        )
                        mark_type = '×'
                    elif score == max_score and max_score > 0:
                        # 最高点の場合は〇（青）
                        mark_color = BLUE_COLOR
                        cv2.circle(
                            mark_overlay, (x, y), int(size), 
                            mark_color, thickness=3, 
                            lineType=cv2.LINE_AA
                        )
                        mark_type = '〇'
                    else:
                        # 部分点の場合は△（緑）
                        mark_color = GREEN_COLOR
                        cv2.drawMarker(
                            mark_overlay, (x, y), mark_color, 
                            thickness=3, 
                            markerType=cv2.MARKER_TRIANGLE_UP, 
                            markerSize=int(size)
                        )
                        mark_type = '△'
                else:
                    # マークなしの場合
                    mark_color = RED_COLOR  # デフォルト赤
                    mark_type = None
                
                # 得点を表示する場合（×(0点)の場合は表示しない）
                if options.get('question_scores', True) and isinstance(score, int) and score > 0:
                    # 得点表示色の決定
                    score_color_option = options.get('score_color', 'red')
                    if score_color_option == 'red':
                        score_color = RED_COLOR
                    elif score_color_option == 'same' and options.get('symbols', False):
                        score_color = mark_color  # マークと同じ色
                    else:  # 'black'または'same'でマークなしの場合
                        score_color = (0, 0, 0)  # 黒
                    
                    score_text = str(score)
                    text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, font_size, 2)[0]
                    
                    # 得点表示位置の決定
                    score_position = options.get('score_position', 'right')
                    if score_position == 'right':
                        text_x = x_g - text_size[0] - 5
                        text_y = y_s + text_size[1] + 5
                    elif score_position == 'left':
                        text_x = x_s + 5
                        text_y = y_s + text_size[1] + 5
                    else:  # 'center' - マークの横または中央
                        if mark_type and options.get('symbols', False):
                            # マークありの場合はマークの横に配置
                            text_x = x + int(size) + 5
                            text_y = y + int(text_size[1]/3)
                        else:
                            # マークなしの場合は中央に配置
                            text_x = x - int(text_size[0]/2)
                            text_y = y + int(text_size[1]/3)
                    
                    # 得点テキストを描画（文字表示用レイヤーに）
                    cv2.putText(
                        text_overlay, score_text, 
                        (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        font_size, score_color, 2, 
                        cv2.LINE_AA
                    )
            
            # 合計点を表示する場合
            if options.get('total_score', True) and name_region and total_score > 0:
                x_s, y_s = name_region["x_s"], name_region["y_s"]
                x_g, y_g = name_region["x_g"], name_region["y_g"]
                
                # 氏名欄の高さを計算
                name_height = y_g - y_s
                
                # 合計点のフォントサイズは氏名欄の高さに基づいて設定（調整係数を適用）
                font_size = name_height / 25  # 氏名欄の高さに合わせる
                
                # 表示位置は常に氏名欄の右端
                total_text = str(total_score)
                text_size = cv2.getTextSize(total_text, cv2.FONT_HERSHEY_SIMPLEX, font_size, 2)[0]
                
                # 右端の位置を計算
                text_x = x_g - text_size[0] - 5
                text_y = y_s + text_size[1] + 5
                
                # 得点表示色の決定（合計点はデフォルトで赤または黒）
                score_color_option = options.get('score_color', 'red')
                if score_color_option == 'red':
                    score_color = RED_COLOR
                elif score_color_option == 'black':
                    score_color = (0, 0, 0)  # 黒
                else:  # 'same'の場合は青を使用（合計点は特別扱い）
                    score_color = BLUE_COLOR
                
                # 合計点テキストを描画（文字表示用レイヤーに）
                cv2.putText(
                    text_overlay, total_text, 
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    font_size, score_color, 2, 
                    cv2.LINE_AA
                )
            
            result_img = None
            
            # 背景画像のコピーを作成（最終結果用）
            result_img = img.copy()
            
            # マークの描画（マーク表示がある場合のみ）
            if options.get('symbols', False):
                if concentration == 100:
                    # 濃さ100%（完全に濃い）の場合は透過せず直接マークを上書き
                    # マークをブレンドせずに配置
                    mask = cv2.cvtColor(mark_overlay, cv2.COLOR_BGR2GRAY)
                    _, binary_mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY_INV)
                    # マーク部分だけを抽出
                    mark_diff = cv2.bitwise_xor(img, mark_overlay)
                    # マスクを使って元画像にマークを追加
                    idx = (binary_mask != 0)
                    result_img[idx] = mark_overlay[idx]
                else:
                    # 通常の透過処理（濃さに応じてブレンド）
                    # alphaは文字の濃さに応じて調整（0.2〜1.0の範囲）
                    # マークを描画
                    mark_diff = cv2.absdiff(img, mark_overlay)
                    mark_mask = cv2.cvtColor(mark_diff, cv2.COLOR_BGR2GRAY)
                    _, mark_mask = cv2.threshold(mark_mask, 5, 255, cv2.THRESH_BINARY)
                    mark_mask_inv = cv2.bitwise_not(mark_mask)
                    
                    # 背景部分
                    bg = cv2.bitwise_and(result_img, result_img, mask=mark_mask_inv)
                    # マーク部分（濃さに応じて元画像とブレンド）
                    fg = cv2.addWeighted(mark_overlay, alpha, img, 1.0 - alpha, 0)
                    fg = cv2.bitwise_and(fg, fg, mask=mark_mask)
                    
                    # 合成
                    result_img = cv2.add(bg, fg)
            
            # 文字の描画（常に行う）
            if concentration == 100:
                # 濃さ100%の場合は透過せず直接上書き
                # 文字部分のマスクを作成
                text_diff = cv2.absdiff(img, text_overlay)
                text_mask = cv2.cvtColor(text_diff, cv2.COLOR_BGR2GRAY)
                _, text_mask = cv2.threshold(text_mask, 5, 255, cv2.THRESH_BINARY)
                
                # マスクを使って文字を上書き
                result_img[text_mask > 0] = text_overlay[text_mask > 0]
            else:
                # 通常の透過処理（濃さに応じてブレンド）
                # 文字部分だけを抽出
                text_diff = cv2.absdiff(img, text_overlay)
                text_mask = cv2.cvtColor(text_diff, cv2.COLOR_BGR2GRAY)
                _, text_mask = cv2.threshold(text_mask, 5, 255, cv2.THRESH_BINARY)
                text_mask_inv = cv2.bitwise_not(text_mask)
                
                # 背景部分
                bg = cv2.bitwise_and(result_img, result_img, mask=text_mask_inv)
                # 文字部分（濃さに応じてブレンド）
                fg = cv2.addWeighted(text_overlay, alpha, img, 1.0 - alpha, 0)
                fg = cv2.bitwise_and(fg, fg, mask=text_mask)
                
                # 合成
                result_img = cv2.add(bg, fg)
            
            # マーク付き画像を保存
            output_path = os.path.join(self.output_dir, filename)
            if _cv_imwrite(output_path, result_img):
                print(f"{filename}の処理を完了しました")
                processed_count += 1
            else:
                print(f"{filename}の保存に失敗しました")
        
        print(f"合計{processed_count}個の画像を処理しました")
        return processed_count > 0
    
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

    def mark_all_answer_sheets_with_symbols(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        すべての解答用紙に〇×△マークを書き込みます
        
        Args:
            options: 出力オプション設定
                - transparency: マークの透過度 (0-100%)
                - score_position: 得点表示位置 ('right', 'center', 'left')
                - score_color: 得点表示色 ('red', 'same', 'black')
        
        Returns:
            bool: 処理成功時True、失敗時False
        """
        # オプション初期値の設定
        if options is None:
            options = {
                'transparency': 50,  # デフォルト50%
                'score_position': 'right',  # デフォルト右端
                'score_color': 'red'  # デフォルト赤
            }
            
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
        
        # 問題ごとの最高得点を取得
        max_scores = self._get_max_scores()
        print(f"各問題の最高得点: {max_scores}")
        
        # 透過度設定の取得
        transparency = options.get('transparency', 50)
        # 透過度の範囲チェック（0〜100の範囲にする）
        transparency = max(0, min(100, transparency))
        # OpenCVで使用する透明度に変換（0〜1）
        alpha = 1 - (transparency / 100)
        
        # 各採点済み画像にマークを付ける
        processed_count = 0
        for img_path in image_files:
            filename = os.path.basename(img_path)
            
            # 画像を読み込む
            img = _cv_imread(img_path)
            if img is None:
                print(f"{filename}の読み込みに失敗しました")
                continue
            
            # 透過処理用にマーク用の透明レイヤーを作成
            overlay = img.copy()
                
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
                x_g, y_g = region["x_g"], y_g
                
                # 中心座標を計算
                x = round(x_s + (x_g - x_s) / 2)
                y = round(y_s + (y_g - y_s) / 2)
                
                # マーカーサイズの決定
                if x_g - x_s < y_g - y_s:
                    size = (x_g - x_s) / 3
                else:
                    size = (y_g - y_s) / 3
                
                # 最小解答欄の高さを得点表示のフォントサイズとして使用
                font_size = int(size * 0.8)
                
                # 採点結果を取得
                score = self.grades[filename][tag]
                
                # マーク色とマークの種類を決定
                if isinstance(score, int):
                    # 問題の最高点を取得（該当問題IDがなければ0）
                    max_score = max_scores.get(tag, 0)
                    
                    # 得点によってマークを判定
                    if score == 0:
                        # 0点の場合は×（赤）
                        mark_color = (0, 0, 255)  # 赤（BGR形式）
                        cv2.drawMarker(
                            overlay, (x, y), mark_color, 
                            thickness=8, 
                            markerType=cv2.MARKER_TILTED_CROSS, 
                            markerSize=int(size)
                        )
                        mark_type = '×'
                    elif score == max_score:
                        # 最高点の場合は〇（青）
                        mark_color = (255, 0, 0)  # 青（BGR形式）
                        cv2.circle(
                            overlay, (x, y), int(size), 
                            mark_color, thickness=3, 
                            lineType=cv2.LINE_AA
                        )
                        mark_type = '〇'
                    else:
                        # 部分点の場合は△（緑）
                        mark_color = (0, 255, 0)  # 緑（BGR形式）
                        cv2.drawMarker(
                            overlay, (x, y), mark_color, 
                            thickness=3, 
                            markerType=cv2.MARKER_TRIANGLE_UP, 
                            markerSize=int(size)
                        )
                        mark_type = '△'
                    
                    # 得点表示位置の決定
                    score_position = options.get('score_position', 'right')
                    
                    # 得点を表示する場合
                    if options.get('question_scores', True):
                        # 得点表示色の決定
                        score_color_option = options.get('score_color', 'red')
                        if score_color_option == 'red':
                            score_color = (0, 0, 255)  # 赤
                        elif score_color_option == 'same':
                            score_color = mark_color  # マークと同じ色
                        else:  # 'black'
                            score_color = (0, 0, 0)  # 黒
                        
                        score_text = str(score)
                        text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, font_size/30, 2)[0]
                        
                        # 位置に応じて座標を設定
                        if score_position == 'right':
                            text_x = x_g - text_size[0] - 5
                            text_y = y_s + text_size[1] + 5
                        elif score_position == 'left':
                            text_x = x_s + 5
                            text_y = y_s + text_size[1] + 5
                        else:  # 'center' - マークの横
                            if mark_type in ['〇', '×']:
                                # マークがある場合はマークの横に配置
                                text_x = x + int(size) + 5
                                text_y = y + int(text_size[1]/2)
                            else:
                                # マークがない場合は中央に配置
                                text_x = x - int(text_size[0]/2)
                                text_y = y + int(text_size[1]/2)
                        
                        # 得点テキストを描画（透過処理は行わない）
                        cv2.putText(
                            img, score_text, 
                            (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            font_size/30, score_color, 2
                        )
            
            # オーバーレイの透過合成
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
            
            # マーク付き画像を保存
            output_path = img_path  # 同じ場所に上書き保存
            if _cv_imwrite(output_path, img):
                print(f"{filename}に〇×△マークを付けました")
                processed_count += 1
            else:
                print(f"{filename}の保存に失敗しました")
        
        print(f"合計{processed_count}個の画像に〇×△マークを付けました")
        return processed_count > 0
        
    def _get_max_scores(self) -> Dict[str, int]:
        """
        問題ごとの最高得点を取得します
        
        Returns:
            Dict[str, int]: {問題ID: 最高得点}の辞書
        """
        max_scores = {}
        
        # setting/outputディレクトリパスの取得
        output_dir = os.path.join(os.path.dirname(os.path.dirname(self.output_dir)), "output")
        if not os.path.exists(output_dir):
            output_dir = str(SETTING_DIR / "output")
            
        if not os.path.exists(output_dir):
            return max_scores
            
        # 問題フォルダを取得（nameフォルダは除外）
        question_dirs = [d for d in os.listdir(output_dir)
                         if os.path.isdir(os.path.join(output_dir, d)) and d != "name"]
                         
        for question_id in question_dirs:
            question_dir = os.path.join(output_dir, question_id)
            
            # 各スコアフォルダを処理
            score_dirs = [d for d in os.listdir(question_dir)
                          if os.path.isdir(os.path.join(question_dir, d))]
            
            # スコアフォルダから数値のみを抽出して最大値を取得
            numeric_scores = []
            for score_dir in score_dirs:
                if score_dir.isdigit():
                    numeric_scores.append(int(score_dir))
            
            if numeric_scores:
                max_scores[question_id] = max(numeric_scores)
                
        return max_scores