"""
一覧形式で採点を行うウィンドウクラス
"""
import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from typing import List, Dict, Optional, Any, Tuple, Callable, Literal
import time

from ...core.grader import Grader
from ...utils.image_utils import (
    resize_image_by_scale, create_thumbnail_for_grid, 
    calculate_whiteness, get_image_with_score_overlay
)
from ...utils.file_utils import SETTING_DIR, ANSWER_DATA_DIR, get_sorted_image_files

# 採点モードの定義
GradingMode = Literal["continuous", "single", "fixed"]


class GridGradingWindow:
    """一覧採点ウィンドウ"""
    
    def __init__(self, parent: tk.Tk, question_id: str):
        """
        初期化処理
        
        Args:
            parent: 親ウィンドウ
            question_id: 採点する問題ID
        """
        self.parent = parent
        self.question_id = question_id
        
        # グレーダーのインスタンス
        self.grader = Grader()
        
        # 画像表示関連の変数
        self.image_files = []  # 未採点ファイルパスのリスト
        self.graded_files = {}  # 点数ごとの採点済みファイルのリスト {score: [filepath, ...]}
        self.image_cache = {}  # 画像キャッシュ {filepath: PIL.Image}
        self.thumbnail_cache = {}  # サムネイルキャッシュ {filepath: PIL.Image}
        self.tk_images = {}  # tkinter用画像オブジェクト {filepath: PhotoImage}
        self.filename_list = []  # ファイル名リスト
        
        # 採点データ
        self.score_dict = {}  # {ファイルパス: スコア}
        self.whiteness_dict = {}  # {ファイルパス: 白さの値}
        
        # 選択状態
        self.selected_items = set()  # 選択された画像のパスセット
        
        # 表示用の設定
        self.thumbnail_size = 150  # サムネイル一辺のサイズ（ピクセル）
        self.scale_factor = 1.0  # 画像の表示倍率
        self.columns = 4  # グリッドの列数
        self.sort_mode = "filename"  # ソートモード（"filename", "score_asc", "score_desc", "whiteness"）
        self.disable_auto_sort = True  # 自動ソート無効フラグ（True: ボタンを押したときのみソート）
        
        # 模範解答関連の変数
        self.model_answer_window = None  # 模範解答表示用ウィンドウ
        self.model_answer_canvas = None  # 模範解答表示用キャンバス
        self.model_answer_image = None   # 模範解答画像
        self.model_answer_tk_image = None  # tkinter用の模範解答画像
        self.model_answer_zoom = 1.0     # 模範解答画像の拡大率
        
        # ソート結果のキャッシュ
        self.sorted_files_cache = None
        self.need_resort = True  # ソートが必要かどうかのフラグ
        
        # 採点モード関連の変数
        self.grading_mode: GradingMode = "single"  # デフォルトは「一つずつクリック採点」モード
        self.active_score = ""  # 連続クリック採点モードでのアクティブな点数
        self.current_active_item = None  # 一つずつクリック採点モードでのアクティブなアイテム
        self.fixed_mode_index = 0  # 固定採点モードでの現在のインデックス
        
        # 許可されている点数のリスト
        self.allowed_scores = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        
        # ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("一覧採点 - " + question_id)
        self.window.geometry("1200x800")
        
        # UI要素の作成
        self._create_ui()
        
        # 画像の読み込み
        self._load_files()
        
        # モーダルウィンドウとして表示
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.focus_set()
        self.window.wait_window()
    
    def _create_ui(self) -> None:
        """UI要素を作成します"""
        # メインレイアウト
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ヘッダー(コントロールフレーム) - 2行に明確に分ける
        self.control_frame_top = tk.Frame(self.main_frame)
        self.control_frame_top.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.control_frame_middle = tk.Frame(self.main_frame)
        self.control_frame_middle.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        self.control_frame_bottom = tk.Frame(self.main_frame)
        self.control_frame_bottom.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # タイトルラベル (最上段中央)
        title_label = tk.Label(
            self.control_frame_top, 
            text=f"問題 {self.question_id} の採点", 
            font=("", 14, "bold")
        )
        title_label.pack(side=tk.TOP, pady=(0, 5))
        
        # ソート方法選択 (中段左側)
        sort_label = tk.Label(self.control_frame_middle, text="並び順:")
        sort_label.pack(side=tk.LEFT, padx=5)
        
        # ソートボタンフレーム
        self.sort_buttons_frame = tk.Frame(self.control_frame_middle)
        self.sort_buttons_frame.pack(side=tk.LEFT, padx=5)
        
        # ソートボタンの作成
        sort_buttons = [
            ("ファイル名順", "filename"),
            ("点数順(昇順)", "score_asc"),
            ("点数順(降順)", "score_desc"),
            ("白さ順", "whiteness"),
        ]
        
        self.sort_mode = "filename"  # デフォルトのソートモード
        
        for text, mode in sort_buttons:
            btn = tk.Button(
                self.sort_buttons_frame,
                text=text,
                width=10,
                command=lambda m=mode: self._sort_by_mode(m),
                relief=tk.RAISED if mode != self.sort_mode else tk.SUNKEN
            )
            btn.pack(side=tk.LEFT, padx=2)
            if mode == self.sort_mode:
                btn.config(bg="#e1e1ff")  # 現在のソートモードを強調表示
        
        # 模範解答ボタン (中段右側)
        self.model_answer_btn = tk.Button(
            self.control_frame_middle,
            text="模範解答を表示",
            command=self.show_model_answer,
            width=15,
            bg="#ffffe0",  # 薄い黄色
            relief=tk.RAISED,
            borderwidth=2
        )
        self.model_answer_btn.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 採点モード選択 (中段右側、模範解答ボタンの左)
        mode_label = tk.Label(self.control_frame_middle, text="採点モード:")
        mode_label.pack(side=tk.RIGHT, padx=(20, 5))
        
        self.mode_var = tk.StringVar(value="一つずつクリック採点")
        mode_options = ["一つずつクリック採点", "連続クリック採点", "数字キーで連続採点"]
        
        self.mode_menu = ttk.Combobox(
            self.control_frame_middle, 
            textvariable=self.mode_var, 
            values=mode_options,
            state="readonly",
            width=20
        )
        self.mode_menu.current(0)
        self.mode_menu.pack(side=tk.RIGHT, padx=5)
        self.mode_menu.bind("<<ComboboxSelected>>", self._on_mode_change)
        
        # 画像サイズスライダー (下段左側)
        size_label = tk.Label(self.control_frame_bottom, text="表示サイズ:")
        size_label.pack(side=tk.LEFT, padx=5)
        
        self.size_var = tk.DoubleVar(value=self.thumbnail_size)
        self.size_slider = ttk.Scale(
            self.control_frame_bottom,
            from_=50,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.size_var,
            length=150
        )
        self.size_slider.pack(side=tk.LEFT, padx=5)
        self.size_slider.bind("<ButtonRelease-1>", self._on_size_change)
        
        # 現在のサイズ表示ラベル
        self.size_value_label = tk.Label(self.control_frame_bottom, text=f"{self.thumbnail_size}px")
        self.size_value_label.pack(side=tk.LEFT, padx=(2, 10))
        
        # 列数設定
        col_label = tk.Label(self.control_frame_bottom, text="列数:")
        col_label.pack(side=tk.LEFT)
        
        self.col_var = tk.IntVar(value=self.columns)
        self.col_slider = ttk.Scale(
            self.control_frame_bottom,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.col_var,
            length=120
        )
        self.col_slider.pack(side=tk.LEFT, padx=5)
        self.col_slider.bind("<ButtonRelease-1>", self._on_column_change)
        
        # 現在の列数表示ラベル
        self.col_value_label = tk.Label(self.control_frame_bottom, text=f"{self.columns}列")
        self.col_value_label.pack(side=tk.LEFT, padx=(2, 10))
        
        # 選択情報表示ラベル
        self.selection_info = tk.Label(
            self.control_frame_bottom,
            text="選択: 0 件",
            width=10
        )
        self.selection_info.pack(side=tk.LEFT, padx=10)
        
        # 採点ボタン (下段右端に配置し、大きくする)
        self.grade_button = tk.Button(
            self.control_frame_bottom,
            text="採点実行",
            command=self.execute_grading,
            width=15,  # 幅を大きく
            height=2,   # 高さを大きく
            font=("", 12, "bold"),  # フォントを大きく
            bg="#4CAF50",  # 緑色の背景
            fg="white"     # 白色の文字
        )
        self.grade_button.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 戻るボタン (下段右端に配置し、少し大きくする)
        self.exit_button = tk.Button(
            self.control_frame_bottom,
            text="戻る",
            command=self.exit_grading,
            width=10,  # 幅を大きく
            height=2,   # 高さを少し大きく
            font=("", 11),  # フォントを少し大きく
            bg="#f0f0f0"
        )
        self.exit_button.pack(side=tk.RIGHT, padx=5)
        
        # 採点進捗表示フレーム
        self.progress_frame = tk.Frame(self.main_frame, height=30, bg="#f8f8f8")
        self.progress_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="採点状況: ",
            font=("", 9),
            bg="#f8f8f8"
        )
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 採点状況のカウント表示ラベル
        self.count_label = tk.Label(
            self.progress_frame,
            text="",
            font=("", 9),
            bg="#f8f8f8"
        )
        self.count_label.pack(side=tk.LEFT)
        
        # 採点モード表示のステータスバー
        self.status_frame = tk.Frame(self.main_frame, height=30, bg="#f0f0f0")
        self.status_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.mode_status_label = tk.Label(
            self.status_frame,
            text="現在のモード: 一つずつクリック採点",
            font=("", 10, "bold"),
            bg="#f0f0f0"
        )
        self.mode_status_label.pack(side=tk.LEFT, padx=10)
        
        self.active_score_label = tk.Label(
            self.status_frame,
            text="",
            font=("", 10),
            bg="#f0f0f0"
        )
        self.active_score_label.pack(side=tk.LEFT, padx=10)
        
        # 複数選択ヒントラベル
        self.selection_hint_label = tk.Label(
            self.status_frame,
            text="Ctrl+クリックで複数選択、Shift+クリックで範囲選択ができます",
            font=("", 9),
            bg="#f0f0f0"
        )
        self.selection_hint_label.pack(side=tk.RIGHT, padx=10)
        
        # キャンバスフレーム（スクロール可能なグリッド表示エリア）
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # スクロールバー
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # キャンバス
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="white",
            yscrollcommand=self.scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        
        # マウスホイールでのスクロールを有効化
        self._bind_mousewheel(self.canvas)
        
        # キャンバスにグリッドフレームを配置
        self.grid_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window(
            0, 0, window=self.grid_frame, anchor=tk.NW
        )
        
        # キャンバスのリサイズ設定
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # フッターフレーム（採点用ボタン）
        self.footer_frame = tk.Frame(self.main_frame)
        self.footer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 採点設定フレーム
        self.grade_control_frame = tk.LabelFrame(self.footer_frame, text="採点操作")
        self.grade_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 点数ボタンフレーム
        self.score_buttons_frame = tk.Frame(self.grade_control_frame)
        self.score_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 点数ボタンを作成
        self.score_buttons = []
        for i in range(10):
            score_btn = tk.Button(
                self.score_buttons_frame,
                text=str(i),
                width=3,
                height=2,
                command=lambda score=str(i): self._set_score_to_selected(score)
            )
            score_btn.pack(side=tk.LEFT, padx=2)
            self.score_buttons.append(score_btn)
        
        # skipボタン
        skip_btn = tk.Button(
            self.score_buttons_frame,
            text="skip",
            width=6,
            height=2,
            command=lambda: self._set_score_to_selected("skip")
        )
        skip_btn.pack(side=tk.LEFT, padx=10)
        
        # 全選択/選択解除ボタン
        select_frame = tk.Frame(self.grade_control_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        select_all_btn = tk.Button(
            select_frame,
            text="全選択",
            width=10,
            command=self._select_all
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        deselect_all_btn = tk.Button(
            select_frame,
            text="選択解除",
            width=10,
            command=self._deselect_all
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        # 説明ラベル
        hint_label = tk.Label(
            select_frame,
            text="Ctrl+クリックで複数選択、Shift+クリックで範囲選択ができます",
            font=("", 9)
        )
        hint_label.pack(side=tk.RIGHT, padx=10)
        
        # キーボードのバインド
        self.window.bind("<Key>", self._on_key_press)
        
    def _load_files(self) -> None:
        """問題フォルダから画像ファイルを読み込みます"""
        # 問題ディレクトリのパス
        question_dir = os.path.join(SETTING_DIR, "output", self.question_id)
        print(f"問題ディレクトリ: {question_dir}")
        
        if not os.path.exists(question_dir):
            messagebox.showerror("エラー", f"問題ディレクトリが見つかりません: {question_dir}")
            self.window.destroy()
            return
        
        # 未採点ファイルを取得
        self.image_files = []
        self.filename_list = []
        
        for file in os.listdir(question_dir):
            file_path = os.path.join(question_dir, file)
            if os.path.isfile(file_path) and not file.startswith('.') and file.lower().endswith(('.jpg', '.jpeg', '.png')):
                self.image_files.append(file_path)
                self.filename_list.append(file)
                
        # 採点済みファイルを取得（点数ごと）
        self.graded_files = {}
        
        for dir_name in os.listdir(question_dir):
            dir_path = os.path.join(question_dir, dir_name)
            if os.path.isdir(dir_path):
                score = dir_name  # ディレクトリ名がスコア
                self.graded_files[score] = []
                
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path) and not file.startswith('.') and file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        self.graded_files[score].append(file_path)
        
        # ファイルをソート
        self.image_files.sort()
        for score, files in self.graded_files.items():
            files.sort()
        
        total_files = len(self.image_files)
        for files in self.graded_files.values():
            total_files += len(files)
        
        if total_files == 0:
            messagebox.showinfo("情報", "表示できる画像ファイルがありません。")
            self.window.destroy()
            return
        
        print(f"読み込んだファイル: 未採点={len(self.image_files)}件, 採点済={total_files - len(self.image_files)}件")
        
        # 画像の白さを事前計算
        self._calculate_image_whiteness()
        
        # 画像を表示
        self._update_grid_view()
        
    def _calculate_image_whiteness(self) -> None:
        """すべての画像の白さを計算します"""
        # 未採点ファイル
        for file_path in self.image_files:
            # 画像をキャッシュとして読み込み、白さを計算
            try:
                img = self._get_image(file_path)
                self.whiteness_dict[file_path] = calculate_whiteness(img)
            except Exception as e:
                print(f"画像の白さ計算エラー: {file_path} - {e}")
                self.whiteness_dict[file_path] = 0.0
        
        # 採点済みファイル
        for score, files in self.graded_files.items():
            for file_path in files:
                try:
                    img = self._get_image(file_path)
                    self.whiteness_dict[file_path] = calculate_whiteness(img)
                except Exception as e:
                    print(f"画像の白さ計算エラー: {file_path} - {e}")
                    self.whiteness_dict[file_path] = 0.0
    
    def _get_image(self, file_path: str) -> Image.Image:
        """
        画像をキャッシュから取得、または読み込みます。
        
        Args:
            file_path: 画像ファイルのパス
            
        Returns:
            Image.Image: 画像オブジェクト
        """
        if file_path in self.image_cache:
            return self.image_cache[file_path]
        
        try:
            img = Image.open(file_path)
            self.image_cache[file_path] = img
            return img
        except Exception as e:
            print(f"画像の読み込みエラー: {file_path} - {e}")
            # エラーの場合はダミー画像を返す
            dummy_img = Image.new('RGB', (200, 100), color='red')
            self.image_cache[file_path] = dummy_img
            return dummy_img
    
    def _get_thumbnail(self, file_path: str, size: int) -> Image.Image:
        """
        サムネイル画像を取得または生成します。
        
        Args:
            file_path: 画像ファイルのパス
            size: サムネイルのサイズ
            
        Returns:
            Image.Image: サムネイル画像
        """
        cache_key = f"{file_path}_{size}"
        
        if cache_key in self.thumbnail_cache:
            return self.thumbnail_cache[cache_key]
        
        # 元画像を取得
        img = self._get_image(file_path)
        
        # サムネイルを作成
        thumbnail = create_thumbnail_for_grid(img, size)
        
        # サムネイルをキャッシュ
        self.thumbnail_cache[cache_key] = thumbnail
        
        return thumbnail
    
    def _update_grid_view(self) -> None:
        """グリッド表示を更新します。ソートは行いません。"""
        start_time = time.time()
        
        # グリッドフレームの子ウィジェットをすべて削除
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        # tk_imagesを初期化（古い参照を削除）        
        self.tk_images = {}
        
        # 現在のファイルリストを使用（ソートしない）
        sorted_files = self._get_sorted_files()
        
        # グリッド表示用のフレームを設定
        self.grid_frame.config(bg="#f0f0f0")  # 薄いグレーの背景
        
        # 現在の列数とサムネイルサイズを取得
        cols = self.columns
        thumb_size = int(self.size_var.get())
        
        # グリッドに画像を追加
        for i, file_path in enumerate(sorted_files):
            # グリッド位置を計算
            row = i // cols
            col = i % cols
            
            # スコア取得
            score = self._get_file_score(file_path)
            
            # 採点状況に応じた背景色を設定
            if score == "":
                # 未採点
                bg_color = "white"
                fg_color = "black"
            elif score == "0":
                # 0点は赤系の背景
                bg_color = "#ffdddd"  # 薄い赤
                fg_color = "black"
            elif score == "skip":
                # スキップはグレー
                bg_color = "#eeeeee"
                fg_color = "#666666"
            else:
                try:
                    # 数値スコアに応じた青のグラデーション (1-9)
                    score_val = int(score)
                    # 明るい青から濃い青へのグラデーション (薄い順)
                    blue_gradients = [
                        "#e3f2fd", "#bbdefb", "#90caf9",
                        "#64b5f6", "#42a5f5", "#2196f3", 
                        "#1e88e5", "#1976d2", "#1565c0"
                    ]
                    bg_color = blue_gradients[min(score_val - 1, 8)]
                    fg_color = "black" if score_val < 7 else "white"  # 濃い青の場合は白文字
                except:
                    # 数値以外の場合はデフォルト
                    bg_color = "#e8f5e9"  # 薄い緑
                    fg_color = "black"
            
            # 画像フレーム
            item_frame = tk.Frame(
                self.grid_frame,
                width=thumb_size + 8,  # 枠線の分を追加
                height=thumb_size + 30 + 8,  # 画像 + ラベル用の高さ + 枠線
                bg=bg_color,
                bd=0,
                highlightthickness=4,  # 枠線の太さ
                highlightbackground=bg_color  # 通常時は背景色と同じ
            )
            
            # 選択状態の場合は黄色の枠線
            if file_path in self.selected_items:
                item_frame.config(highlightbackground="#FFD700")  # 金色/黄色の枠線
                
            # アクティブアイテムの場合は特別な強調
            if file_path == self.current_active_item:
                item_frame.config(
                    highlightbackground="#FF8C00",  # より目立つオレンジ色
                    highlightthickness=5  # より太い枠線
                )
            
            item_frame.grid(row=row, column=col, padx=5, pady=5)
            item_frame.pack_propagate(False)  # サイズを固定
            
            # 中身のコンテナ (背景色を設定するため)
            content_frame = tk.Frame(item_frame, bg=bg_color)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            
            # サムネイルの作成
            thumbnail = self._get_thumbnail(file_path, thumb_size)
            
            # 画像が採点済みかどうかをチェック
            if score:
                # 採点済みの場合、スコアをオーバーレイ表示
                thumbnail = get_image_with_score_overlay(thumbnail, score)
            
            # PhotoImageの作成（tkinterで表示するため）
            photo = ImageTk.PhotoImage(thumbnail)
            self.tk_images[file_path] = photo
            
            # 画像ラベル
            image_label = tk.Label(
                content_frame,
                image=photo,
                bg=bg_color,
                bd=0
            )
            image_label.pack(fill=tk.BOTH, expand=True)
            
            # ファイル名ラベル
            filename = os.path.basename(file_path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            
            file_label = tk.Label(
                content_frame,
                text=filename,
                bg=bg_color,
                fg=fg_color,
                font=("", 8)
            )
            file_label.pack(side=tk.BOTTOM, fill=tk.X)
            
            # 選択イベントのバインド
            image_label.bind("<Button-1>", lambda e, path=file_path: self._on_item_click(e, path))
            file_label.bind("<Button-1>", lambda e, path=file_path: self._on_item_click(e, path))
            content_frame.bind("<Button-1>", lambda e, path=file_path: self._on_item_click(e, path))
            item_frame.bind("<Button-1>", lambda e, path=file_path: self._on_item_click(e, path))
        
        # グリッドフレームのサイズを更新
        self.grid_frame.update_idletasks()
        
        # キャンバスのスクロール領域を更新
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        end_time = time.time()
        print(f"グリッド表示の更新: {end_time - start_time:.3f}秒")
    
    def _get_sorted_files(self) -> List[str]:
        """
        現在のソートモードに基づいてファイルをソートして返します。
        ソートが必要な場合のみソートを実行し、そうでない場合はキャッシュを返します。
        
        Returns:
            List[str]: ソート済みのファイルパスリスト
        """
        # キャッシュがあり、ソートが不要な場合はキャッシュを返す
        if not self.need_resort and self.sorted_files_cache is not None:
            return self.sorted_files_cache
        
        # 全ファイルリストを準備
        all_files = self.image_files.copy()
        for score_files in self.graded_files.values():
            all_files.extend(score_files)
            
        # ソートモードに基づいてソート
        if self.sort_mode == "filename":
            # ファイル名でソート
            sorted_files = sorted(all_files, key=lambda x: os.path.basename(x))
        elif self.sort_mode == "score_asc":
            # スコア昇順でソート (未採点→0→1→...→9)
            sorted_files = sorted(all_files, key=lambda x: self._get_sort_score_value(x))
        elif self.sort_mode == "score_desc":
            # スコア降順でソート (9→...→1→0→未採点)
            sorted_files = sorted(all_files, key=lambda x: self._get_sort_score_value(x), reverse=True)
        elif self.sort_mode == "whiteness":
            # 白さでソート (白い順)
            sorted_files = sorted(all_files, key=lambda x: self.whiteness_dict.get(x, 0.0), reverse=True)
        else:
            # デフォルトはファイル名でソート
            sorted_files = sorted(all_files, key=lambda x: os.path.basename(x))
        
        # ソート結果をキャッシュ
        self.sorted_files_cache = sorted_files
        self.need_resort = False
        
        return sorted_files
    
    def _get_sort_score_value(self, file_path: str) -> float:
        """
        ソート用のスコア値を取得
        未採点:100, skip:50, 0-9:実際の値
        
        Args:
            file_path: ファイルパス
            
        Returns:
            float: ソート用のスコア値
        """
        score = self._get_file_score(file_path)
        if not score:
            return 100.0  # 未採点は最大値
        elif score == "skip":
            return 50.0   # skipは中間値
        else:
            try:
                return float(score)  # 数値スコア
            except ValueError:
                return 0.0  # 数値以外は0とみなす
    
    def _get_file_score(self, file_path: str) -> str:
        """
        ファイルのスコアを取得
        
        Args:
            file_path: ファイルパス
            
        Returns:
            str: スコア文字列 (未採点の場合は空文字)
        """
        # スコア辞書に登録されている場合
        if file_path in self.score_dict:
            return self.score_dict[file_path]
            
        # 採点済みリストから探す
        for score, files in self.graded_files.items():
            if file_path in files:
                return score
                
        # 見つからない場合は未採点
        return ""
    
    def _on_item_click(self, event, file_path: str) -> None:
        """画像アイテムがクリックされた時の処理"""
        # 現在の採点モードによって処理を分岐
        if self.grading_mode == "continuous":
            # 連続クリック採点モード：アクティブなスコアがあれば直接採点
            if self.active_score:
                self.score_dict[file_path] = self.active_score
                print(f"連続クリック採点: {os.path.basename(file_path)} → {self.active_score}")
                self._update_grid_view()
                return
            else:
                # アクティブスコアが設定されていない場合は選択のみ
                self.selected_items = {file_path}
                self.selection_info.config(text="選択: 1 件")
                self._update_grid_view()
                messagebox.showinfo("情報", "連続クリック採点モードでは、先に点数ボタンをクリックしてアクティブな点数を設定してください。")
                return
        
        elif self.grading_mode == "fixed":
            # 固定採点モード：選択して、次のステップでキーボード入力待ち
            self.selected_items = {file_path}
            self.selection_info.config(text="選択: 1 件 (数字キーで採点)")
            self.current_active_item = file_path
            self._update_grid_view()
            return
        
        # 以下は「一つずつクリック採点」モードまたはデフォルト動作
        
        # Ctrlキーが押されている場合は複数選択
        if event.state & 0x0004:  # Ctrlキー
            if file_path in self.selected_items:
                self.selected_items.remove(file_path)
            else:
                self.selected_items.add(file_path)
        
        # Shiftキーが押されている場合は範囲選択
        elif event.state & 0x0001:  # Shiftキー
            if not self.selected_items:
                self.selected_items.add(file_path)
            else:
                # 現在の並び順でファイルリストを取得
                sorted_files = self._get_sorted_files()
                
                # 最後に選択したアイテムのインデックスを見つける
                last_selected = list(self.selected_items)[-1]
                try:
                    start_idx = sorted_files.index(last_selected)
                    end_idx = sorted_files.index(file_path)
                    
                    # 範囲を正規化（常に小さいインデックスから大きいインデックスへ）
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                    
                    # 範囲内のすべてのファイルを選択
                    for i in range(start_idx, end_idx + 1):
                        self.selected_items.add(sorted_files[i])
                    
                except ValueError:
                    # インデックスが見つからない場合は単一選択
                    self.selected_items = {file_path}
        
        # 通常のクリック（単一選択）
        else:
            self.selected_items = {file_path}
        
        # 選択情報を更新
        self.selection_info.config(text=f"選択: {len(self.selected_items)} 件")
        
        # グリッド表示を更新
        self._update_grid_view()
    
    def _sort_by_mode(self, mode: str) -> None:
        """
        指定されたモードでファイルをソートし、グリッド表示を更新します。
        このメソッドは「並び順」ボタンが押されたときにのみ呼び出されます。
        
        Args:
            mode: ソートモード ("filename", "score_asc", "score_desc", "whiteness")
        """
        # 前回と同じモードの場合はソート方法を変更しない
        if mode == self.sort_mode:
            return
            
        # ソートモードを更新
        self.sort_mode = mode
        self.need_resort = True  # ソートが必要な状態にする
        print(f"ソートモードを {mode} に変更しました")
        
        # ソートボタンの表示を更新
        self._update_sort_buttons()
        
        # グリッド表示を更新
        # 明示的にソートが行われるのはここだけ
        self._update_grid_view()
        
    def _update_sort_buttons(self) -> None:
        """ソートボタンの状態を更新します"""
        # ソートボタンフレーム内の全ボタンをリセット
        for btn in self.sort_buttons_frame.winfo_children():
            if isinstance(btn, tk.Button):
                btn.config(relief=tk.RAISED, bg="#f0f0f0")  # デフォルト状態に戻す
                
        # 現在選択されているモードのボタンを強調
        for btn in self.sort_buttons_frame.winfo_children():
            if isinstance(btn, tk.Button):
                # ボタンのテキストからモードを判別
                if btn["text"] == "ファイル名順" and self.sort_mode == "filename":
                    btn.config(relief=tk.SUNKEN, bg="#e1e1ff")
                elif btn["text"] == "点数順(昇順)" and self.sort_mode == "score_asc":
                    btn.config(relief=tk.SUNKEN, bg="#e1e1ff")
                elif btn["text"] == "点数順(降順)" and self.sort_mode == "score_desc":
                    btn.config(relief=tk.SUNKEN, bg="#e1e1ff")
                elif btn["text"] == "白さ順" and self.sort_mode == "whiteness":
                    btn.config(relief=tk.SUNKEN, bg="#e1e1ff")
                    
    def update_score(self, thumbnail_index, score):
        """
        採点結果を更新します
        """
        if thumbnail_index >= len(self.answer_thumbnails):
            return
        
        thumbnail = self.answer_thumbnails[thumbnail_index]
        old_score = thumbnail.score
        thumbnail.score = score
        
        # UIを更新
        self._update_score_label(thumbnail_index)
        self._update_progress_label()
        
        # -------- 自動ソートの部分を削除 --------
        # 自動ソートは行わず、ユーザーがソートボタンを押したときのみソートされるようにする
        # 採点後のリアルタイムソートを無効化
        
        # 変更があったことを記録
        if old_score != score:
            self.has_changes = True
    
    def _sort_and_refresh_grid(self) -> None:
        """
        現在のソートモードに基づいて画像を並べ替え、グリッド表示を更新します
        """
        # ファイル名を現在のソートモードに基づいて並べ替え
        if self.sort_mode == "filename":
            self.filename_list.sort()
        elif self.sort_mode == "score_asc":
            # 点数の昇順
            self.filename_list.sort(key=lambda f: self.score_dict.get(f, ""))
        elif self.sort_mode == "score_desc":
            # 点数の降順
            self.filename_list.sort(key=lambda f: self.score_dict.get(f, ""), reverse=True)
        elif self.sort_mode == "whiteness":
            # 白さの値で並べ替え（昇順 - 白いものが先頭に）
            self.filename_list.sort(key=lambda f: self.whiteness_dict.get(f, 0), reverse=True)
        
        # グリッドを再描画
        self._refresh_grid()
        
        # 採点モードが一つずつクリック採点の場合、アクティブなアイテムを選択
        if self.grading_mode == "single" and self.current_active_item:
            # アクティブなアイテムがリストに存在するかチェック
            if self.current_active_item in self.filename_list:
                # アクティブなアイテムの位置にスクロール
                self._scroll_to_item(self.current_active_item)
        
    def _refresh_grid(self) -> None:
        """
        グリッドビューを再描画します
        """
        # グリッドフレームの既存の子ウィジェットを削除
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        # キャッシュをクリア（すでに作成されたTkイメージを破棄）        
        for img in self.tk_images.values():
            if img:
                del img
        self.tk_images = {}
        
        # グリッドを構築
        row = 0
        col = 0
        
        # 現在の選択状態を維持するための辞書
        frame_dict = {}
        
        # ファイル名リストから完全なパスのリストを作成
        sorted_files = self._get_sorted_files()
        
        for filepath in sorted_files:
            # アイテムフレームを作成
            item_frame = tk.Frame(
                self.grid_frame,
                bd=2,
                relief=tk.RIDGE,
                width=self.thumbnail_size + 20,
                height=self.thumbnail_size + 40
            )
            item_frame.grid(
                row=row,
                column=col,
                padx=5,
                pady=5,
                sticky=tk.NSEW
            )
            item_frame.grid_propagate(False)
            
            # サムネイル画像を取得
            cache_key = f"{filepath}_{self.thumbnail_size}"
            if cache_key not in self.thumbnail_cache:
                # 画像を読み込んでからサムネイルを作成
                img = self._get_image(filepath)
                self.thumbnail_cache[cache_key] = create_thumbnail_for_grid(
                    img, self.thumbnail_size
                )
                
            thumbnail = self.thumbnail_cache[cache_key]
            
            # TkinterのPhotoImageオブジェクトを作成（参照を保持するために格納）
            self.tk_images[filepath] = ImageTk.PhotoImage(thumbnail)
            
            # 画像ラベルを作成
            img_label = tk.Label(
                item_frame,
                image=self.tk_images[filepath],
                bd=0
            )
            img_label.pack(pady=(5, 0))
            
            # ファイル名ラベルの作成
            name_label = tk.Label(
                item_frame,
                text=os.path.basename(filepath),
                font=("", 8),
                wraplength=self.thumbnail_size
            )
            name_label.pack(side=tk.BOTTOM, fill=tk.X, pady=0)
            
            # 点数ラベルを作成（もし存在すれば）
            score = self.score_dict.get(filepath, "")
            if score:
                score_label = tk.Label(
                    item_frame,
                    text=f"点数: {score}",
                    font=("", 9, "bold"),
                    bg="#ffffcc",
                    width=10
                )
                score_label.pack(side=tk.BOTTOM, fill=tk.X, pady=0)
                
            # アクティブな項目の背景色を変更
            if self.grading_mode == "single" and filepath == self.current_active_item:
                item_frame.config(bd=3, relief=tk.RAISED, bg="#e1e1ff")
                
            # 選択済みの項目の背景色を変更
            if filepath in self.selected_items:
                item_frame.config(bd=3, relief=tk.SUNKEN, bg="#ffe1e1")
                
            # クリックイベントの設定（_handle_item_clickを_on_item_clickに修正）
            item_frame.bind("<Button-1>", lambda e, path=filepath: self._on_item_click(e, path))
            img_label.bind("<Button-1>", lambda e, path=filepath: self._on_item_click(e, path))
            name_label.bind("<Button-1>", lambda e, path=filepath: self._on_item_click(e, path))
            
            # 辞書にフレームを格納
            frame_dict[filepath] = item_frame
            
            # 次の列または行に移動
            col += 1
            if col >= self.columns:
                col = 0
                row += 1
                
        # グリッドフレームのサイズを更新
        self.grid_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
    def _set_score_to_selected(self, score: str) -> None:
        """
        選択された画像に対して点数をセットします
        
        Args:
            score: 設定する点数
        """
        # 採点モードが連続クリック採点の場合、アクティブな点数を記録
        if self.grading_mode == "continuous":
            self.active_score = score
            self.active_score_label.config(text=f"設定点数: {score}")
            # アクティブな点数ボタンの色を変更
            for btn in self.score_buttons:
                if btn["text"] == score:
                    btn.config(bg="#ffcccc")  # アクティブなボタンをハイライト
                else:
                    btn.config(bg="#f0f0f0")  # その他のボタンを通常の色に戻す
        
        # 選択されているアイテムがある場合
        if self.selected_items:
            # 現在のソート順のファイルリストを取得（採点前）
            sorted_files = self._get_sorted_files()
            
            # 選択されている各アイテムに点数をセット
            for filepath in self.selected_items:
                if score == "skip":
                    # skipの場合は点数を削除
                    if filepath in self.score_dict:
                        del self.score_dict[filepath]
                else:
                    # 点数を設定
                    self.score_dict[filepath] = score
            
            # 現在のアクティブアイテムと位置を記録
            current_active = self.current_active_item
            current_idx = -1
            if current_active in sorted_files:
                current_idx = sorted_files.index(current_active)
            
            # 選択をクリア
            self.selected_items.clear()
            self.selection_info.config(text="選択: 0 件")
            
            # 採点の進捗を更新
            self._update_progress_info()
            
            # 採点モードごとの処理
            if self.grading_mode == "single" and current_active:
                # 一つずつクリック採点モード - 並び順を維持したまま次のアイテムをアクティブにする
                if current_idx >= 0 and current_idx < len(sorted_files) - 1:
                    next_idx = current_idx + 1
                    self.current_active_item = sorted_files[next_idx]
                    self.selected_items = {self.current_active_item}
                    # 次のアイテムが表示されるようにスクロール
                    self._scroll_to_item(self.current_active_item)
                else:
                    # インデックスが無効な場合は選択解除
                    self.current_active_item = None

            # 固定順採点モードでは次のアイテムをアクティブにする
            elif self.grading_mode == "fixed":
                # 現在のインデックスを更新
                self.fixed_mode_index += 1
                
                # インデックスが範囲内かチェック
                if self.fixed_mode_index < len(sorted_files):
                    self.current_active_item = sorted_files[self.fixed_mode_index]
                    self.selected_items = {self.current_active_item}
                    # 次のアイテムが表示されるようにスクロール
                    self._scroll_to_item(self.current_active_item)
                else:
                    # すべてのアイテムが採点済みの場合
                    self.current_active_item = None
                    messagebox.showinfo("採点完了", "すべての画像の採点が完了しました。")
            
            # グリッドを更新（採点後は自動でソートせず、現在の表示順を維持）            
            # _update_grid_viewを呼び出すが、need_resortフラグはFalseのまま
            self._update_grid_view()
    
    def _on_sort_change(self, event=None) -> None:
        """ソート方法が変更された時の処理（レガシー機能、非推奨）"""
        pass  # 実装を無効化（ボタンに置き換え）
    
    def _on_size_change(self, event=None) -> None:
        """サムネイルサイズが変更された時の処理"""
        new_size = int(self.size_var.get())
        if (new_size != self.thumbnail_size):
            self.thumbnail_size = new_size
            self.size_value_label.config(text=f"{self.thumbnail_size}px")
            self._update_grid_view()
    
    def _on_column_change(self, event=None) -> None:
        """列数が変更された時の処理"""
        new_cols = int(self.col_var.get())
        if new_cols != self.columns:
            self.columns = new_cols
            self.col_value_label.config(text=f"{self.columns}列")
            self._update_grid_view()
    
    def _on_mode_change(self, event=None) -> None:
        """採点モードが変更された時の処理"""
        selected_text = self.mode_menu.get()
        
        # 前のモードのリセット処理
        self.active_score = ""
        self.current_active_item = None
        
        # すべての点数ボタンを通常状態に戻す
        for btn in self.score_buttons:
            btn.config(relief=tk.RAISED, bg="SystemButtonFace")
        
        if selected_text == "一つずつクリック採点":
            self.grading_mode = "single"
            self.mode_status_label.config(text="現在のモード: 一つずつクリック採点")
            self.active_score_label.config(text="画像を選択してから点数をクリック")
            
        elif selected_text == "連続クリック採点":
            self.grading_mode = "continuous"
            self.mode_status_label.config(text="現在のモード: 連続クリック採点")
            self.active_score_label.config(text="点数ボタンを選択してください")
            
        elif selected_text == "数字キーで連続採点":
            self.grading_mode = "fixed"
            self.mode_status_label.config(text="現在のモード: 数字キーで連続採点")
            self.active_score_label.config(text="数字キーで採点すると自動的に次に進みます")
            
            # 数字キーで連続採点モードでは最初の画像が選択されている状態にする
            sorted_files = self._get_sorted_files()
            if sorted_files:
                # インデックスをリセット
                self.fixed_mode_index = 0
                self.current_active_item = sorted_files[0]
                self.selected_items = {sorted_files[0]}
                self.selection_info.config(text="選択: 1 件 (数字キーで採点)")
                
                # 最初の画像が表示されるようにスクロール
                self._scroll_to_item(self.current_active_item)
        
        # ヒント表示を更新
        self._update_mode_hint()
        
        # グリッド表示を更新
        self._update_grid_view()
    
    def _on_canvas_configure(self, event=None) -> None:
        """キャンバスがリサイズされた時の処理"""
        # グリッドフレームの幅をキャンバスの幅に合わせる
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_key_press(self, event) -> None:
        """キー入力に対する処理"""
        key = event.char
        
        # 数字キーの場合は採点
        if key in self.allowed_scores:
            # 固定採点モードでは現在のアクティブアイテムに採点
            if self.grading_mode == "fixed":
                # アクティブアイテムがない場合は最初のアイテムをアクティブにする
                if not self.current_active_item:
                    sorted_files = self._get_sorted_files()
                    if sorted_files:
                        self.fixed_mode_index = 0
                        self.current_active_item = sorted_files[0]
                        self.selected_items = {self.current_active_item}
                
                # アクティブアイテムがある場合は採点
                if self.current_active_item:
                    print(f"数字キー採点: {os.path.basename(self.current_active_item)} → {key}")
                    self.selected_items = {self.current_active_item}
                    self._set_score_to_selected(key)
                return
            
            # 一つずつクリック採点モードでは通常の動作
            elif self.grading_mode == "single" and self.selected_items:
                self._set_score_to_selected(key)
                return
            
            # 連続クリック採点モードでは数字キーでもアクティブな点数を設定する
            elif self.grading_mode == "continuous":
                # アクティブスコアをトグルする
                if self.active_score == key:
                    self.active_score = ""
                    self.active_score_label.config(text="")
                else:
                    self.active_score = key
                    self.active_score_label.config(text=f"アクティブな点数: {key}")
                
                # ボタンの見た目を更新
                for btn in self.score_buttons:
                    if btn.cget('text') == key and self.active_score:
                        btn.config(relief=tk.SUNKEN, bg="#add8e6")  # 押された状態、青色背景
                    else:
                        btn.config(relief=tk.RAISED, bg="SystemButtonFace")  # 通常状態
                return
        
        # スペースキーの場合はskip
        elif key == " ":
            # 固定採点モードではskipでも次に進む
            if self.grading_mode == "fixed" and self.current_active_item:
                self.selected_items = {self.current_active_item}
                self._set_score_to_selected("skip")
            # その他のモードでは通常のskip動作
            elif self.selected_items:
                self._set_score_to_selected("skip")
        
        # モード切り替えショートカット
        elif key == "1":  # 1キーで一つずつクリック採点モード
            self.mode_var.set("一つずつクリック採点")
            self._on_mode_change()
        elif key == "2":  # 2キーで連続クリック採点モード
            self.mode_var.set("連続クリック採点")
            self._on_mode_change()
        elif key == "3":  # 3キーで固定採点モード
            self.mode_var.set("数字キーで連続採点")
            self._on_mode_change()
    
    def _deselect_all(self) -> None:
        """すべての画像の選択を解除します"""
        self.selected_items = set()
        self.current_active_item = None
        self.selection_info.config(text="選択: 0 件")
        self._update_grid_view()
    
    def _select_all(self) -> None:
        """すべての画像を選択します"""
        # 現在の並び順でファイルをすべて選択
        sorted_files = self._get_sorted_files()
        self.selected_items = set(sorted_files)
        self.selection_info.config(text=f"選択: {len(self.selected_items)} 件")
        self._update_grid_view()
    
    def execute_grading(self) -> None:
        """採点結果を保存します"""
        # 採点されたファイルがない場合
        if not self.score_dict:
            messagebox.showinfo("情報", "採点されたファイルがありません。")
            return
        
        # 確認ダイアログ
        ret = messagebox.askyesno(
            '採点実行確認',
            f'{len(self.score_dict)}件のファイルを採点します。\n実行してよろしいですか？'
        )
        if not ret:
            return
        
        success_count = 0
        for file_path, score in self.score_dict.items():
            # 有効なスコアの場合のみ処理
            if score in self.allowed_scores or score == "skip":
                student_file = os.path.basename(file_path)
                question_dir = os.path.join(SETTING_DIR, "output", self.question_id)
                
                # 元のファイルパスを確認（すでに移動されている場合もある）
                if os.path.exists(file_path):
                    original_path = file_path
                else:
                    # 元のパスが存在しない場合は、未採点フォルダのパスを試す
                    original_path = os.path.join(question_dir, student_file)
                    if not os.path.exists(original_path):
                        # それも存在しない場合は、他の点数フォルダにあるか探す
                        found = False
                        for old_score, files in self.graded_files.items():
                            for old_file in files:
                                if os.path.basename(old_file) == student_file:
                                    original_path = old_file
                                    found = True
                                    break
                            if found:
                                break
                        
                        if not found:
                            print(f"ファイルが見つかりません: {student_file}")
                            continue
                
                # スコアディレクトリを作成
                score_dir = os.path.join(question_dir, str(score))
                os.makedirs(score_dir, exist_ok=True)
                
                # ファイルを移動
                try:
                    target_path = os.path.join(score_dir, student_file)
                    shutil.move(original_path, target_path)
                    print(f"ファイル移動: {original_path} → {target_path}")
                    success_count += 1
                except Exception as e:
                    print(f"ファイル移動エラー: {e}")
        
        # 採点結果をExcelに保存
        print("Excel出力を開始します")
        self.grader.create_excel_report()
        
        # 結果通知
        if success_count > 0:
            messagebox.showinfo(
                "採点保存",
                f"採点結果を保存しました。({success_count}件)\n"
                "skipした項目は、採点されていません。"
            )
            
            # 画像の再読み込み
            self.score_dict = {}  # 採点データをクリア
            self.selected_items = set()  # 選択をクリア
            self._load_files()  # ファイルを再読み込み
        else:
            messagebox.showinfo("採点保存", "採点対象がありませんでした。")
    
    def exit_grading(self) -> None:
        """採点を中断してトップ画面に戻ります"""
        if self.score_dict:
            ret = messagebox.askyesno('終了確認', '採点結果が保存されていません。\n終了してもよろしいですか？')
            if not ret:
                return
        
        # 模範解答ウィンドウが開いていれば閉じる
        self.close_model_answer()
        self.window.destroy()
    
    def on_closing(self) -> None:
        """ウィンドウを閉じる際の処理"""
        # 模範解答ウィンドウが開いていれば閉じる
        self.close_model_answer()
        self.exit_grading()
    
    def _update_mode_hint(self) -> None:
        """現在の採点モードに合わせてヒント表示を更新します"""
        mode_hints = {
            "single": "【一つずつクリック採点】まず画像を選択し、次に点数ボタンをクリックします。Ctrl+クリックで複数選択、Shift+クリックで範囲選択ができます。",
            "continuous": "【連続クリック採点】まず点数ボタンを選択してアクティブにし、その後クリックした画像すべてに同じ点数が付きます。",
            "fixed": "【数字キーで連続採点】画像を選択し、キーボードの数字キーで採点します。自動的に次の画像に移動します。"
        }
        
        # モード説明フレームがなければ作成
        if not hasattr(self, 'hint_frame'):
            self.hint_frame = tk.Frame(self.status_frame, bg="#f0f0f0")
            self.hint_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
            
            self.mode_hint_label = tk.Label(
                self.hint_frame,
                text="",
                font=("", 9),
                bg="#f0f0f0",
                fg="#333333",
                justify=tk.LEFT
            )
            self.mode_hint_label.pack(side=tk.RIGHT)
            
        # 現在のモードに合わせてヒントテキストを更新
        if self.grading_mode in mode_hints:
            self.mode_hint_label.config(text=mode_hints[self.grading_mode])
            
        # 「一つずつクリック採点」モード以外では複数選択ヒントを非表示
        if hasattr(self, 'selection_hint_label'):
            if self.grading_mode == "single":
                self.selection_hint_label.pack(side=tk.RIGHT, padx=10)
            else:
                self.selection_hint_label.pack_forget()
    
    def _bind_mousewheel(self, widget):
        """マウスホイールイベントをウィジェットにバインドします"""
        try:
            # グローバルバインドに戻す - これが動作する方法
            if sys.platform.startswith("win") or sys.platform == "darwin":  # Windows / macOS
                widget.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
            else:  # Linux
                widget.bind_all("<Button-4>", self._on_mousewheel, add="+")
                widget.bind_all("<Button-5>", self._on_mousewheel, add="+")
        except Exception as e:
            print(f"マウスホイールバインドエラー（無視します）: {e}")
    
    def _on_mousewheel(self, event) -> None:
        """マウスホイールでのスクロール処理"""
        try:
            # キャンバスが存在し、有効かチェック
            if not hasattr(self, 'canvas') or not self.canvas or not self.canvas.winfo_exists():
                return "break"  # 破棄済みなら何もしない
            
            # Windows環境 (event.deltaが存在する場合)
            if hasattr(event, "delta") and event.delta:
                step = -1 if event.delta > 0 else 1
            # Linux環境 (num は 4↑ 5↓)
            else:
                step = -1 if getattr(event, "num", 0) == 4 else 1
            
            # スクロールを実行
            self.canvas.yview_scroll(step, "units")
        except Exception:
            # エラーを表示せずに静かに失敗
            pass
            
        # イベントの伝播を防止
        return "break"
    
    def _update_progress_info(self) -> None:
        """採点進捗情報を更新します"""
        # 未採点、採点済み、スキップされたファイルの数を集計
        total_files = 0
        graded_count = 0
        skip_count = 0
        
        # 未採点ファイルと現在のセッションで採点したファイル
        for file_path in self.image_files:
            total_files += 1
            score = self._get_file_score(file_path)
            if score == "skip":
                skip_count += 1
            elif score:
                graded_count += 1
                
        # 既に採点済みのファイル
        for score, files in self.graded_files.items():
            for file_path in files:
                total_files += 1
                if score == "skip":
                    skip_count += 1
                else:
                    graded_count += 1
        
        # 残りの未採点ファイル数
        ungraded_count = total_files - graded_count - skip_count
        
        # 進捗テキスト更新
        progress_text = f"採点: {graded_count}枚 / スキップ: {skip_count}枚 / 未採点: {ungraded_count}枚 (合計: {total_files}枚)"
        self.count_label.config(text=progress_text)
        
        # 進捗率を表示 (オプション)
        if total_files > 0:
            # スキップも含めた処理済み割合
            progress_rate = (graded_count + skip_count) / total_files * 100
            progress_info = f" - 進捗率: {progress_rate:.1f}%"
            self.progress_label.config(text=f"採点状況: {progress_info}")
        else:
            self.progress_label.config(text="採点状況: ")
    
    def _show_continuation_dialog(self) -> bool:
        """
        反復処理を続行するかどうかを確認するダイアログを表示します。
        
        Returns:
            bool: ユーザーが「はい」を選択した場合はTrue、それ以外の場合はFalse
        """
        # 反復処理確認ダイアログを表示
        result = messagebox.askyesno(
            "処理の確認", 
            "反復処理を続行しますか?",
            icon="question"
        )
        return result

    def _scroll_to_item(self, file_path: str) -> None:
        """
        指定されたファイルパスに対応するアイテムが表示されるようにスクロールします。

        Args:
            file_path: スクロール先のファイルパス
        """
        # ファイルが存在するかチェック
        sorted_files = self._get_sorted_files()
        if file_path not in sorted_files:
            return

        # アイテムのインデックスを取得
        file_index = sorted_files.index(file_path)
        
        # 行と列の位置を計算（グリッド内での位置）
        row = file_index // self.columns
        
        # キャンバスの表示領域を計算
        canvas_height = self.canvas.winfo_height()
        
        # アイテムの高さとパディングを考慮した1行の高さを計算
        row_height = self.thumbnail_size + 40 + 10  # サムネイル + ラベル + パディング
        
        # スクロール位置を計算
        # アイテムをある程度中央に表示するようにスクロール
        scroll_position = (row * row_height) / self.grid_frame.winfo_height()
        
        # スクロール位置を設定（0.0-1.0の範囲）
        self.canvas.yview_moveto(max(0, min(1, scroll_position)))

    def show_model_answer(self, event=None) -> None:
        """
        模範解答を別ウィンドウで表示します。
        grading_windowの実装に合わせて、正しいパスから画像を探索します。
        """
        try:
            # すでにウィンドウが開いている場合は前面表示して終了
            if self.model_answer_window and self.model_answer_window.winfo_exists():
                self.model_answer_window.lift()
                return
                
            # 模範解答画像のパスを取得（正しい場所: ANSWER_DATA_DIR/output/問題ID/ 配下）
            answer_output_dir = os.path.join(ANSWER_DATA_DIR, "output", self.question_id)
            
            if not os.path.exists(answer_output_dir):
                messagebox.showinfo("情報", f"問題 {self.question_id} の模範解答ディレクトリが見つかりません。")
                return
                
            # ディレクトリ内の画像ファイルを探す
            answer_files = [os.path.join(answer_output_dir, f) for f in os.listdir(answer_output_dir) 
                          if os.path.isfile(os.path.join(answer_output_dir, f)) and 
                          f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                
            if not answer_files:
                messagebox.showinfo("情報", f"問題 {self.question_id} の模範解答画像が見つかりません。")
                return
                
            # 画像を読み込み（最初の画像を使用）
            self.model_answer_image = Image.open(answer_files[0])
            img = self.model_answer_image
            
            # ウィンドウを作成
            self.model_answer_window = tk.Toplevel(self.window)
            self.model_answer_window.title(f"模範解答 - {self.question_id}")
            self.model_answer_window.protocol("WM_DELETE_WINDOW", self.close_model_answer)
            
            # 画面サイズを取得して、適切なウィンドウサイズを設定
            screen_width = self.model_answer_window.winfo_screenwidth()
            screen_height = self.model_answer_window.winfo_screenheight()
            
            # 画像サイズを取得
            img_width, img_height = img.size
            
            # 画面サイズの80%を上限として、画像のアスペクト比を維持したウィンドウサイズを計算
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)
            
            # 縦横比を維持したまま、最大サイズに収める
            if img_width > max_width or img_height > max_height:
                # 縮小が必要な場合
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                ratio = min(width_ratio, height_ratio)
                
                display_width = int(img_width * ratio)
                display_height = int(img_height * ratio)
                self.model_answer_zoom = ratio  # 拡大率を記録
            else:
                # 元のサイズでOK
                display_width = img_width
                display_height = img_height
                self.model_answer_zoom = 1.0  # 等倍
                
            # ウィンドウサイズを設定（ボタンなどのUIの分少し大きく）
            window_width = display_width
            window_height = display_height + 40  # ボタン用の領域を追加
            
            # ウィンドウの位置を設定（画面中央）
            position_x = (screen_width - window_width) // 2
            position_y = (screen_height - window_height) // 2
            
            # ウィンドウのサイズと位置を設定
            self.model_answer_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
            
            # 操作用フレーム
            control_frame = tk.Frame(self.model_answer_window)
            control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
            
            # 拡大・縮小ボタン
            zoom_in_btn = tk.Button(
                control_frame, 
                text="拡大(+)", 
                command=self.zoom_in_model_answer
            )
            zoom_in_btn.pack(side=tk.LEFT, padx=5)
            
            zoom_out_btn = tk.Button(
                control_frame, 
                text="縮小(-)", 
                command=self.zoom_out_model_answer
            )
            zoom_out_btn.pack(side=tk.LEFT, padx=5)
            
            reset_btn = tk.Button(
                control_frame, 
                text="等倍表示", 
                command=self.reset_model_answer_zoom
            )
            reset_btn.pack(side=tk.LEFT, padx=5)
            
            # 現在の表示倍率ラベル
            self.zoom_label = tk.Label(
                control_frame, 
                text=f"表示倍率: {self.model_answer_zoom:.1f}x"
            )
            self.zoom_label.pack(side=tk.LEFT, padx=10)
            
            # 画像ファイル名を表示
            file_label = tk.Label(
                control_frame, 
                text=f"ファイル: {os.path.basename(answer_files[0])}"
            )
            file_label.pack(side=tk.RIGHT, padx=10)
            
            # キャンバス（スクロール可能）を作成
            canvas_frame = tk.Frame(self.model_answer_window)
            canvas_frame.pack(fill=tk.BOTH, expand=True)
            
            # 水平・垂直スクロールバー
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # キャンバス
            self.model_answer_canvas = tk.Canvas(
                canvas_frame,
                width=display_width,
                height=display_height,
                xscrollcommand=h_scrollbar.set,
                yscrollcommand=v_scrollbar.set
            )
            self.model_answer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # スクロールバーとキャンバスを関連付け
            h_scrollbar.config(command=self.model_answer_canvas.xview)
            v_scrollbar.config(command=self.model_answer_canvas.yview)
            
            # マウスホイールでのスクロール対応 - ローカルバインドに変更
            self.model_answer_canvas.bind("<MouseWheel>", self._on_model_answer_mousewheel)
            if not sys.platform.startswith("win"):  # Linux用
                self.model_answer_canvas.bind("<Button-4>", self._on_model_answer_mousewheel)
                self.model_answer_canvas.bind("<Button-5>", self._on_model_answer_mousewheel)
            
            # 画像を表示
            self._update_model_answer_display()
            
            # 画像ウィンドウを前面に表示
            self.model_answer_window.lift()
            self.model_answer_window.focus_set()
            
            # 採点ウィンドウも引き続き操作できるように
            self.model_answer_window.transient(self.window)
            # grab_set()を削除し、非モーダル動作に変更
            
            # キーボードショートカット
            self.model_answer_window.bind("<plus>", self.zoom_in_model_answer)
            self.model_answer_window.bind("<minus>", self.zoom_out_model_answer)
            self.model_answer_window.bind("<0>", self.reset_model_answer_zoom)
            self.model_answer_window.bind("<Escape>", self.close_model_answer)
            
        except Exception as e:
            print(f"模範解答画像の表示エラー: {e}")
            messagebox.showerror("エラー", f"模範解答画像の表示中にエラーが発生しました:\n{e}")
    
    def _update_model_answer_display(self) -> None:
        """
        模範解答画像の表示を更新します。
        """
        if not self.model_answer_image or not self.model_answer_window or not self.model_answer_canvas:
            return
            
        try:
            # 元の画像を現在の拡大率で変更
            img_width, img_height = self.model_answer_image.size
            new_width = int(img_width * self.model_answer_zoom)
            new_height = int(img_height * self.model_answer_zoom)
            
            # リサイズした画像を作成
            resized_img = self.model_answer_image.resize((new_width, new_height), Image.LANCZOS)
            
            # tkinter用の画像オブジェクトを作成
            self.model_answer_tk_image = ImageTk.PhotoImage(resized_img)
            
            # キャンバスをクリアし、新しい画像を表示
            self.model_answer_canvas.delete("all")
            self.model_answer_canvas.create_image(0, 0, anchor=tk.NW, image=self.model_answer_tk_image)
            
            # キャンバスのスクロール領域を設定
            self.model_answer_canvas.config(scrollregion=(0, 0, new_width, new_height))
            
            # 拡大率表示を更新
            if hasattr(self, 'zoom_label'):
                self.zoom_label.config(text=f"表示倍率: {self.model_answer_zoom:.1f}x")
            
        except Exception as e:
            print(f"模範解答画像の更新エラー: {e}")
    
    def zoom_in_model_answer(self, event=None) -> None:
        """
        模範解答画像を拡大します。
        """
        self.model_answer_zoom *= 1.2  # 20%拡大
        self._update_model_answer_display()
    
    def zoom_out_model_answer(self, event=None) -> None:
        """
        模範解答画像を縮小します。
        """
        self.model_answer_zoom *= 0.8  # 20%縮小
        self._update_model_answer_display()
    
    def reset_model_answer_zoom(self, event=None) -> None:
        """
        模範解答画像の表示倍率を等倍(1.0)にリセットします。
        """
        self.model_answer_zoom = 1.0
        self._update_model_answer_display()
    
    def close_model_answer(self, event=None) -> None:
        """
        模範解答画像ウィンドウを閉じます。
        """
        if self.model_answer_window and self.model_answer_window.winfo_exists():
            self.model_answer_window.destroy()
            self.model_answer_window = None
            self.model_answer_tk_image = None  # メモリ解放
        
    def _on_model_answer_mousewheel(self, event) -> None:
        """
        模範解答画像ウィンドウ内でのマウスホイール操作
        """
        # キャンバスが存在し、有効かチェック
        if not (self.model_answer_canvas and self.model_answer_canvas.winfo_exists()):
            return "break"  # 破棄済みなら何もしない
            
        # マウスホイールの方向を判定
        if hasattr(event, "delta"):  # Windowsの場合
            delta = event.delta
            step = -1 if delta > 0 else 1
        else:  # Linuxの場合
            num = getattr(event, "num", 0)
            step = -1 if num == 4 else 1
            
        if event.state & 0x0004:  # Ctrlキーが押されている場合、拡大・縮小
            if step < 0:  # 上方向スクロール
                self.zoom_in_model_answer()
            else:  # 下方向スクロール
                self.zoom_out_model_answer()
        else:  # 通常はスクロール
            if event.state & 0x0001:  # Shiftキーが押されている場合、水平スクロール
                self.model_answer_canvas.xview_scroll(step, "units")
            else:  # 垂直スクロール
                self.model_answer_canvas.yview_scroll(step, "units")
                
        return "break"  # イベントの伝播を防止