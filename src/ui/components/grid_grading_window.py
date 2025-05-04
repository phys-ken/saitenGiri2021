"""
タイルビュー(グリッド)形式で採点を行うウィンドウクラス
"""
import os
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from typing import List, Dict, Optional, Any, Tuple, Callable
import time

from ...core.grader import Grader
from ...utils.image_utils import (
    resize_image_by_scale, create_thumbnail_for_grid, 
    calculate_whiteness, get_image_with_score_overlay
)
from ...utils.file_utils import SETTING_DIR, get_sorted_image_files


class GridGradingWindow:
    """グリッド表示（タイルビュー）採点ウィンドウ"""
    
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
        
        # ヘッダー(コントロールフレーム)
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # ソート方法選択
        sort_label = tk.Label(self.control_frame, text="並び順:")
        sort_label.pack(side=tk.LEFT, padx=5)
        
        self.sort_var = tk.StringVar(value="filename")
        sort_options = [
            ("ファイル名順", "filename"),
            ("点数順(昇順)", "score_asc"),
            ("点数順(降順)", "score_desc"),
            ("白さ順", "whiteness"),
        ]
        
        self.sort_menu = ttk.Combobox(
            self.control_frame, 
            textvariable=self.sort_var, 
            values=[opt[0] for opt in sort_options],
            state="readonly",
            width=15
        )
        self.sort_menu.current(0)
        self.sort_menu.pack(side=tk.LEFT, padx=5)
        self.sort_menu.bind("<<ComboboxSelected>>", self._on_sort_change)
        
        # 画像サイズスライダー
        size_label = tk.Label(self.control_frame, text="表示サイズ:")
        size_label.pack(side=tk.LEFT, padx=10)
        
        self.size_var = tk.DoubleVar(value=self.thumbnail_size)
        self.size_slider = ttk.Scale(
            self.control_frame,
            from_=50,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.size_var,
            length=200
        )
        self.size_slider.pack(side=tk.LEFT, padx=5)
        self.size_slider.bind("<ButtonRelease-1>", self._on_size_change)
        
        # 現在のサイズ表示ラベル
        self.size_value_label = tk.Label(self.control_frame, text=f"{self.thumbnail_size}px")
        self.size_value_label.pack(side=tk.LEFT, padx=5)
        
        # 列数設定
        col_label = tk.Label(self.control_frame, text="列数:")
        col_label.pack(side=tk.LEFT, padx=10)
        
        self.col_var = tk.IntVar(value=self.columns)
        self.col_slider = ttk.Scale(
            self.control_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.col_var,
            length=150
        )
        self.col_slider.pack(side=tk.LEFT, padx=5)
        self.col_slider.bind("<ButtonRelease-1>", self._on_column_change)
        
        # 現在の列数表示ラベル
        self.col_value_label = tk.Label(self.control_frame, text=f"{self.columns}列")
        self.col_value_label.pack(side=tk.LEFT, padx=5)
        
        # 採点ボタン
        self.grade_button = tk.Button(
            self.control_frame,
            text="採点実行",
            command=self.execute_grading,
            width=10
        )
        self.grade_button.pack(side=tk.RIGHT, padx=10)
        
        # 戻るボタン
        self.exit_button = tk.Button(
            self.control_frame,
            text="戻る",
            command=self.exit_grading,
            width=8
        )
        self.exit_button.pack(side=tk.RIGHT)
        
        # 選択情報表示ラベル
        self.selection_info = tk.Label(
            self.control_frame,
            text="選択: 0 件",
            width=15
        )
        self.selection_info.pack(side=tk.RIGHT, padx=10)
        
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
        for i in range(10):
            score_btn = tk.Button(
                self.score_buttons_frame,
                text=str(i),
                width=3,
                height=2,
                command=lambda score=str(i): self._set_score_to_selected(score)
            )
            score_btn.pack(side=tk.LEFT, padx=2)
        
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
        """グリッド表示を更新します"""
        start_time = time.time()
        
        # グリッドフレームの子ウィジェットをすべて削除
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        # tk_imagesを初期化（古い参照を削除）
        self.tk_images = {}
        
        # 指定されたソート方法でファイルをソート
        sorted_files = self._get_sorted_files()
        
        # グリッド表示用のフレームを設定
        self.grid_frame.config(bg="white")
        
        # 現在の列数とサムネイルサイズを取得
        cols = self.columns
        thumb_size = int(self.size_var.get())
        
        # グリッドに画像を追加
        for i, file_path in enumerate(sorted_files):
            # グリッド位置を計算
            row = i // cols
            col = i % cols
            
            # 画像フレーム
            item_frame = tk.Frame(
                self.grid_frame,
                width=thumb_size,
                height=thumb_size + 30,  # 画像 + ラベル用の高さ
                bg="white"
            )
            item_frame.grid(row=row, column=col, padx=5, pady=5)
            item_frame.pack_propagate(False)  # サイズを固定
            
            # サムネイルの作成
            thumbnail = self._get_thumbnail(file_path, thumb_size)
            
            # 画像が採点済みかどうかをチェック
            score = self._get_file_score(file_path)
            if score:
                # 採点済みの場合、スコアをオーバーレイ表示
                thumbnail = get_image_with_score_overlay(thumbnail, score)
            
            # PhotoImageの作成（tkinterで表示するため）
            photo = ImageTk.PhotoImage(thumbnail)
            self.tk_images[file_path] = photo
            
            # 画像ラベル（選択状態に応じた背景色）
            bg_color = "#add8e6" if file_path in self.selected_items else "white"
            image_label = tk.Label(
                item_frame,
                image=photo,
                bg=bg_color
            )
            image_label.pack(fill=tk.BOTH, expand=True)
            
            # ファイル名ラベル
            filename = os.path.basename(file_path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            
            file_label = tk.Label(
                item_frame,
                text=filename,
                bg="white",
                font=("", 8)
            )
            file_label.pack(side=tk.BOTTOM, fill=tk.X)
            
            # 選択イベントのバインド
            image_label.bind("<Button-1>", lambda e, path=file_path: self._on_item_click(e, path))
            file_label.bind("<Button-1>", lambda e, path=file_path: self._on_item_click(e, path))
        
        # グリッドフレームのサイズを更新
        self.grid_frame.update_idletasks()
        
        # キャンバスのスクロール領域を更新
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        end_time = time.time()
        print(f"グリッド表示の更新: {end_time - start_time:.3f}秒")
    
    def _get_sorted_files(self) -> List[str]:
        """現在のソートモードに従ってファイルをソートします"""
        all_files = self.image_files.copy()
        for files in self.graded_files.values():
            all_files.extend(files)
        
        if self.sort_mode == "filename":
            # ファイル名順
            return sorted(all_files, key=lambda x: os.path.basename(x))
        
        elif self.sort_mode == "whiteness":
            # 白さ順（白いものが先）
            return sorted(all_files, key=lambda x: self.whiteness_dict.get(x, 0.0), reverse=True)
        
        elif self.sort_mode.startswith("score"):
            # 点数順
            def get_numeric_score(path):
                score = self._get_file_score(path)
                if score == "skip":
                    return -1  # skipは最低点として扱う
                try:
                    return int(score) if score else 0
                except:
                    return 0
            
            reverse = self.sort_mode == "score_desc"
            return sorted(all_files, key=get_numeric_score, reverse=reverse)
        
        # デフォルト
        return all_files
    
    def _get_file_score(self, file_path: str) -> str:
        """ファイルの点数を取得します"""
        # すでに採点データがある場合
        if file_path in self.score_dict:
            return self.score_dict[file_path]
        
        # 採点済みフォルダにあるファイルの場合
        for score, files in self.graded_files.items():
            if file_path in files:
                return score
        
        return ""  # 未採点
    
    def _on_item_click(self, event, file_path: str) -> None:
        """画像アイテムがクリックされた時の処理"""
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
    
    def _on_sort_change(self, event=None) -> None:
        """ソート方法が変更された時の処理"""
        selected_text = self.sort_menu.get()
        
        if selected_text == "ファイル名順":
            self.sort_mode = "filename"
        elif selected_text == "点数順(昇順)":
            self.sort_mode = "score_asc"
        elif selected_text == "点数順(降順)":
            self.sort_mode = "score_desc"
        elif selected_text == "白さ順":
            self.sort_mode = "whiteness"
        else:
            self.sort_mode = "filename"  # デフォルト
        
        self._update_grid_view()
    
    def _on_size_change(self, event=None) -> None:
        """サムネイルサイズが変更された時の処理"""
        new_size = int(self.size_var.get())
        if new_size != self.thumbnail_size:
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
    
    def _on_canvas_configure(self, event=None) -> None:
        """キャンバスがリサイズされた時の処理"""
        # グリッドフレームの幅をキャンバスの幅に合わせる
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_key_press(self, event) -> None:
        """キー入力に対する処理"""
        key = event.char
        
        # 数字キーの場合は採点
        if key in self.allowed_scores:
            self._set_score_to_selected(key)
        
        # スペースキーの場合はskip
        elif key == " ":
            self._set_score_to_selected("skip")
    
    def _set_score_to_selected(self, score: str) -> None:
        """選択された画像に点数を設定します"""
        if not self.selected_items:
            messagebox.showinfo("情報", "採点する画像を選択してください。")
            return
        
        # 選択されたすべての画像に点数を設定
        for file_path in self.selected_items:
            self.score_dict[file_path] = score
            print(f"スコア設定: {os.path.basename(file_path)} → {score}")
        
        # グリッド表示を更新
        self._update_grid_view()
    
    def _select_all(self) -> None:
        """すべての画像を選択します"""
        all_files = self._get_sorted_files()
        self.selected_items = set(all_files)
        self.selection_info.config(text=f"選択: {len(self.selected_items)} 件")
        self._update_grid_view()
    
    def _deselect_all(self) -> None:
        """すべての選択を解除します"""
        self.selected_items = set()
        self.selection_info.config(text=f"選択: 0 件")
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
        
        self.window.destroy()
    
    def on_closing(self) -> None:
        """ウィンドウを閉じる際の処理"""
        self.exit_grading()