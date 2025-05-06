"""
解答用紙の切り取り領域を定義するためのウィンドウクラス
"""
import os
import csv
import shutil
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import List, Tuple, Optional, Dict, Any

from ...models.answer_sheet import Region
from ...utils.image_utils import calculate_resize_ratio, create_rectangle_with_alpha
from ...utils.file_utils import SETTING_DIR, ANSWER_DATA_DIR
from ...core.trimmer import ImageTrimmer


class TrimDefinerWindow:
    """切り取り領域定義ウィンドウ"""
    
    def __init__(self, parent: tk.Tk, image_path: str):
        """
        初期化処理
        
        Args:
            parent: 親ウィンドウ
            image_path: 切り取り定義に使用する画像パス
        """
        self.parent = parent
        self.image_path = image_path
        
        # ドラッグ操作用の変数
        self.start_x = 0
        self.start_y = 0
        self.q_count = 0  # 問題カウンタ
        self.resize_ratio = 1.0  # 画像リサイズ比率
        
        # 画像表示用の変数
        self.original_image = None
        self.resized_image = None
        self.tk_image = None
        self.images = []  # 透過矩形用の参照保持リスト
        
        # 模範解答画像を使用するか確認
        self.use_sample_answer = self._check_sample_answer()
        
        # ウィンドウ作成
        self._create_window()
        # 既存領域を表示
        self._load_existing_regions()
        # 定義画面を表示し続ける
        self.window.wait_window()
        
    def _check_sample_answer(self) -> bool:
        """
        模範解答画像があるか確認し、使用するかを確認します
        
        Returns:
            bool: 模範解答を使用する場合はTrue
        """
        # 模範解答ディレクトリのチェック
        if not ANSWER_DATA_DIR.exists():
            return False
            
        # 模範解答画像があるかチェック
        sample_files = [f for f in ANSWER_DATA_DIR.iterdir() 
                       if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif')]
        if not sample_files:
            return False
            
        # ユーザーに模範解答を使用するか確認
        trimmer = ImageTrimmer()
        if trimmer.has_sample_answers():
            ret = messagebox.askyesno(
                '模範解答画像', 
                '模範解答画像が見つかりました。\n'
                '斬り取り領域のプレビューに模範解答を使用しますか？\n\n'
                '「いいえ」を選ぶと通常の解答用紙を使用します。'
            )
            return ret
        return False
    
    def _create_window(self) -> None:
        """ウィンドウを作成します"""
        # ウィンドウ設定
        self.window = tk.Toplevel(self.parent)
        self.window.title("解答用紙を斬る")
        
        # 画面サイズ設定
        window_h = 700
        window_w = int(window_h * 1.7)
        fig_area_w = int(window_h * 1)
        self.window.geometry(f"{window_w}x{window_h}")
        
        # フレーム作成
        self.cutting_frame = tk.Frame(self.window)
        self.cutting_frame.pack()
        
        self.canvas_frame = tk.Frame(self.cutting_frame)
        self.canvas_frame.grid(column=0, row=0)
        
        self.button_frame = tk.Frame(self.cutting_frame)
        self.button_frame.grid(column=1, row=0)
        
        # CSVファイルを初期化
        self._initialize_csv()
        
        # 画像の読み込みとリサイズ
        if self.use_sample_answer:
            # 模範解答画像を使用
            sample_files = sorted([f for f in ANSWER_DATA_DIR.iterdir() 
                               if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif')])
            self.original_image = Image.open(str(sample_files[0]))
            
            # 模範解答使用中のラベル
            self.sample_label = tk.Label(
                self.button_frame,
                text="模範解答画像使用中",
                bg="#ffe6cc",
                fg="#333333",
                font=("Meiryo UI", 9, "bold"),
                padx=10,
                pady=5
            )
            self.sample_label.pack(pady=(0, 10))
        else:
            # 通常の解答用紙を使用
            self.original_image = Image.open(self.image_path)
        
        # リサイズ比率の計算
        self.resize_ratio = calculate_resize_ratio(
            self.original_image, target_width=fig_area_w, target_height=window_h
        )
        
        # 画像をリサイズ
        self.resized_image = self.original_image.resize(
            (
                int(self.original_image.width / self.resize_ratio),
                int(self.original_image.height / self.resize_ratio)
            ),
            Image.Resampling.LANCZOS
        )
        
        # tkinter用の画像オブジェクト作成
        self.tk_image = ImageTk.PhotoImage(self.resized_image, master=self.window)
        
        # キャンバス作成
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="black",
            width=self.resized_image.width,
            height=self.resized_image.height,
            highlightthickness=0
        )
        
        # キャンバスに画像を描画
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        self.canvas.pack()
        
        # ボタン作成
        back_button = tk.Button(
            self.button_frame, text='一つ前に戻る', 
            command=self.back_one, width=20, height=4
        )
        back_button.pack()
        
        finish_button = tk.Button(
            self.button_frame, text='入力完了\n(保存して戻る)', 
            command=self.trim_finish, width=20, height=4
        )
        finish_button.pack()
        
        cancel_button = tk.Button(
            self.button_frame, text='topに戻る\n(保存はされません)', 
            command=self.to_top, width=20, height=4
        )
        cancel_button.pack()
        
        # イベントバインド
        self.canvas.bind("<ButtonPress-1>", self.start_point_get)
        self.canvas.bind("<Button1-Motion>", self.rect_drawing)
        self.canvas.bind("<ButtonRelease-1>", self.release_action)
        
        # モーダルウィンドウとして表示
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.focus_set()
    
    def _initialize_csv(self) -> None:
        """CSVファイルを初期化します"""
        ini_path = SETTING_DIR / 'ini.csv'
        trim_path = SETTING_DIR / 'trimData.csv'
        # 既存のtrimData.csvがあれば初期化用ini.csvにコピー
        try:
            if trim_path.exists():
                shutil.copy(trim_path, ini_path)
            else:
                with open(ini_path, 'w', newline='') as f:
                    writer = csv.writer(f, lineterminator='\n')
                    writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y"])
                # trimData.csvも同様に初期化 (定義前にtrim_all_imagesが呼ばれた場合のため)
                with open(trim_path, 'w', newline='') as f:
                    writer = csv.writer(f, lineterminator='\n')
                    writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y"])
        except Exception as e:
            messagebox.showerror('エラー', f'設定ファイル初期化中にエラーが発生しました: {e}')

    def _load_existing_regions(self) -> None:
        """既存のini.csvに記録された領域をキャンバス上に表示します"""
        ini_path = SETTING_DIR / 'ini.csv'
        try:
            with open(ini_path) as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) < 5:
                        continue
                    tag, sx, sy, ex, ey = row
                    # キャンバス描画用に縮尺を戻す
                    rsx, rsy, rex, rey = (
                        int(int(sx) / self.resize_ratio),
                        int(int(sy) / self.resize_ratio),
                        int(int(ex) / self.resize_ratio),
                        int(int(ey) / self.resize_ratio)
                    )
                    color = 'green' if tag == 'name' else 'red'
                    create_rectangle_with_alpha(
                        self.canvas, rsx, rsy, rex, rey,
                        fill=color, alpha=0.3, tag=tag
                    )
                    # テキスト表示
                    self.canvas.create_text(
                        (rsx + rex)/2, (rsy + rey)/2,
                        text=tag, tag=tag + '_text'
                    )
                    self.q_count += 1
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f'既存領域読み込み中にエラー: {e}')

    def start_point_get(self, event) -> None:
        """ドラッグ開始時の処理"""
        # 既存の一時的な矩形を削除
        self.canvas.delete("rectTmp")
        
        # 一時的な矩形を描画
        self.canvas.create_rectangle(
            event.x, event.y, event.x + 1, event.y + 1,
            outline="red", tag="rectTmp"
        )
        
        # 開始座標を保存
        self.start_x = event.x
        self.start_y = event.y
    
    def rect_drawing(self, event) -> None:
        """ドラッグ中の処理"""
        # 画像の範囲内に座標を制限
        end_x = max(0, min(self.resized_image.width, event.x))
        end_y = max(0, min(self.resized_image.height, event.y))
        
        # 一時的な矩形を更新
        self.canvas.coords("rectTmp", self.start_x, self.start_y, end_x, end_y)
    
    def release_action(self, event) -> None:
        """ドラッグ終了時の処理"""
        # 座標を取得
        pos = self.canvas.bbox("rectTmp")
        if not pos:
            return
        
        if self.q_count == 0:
            # 名前領域の場合
            create_rectangle_with_alpha(
                self.canvas, pos[0], pos[1], pos[2], pos[3],
                fill="green", alpha=0.3, tag="nameBox"
            )
            
            self.canvas.create_text(
                (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2,
                text="name", tag="nameText"
            )
            
            # 座標を元の縮尺に戻して保存
            start_x, start_y, end_x, end_y = [
                round(n * self.resize_ratio) for n in self.canvas.coords("rectTmp")
            ]
            
            path = SETTING_DIR / 'ini.csv'
            with open(path, 'a', newline='') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow(["name", start_x, start_y, end_x, end_y])
            
            # 即時にtrimData.csvにも書き込み (ini.csvのみだとtrim_all_imagesで読み込めない)
            trim_path = SETTING_DIR / 'trimData.csv'
            try:
                # 既存データをコピー
                shutil.copy(path, trim_path)
            except Exception as e:
                print(f"trimData.csvの更新に失敗: {e}")
        
        else:
            # 問題領域の場合
            create_rectangle_with_alpha(
                self.canvas, pos[0], pos[1], pos[2], pos[3],
                fill="red", alpha=0.3, tag=f"qBox{self.q_count}"
            )
            
            self.canvas.create_text(
                (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2,
                text=f"Q_{self.q_count}", tag=f"qText{self.q_count}"
            )
            
            # 座標を元の縮尺に戻して保存
            start_x, start_y, end_x, end_y = [
                round(n * self.resize_ratio) for n in self.canvas.coords("rectTmp")
            ]
            
            path = SETTING_DIR / 'ini.csv'
            with open(path, 'a', newline='') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow([f"Q_{str(self.q_count).zfill(4)}", start_x, start_y, end_x, end_y])
            
            # 即時にtrimData.csvにも書き込み (ini.csvのみだとtrim_all_imagesで読み込めない)
            trim_path = SETTING_DIR / 'trimData.csv'
            try:
                # 既存データをコピー
                shutil.copy(path, trim_path)
            except Exception as e:
                print(f"trimData.csvの更新に失敗: {e}")
        
        # カウンタを更新
        self.q_count += 1
    
    def back_one(self) -> None:
        """一つ前の操作に戻ります"""
        if self.q_count == 0:
            return
        
        self.q_count -= 1
        
        # 領域の削除
        if self.q_count == 0:
            self.canvas.delete("nameBox", "nameText", "rectTmp")
            if self.images:
                self.images.pop()
        else:
            self.canvas.delete(f"qBox{self.q_count}", f"qText{self.q_count}", "rectTmp")
            if self.images:
                self.images.pop()
        
        # CSVの最終行を削除
        try:
            path = SETTING_DIR / 'ini.csv'
            with open(path, "r") as readFile:
                lines = readFile.readlines()
            
            with open(path, 'w') as w:
                w.writelines([line for line in lines[:-1]])
            
            # trimData.csvも同期
            trim_path = SETTING_DIR / 'trimData.csv'
            try:
                # 既存データをコピー
                shutil.copy(path, trim_path)
            except Exception as e:
                print(f"trimData.csvの更新に失敗: {e}")
        except Exception as e:
            print(f"CSV行削除中にエラーが発生しました: {e}")
    
    def trim_finish(self) -> None:
        """切り取り定義を完了します"""
        ret = messagebox.askyesno('終了します', '斬り方を決定し、ホームに戻っても良いですか？')
        if ret:
            # ini.csvをtrimData.csvにリネームして保存
            ini_path = SETTING_DIR / 'ini.csv'
            trim_path = SETTING_DIR / 'trimData.csv'
            try:
                # moveではなくcopyでtrimData.csvに反映し、ini.csvも残す
                shutil.copy(str(ini_path), str(trim_path))
                self.window.destroy()
            except Exception as e:
                messagebox.showerror('エラー', f'ファイル保存中にエラーが発生しました: {e}')
    
    def to_top(self) -> None:
        """保存せずにトップ画面に戻ります"""
        ret = messagebox.askyesno('保存しません', '作業中のデータは保存されません。\n画面を移動しますか？')
        if ret:
            self.q_count = 0
            self.window.destroy()