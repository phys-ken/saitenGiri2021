"""
アプリケーションのメインウィンドウを管理するモジュール
"""
import os
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import pathlib
from typing import Dict, List, Optional, Callable

from ..utils.file_utils import resource_path, SETTING_DIR
from ..core.trimmer import ImageTrimmer
from ..core.grader import Grader
from ..core.marker import AnswerMarker
from .components.export_options_dialog import ExportOptionsDialog


class MainWindow:
    """アプリケーションのメインウィンドウ"""
    
    def __init__(self, root: tk.Tk):
        """
        メインウィンドウの初期化
        
        Args:
            root: tkinterのルートウィンドウ
        """
        self.root = root
        self.top_frame = None
        
        # ウィンドウの設定
        self.root.title("採点斬り")
        self.root.geometry("900x650")  # ウィンドウサイズを高めに設定して余裕を持たせる
        self.root.configure(bg='#f5f5f5')  # 背景色をライトグレーに変更
        
        # ボタン参照を保持
        self.buttons = {}
        self.status_bars = {}
        
        # ウィンドウの初期化
        self._init_top_frame()
        
        # 初期状態の確認と更新
        self._update_button_states()
        self._update_grading_status()

    def _init_top_frame(self) -> None:
        """トップ画面を初期化します"""
        # 既存のフレームがあれば削除
        if self.top_frame:
            self.top_frame.destroy()
        
        # トップフレームを作成
        self.top_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.top_frame.pack(fill=tk.BOTH, expand=True)
        
        # ヘッダーフレーム
        header_frame = tk.Frame(self.top_frame, bg="#4a86e8", height=70)
        header_frame.pack(fill=tk.X, pady=0)
        
        # アプリタイトル
        title_label = tk.Label(
            header_frame, 
            text="採点斬り 2021",
            font=("Meiryo UI", 24, "bold"),
            fg="white",
            bg="#4a86e8"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # サブタイトル
        subtitle_label = tk.Label(
            header_frame, 
            text="解答用紙の切り取り・採点・結果出力システム",
            font=("Meiryo UI", 12),
            fg="white",
            bg="#4a86e8"
        )
        subtitle_label.place(x=240, y=28)
        
        # メイン領域（グリッドレイアウト）
        main_frame = tk.Frame(self.top_frame, bg="#f5f5f5", padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側：手順カードフレーム
        workflow_frame = tk.LabelFrame(
            main_frame,
            text="手順",
            font=("Meiryo UI", 12, "bold"),
            bg="#f5f5f5",
            fg="#333333",
            padx=10,
            pady=10
        )
        workflow_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # 右側：情報・状態表示フレーム
        info_frame = tk.LabelFrame(
            main_frame,
            text="採点状況",
            font=("Meiryo UI", 12, "bold"),
            bg="#f5f5f5",
            fg="#333333",
            padx=10,
            pady=10,
            width=300  # 固定幅
        )
        info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        info_frame.grid_propagate(False)  # サイズ固定
        
        # グリッドの列の重みを設定（左側を拡大可能に）
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # ワークフローボタン群
        self._create_workflow_buttons(workflow_frame)
        
        # 採点状況表示
        self._create_status_display(info_frame)
        
        # フッターフレーム
        footer_frame = tk.Frame(self.top_frame, bg="#eeeeee", height=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # その他の機能へのリンク
        other_features_link = tk.Label(
            footer_frame,
            text="その他の機能",
            font=("Meiryo UI", 9, "underline"),
            fg="#0066cc",
            bg="#eeeeee",
            cursor="hand2"
        )
        other_features_link.pack(side=tk.RIGHT, padx=20, pady=5)
        other_features_link.bind("<Button-1>", self._show_other_features)

        # ヘルプへのリンク
        help_link = tk.Label(
            footer_frame,
            text="ヘルプ",
            font=("Meiryo UI", 9, "underline"),
            fg="#0066cc",
            bg="#eeeeee",
            cursor="hand2"
        )
        help_link.pack(side=tk.RIGHT, padx=10, pady=5)
        help_link.bind("<Button-1>", self._show_help)

    def _create_workflow_buttons(self, parent_frame: tk.Frame) -> None:
        """
        手順関連のボタンを作成します
        
        Args:
            parent_frame: ボタンを配置する親フレーム
        """
        # ボタンスタイル設定
        button_width = 22
        button_height = 2
        button_font = ("Meiryo UI", 11)
        button_padx = 5  # 横のパディングを小さく
        button_pady = 5  # 縦のパディングを小さく
        
        # ボタン配置用フレーム
        buttons_frame = tk.Frame(parent_frame, bg="#f5f5f5")
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # セクション1: 初期設定
        section1_frame = tk.LabelFrame(
            buttons_frame,
            text="1. 準備",
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=5
        )
        section1_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 初期設定ボタン
        init_button = tk.Button(
            section1_frame,
            text="初期設定をする",
            command=self.initialize_settings,
            width=button_width,
            height=button_height,
            font=button_font,
            bg="#e6f0ff",
            relief=tk.GROOVE
        )
        init_button.pack(padx=button_padx, pady=button_pady, anchor=tk.W)  # 左詰めに配置
        self.buttons["init"] = init_button
        
        # セクション2: 解答用紙処理
        section2_frame = tk.LabelFrame(
            buttons_frame,
            text="2. 解答用紙の斬り取り",
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=5
        )
        section2_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 切り取り定義ボタンの配置フレーム
        trim_buttons_frame = tk.Frame(section2_frame, bg="#f5f5f5")
        trim_buttons_frame.pack(fill=tk.X)
        
        # 切り取り定義ボタン
        trim_define_button = tk.Button(
            trim_buttons_frame,
            text="どこを斬るか決める",
            command=self.launch_trim_define,
            width=button_width,
            height=button_height,
            font=button_font,
            bg="#ffe6cc",
            relief=tk.GROOVE
        )
        trim_define_button.pack(side=tk.LEFT, padx=button_padx, pady=button_pady)
        self.buttons["trim_define"] = trim_define_button
        
        # 全員分の解答用紙切り取りボタン
        trim_all_button = tk.Button(
            trim_buttons_frame,
            text="全員の解答用紙を斬る",
            command=self.trim_all_papers,
            width=button_width,
            height=button_height,
            font=button_font,
            bg="#ffe6cc",
            relief=tk.GROOVE
        )
        trim_all_button.pack(side=tk.LEFT, padx=button_padx, pady=button_pady)
        self.buttons["trim_all"] = trim_all_button
        
        # セクション3: 採点処理
        section3_frame = tk.LabelFrame(
            buttons_frame,
            text="3. 採点",
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=5
        )
        section3_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 採点ボタン
        grade_button = tk.Button(
            section3_frame,
            text="斬った画像を採点する",
            command=self.launch_grading,
            width=button_width,
            height=button_height,
            font=button_font,
            bg="#e6ffe6",
            relief=tk.GROOVE
        )
        grade_button.pack(padx=button_padx, pady=button_pady, anchor=tk.W)  # 左詰めに配置
        self.buttons["grade"] = grade_button
        
        # セクション4: 結果出力
        section4_frame = tk.LabelFrame(
            buttons_frame,
            text="4. 結果出力",
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10,
            pady=5
        )
        section4_frame.pack(fill=tk.X)
        
        # 出力ボタン用フレーム
        output_buttons_frame = tk.Frame(section4_frame, bg="#f5f5f5")
        output_buttons_frame.pack(fill=tk.X)
        
        # Excel出力ボタン
        excel_button = tk.Button(
            output_buttons_frame,
            text="Excelに出力",
            command=self.export_excel,
            width=button_width,
            height=button_height,
            font=button_font,
            bg="#e6e6ff",
            relief=tk.GROOVE
        )
        excel_button.pack(side=tk.LEFT, padx=button_padx, pady=button_pady)
        self.buttons["excel"] = excel_button
        
        # 採点済み答案出力ボタン
        write_img_button = tk.Button(
            output_buttons_frame,
            text="採点済み答案を出力",
            command=self.write_graded_images,
            width=button_width,
            height=button_height,
            font=button_font,
            bg="#e6e6ff",
            relief=tk.GROOVE
        )
        write_img_button.pack(side=tk.LEFT, padx=button_padx, pady=button_pady)
        self.buttons["write_img"] = write_img_button
        
        # アプリ終了ボタン
        exit_button = tk.Button(
            buttons_frame,
            text="アプリを閉じる",
            command=self.exit_app,
            width=15,
            height=1,
            font=("Meiryo UI", 9),
            bg="#f0f0f0"
        )
        exit_button.pack(side=tk.RIGHT, padx=10, pady=(8, 0))
        self.buttons["exit"] = exit_button

    def _create_status_display(self, parent_frame: tk.Frame) -> None:
        """
        採点状況表示領域を作成します
        
        Args:
            parent_frame: 状態表示を配置する親フレーム
        """
        # 状態表示フレーム
        status_content_frame = tk.Frame(parent_frame, bg="#f5f5f5")
        status_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 準備状態表示
        prep_status_label = tk.Label(
            status_content_frame,
            text="準備状態:",
            font=("Meiryo UI", 11, "bold"),
            bg="#f5f5f5",
            anchor="w"
        )
        prep_status_label.pack(fill=tk.X, pady=(0, 5))
        
        # 設定フォルダ状態
        setting_status_frame = tk.Frame(status_content_frame, bg="#f5f5f5")
        setting_status_frame.pack(fill=tk.X, pady=2)
        
        setting_label = tk.Label(
            setting_status_frame,
            text="設定フォルダ:",
            font=("Meiryo UI", 9),
            width=15,
            anchor="w",
            bg="#f5f5f5"
        )
        setting_label.pack(side=tk.LEFT)
        
        self.setting_status = tk.Label(
            setting_status_frame,
            text="未作成",
            font=("Meiryo UI", 9),
            fg="red",
            bg="#f5f5f5"
        )
        self.setting_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bars["setting"] = self.setting_status
        
        # 入力ファイル状態
        input_status_frame = tk.Frame(status_content_frame, bg="#f5f5f5")
        input_status_frame.pack(fill=tk.X, pady=2)
        
        input_label = tk.Label(
            input_status_frame,
            text="入力ファイル:",
            font=("Meiryo UI", 9),
            width=15,
            anchor="w",
            bg="#f5f5f5"
        )
        input_label.pack(side=tk.LEFT)
        
        self.input_status = tk.Label(
            input_status_frame,
            text="なし",
            font=("Meiryo UI", 9),
            fg="red",
            bg="#f5f5f5"
        )
        self.input_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bars["input"] = self.input_status
        
        # 採点データ状態
        trim_status_frame = tk.Frame(status_content_frame, bg="#f5f5f5")
        trim_status_frame.pack(fill=tk.X, pady=2)
        
        trim_label = tk.Label(
            trim_status_frame,
            text="切り取り定義:",
            font=("Meiryo UI", 9),
            width=15,
            anchor="w",
            bg="#f5f5f5"
        )
        trim_label.pack(side=tk.LEFT)
        
        self.trim_status = tk.Label(
            trim_status_frame,
            text="未定義",
            font=("Meiryo UI", 9),
            fg="red",
            bg="#f5f5f5"
        )
        self.trim_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bars["trim"] = self.trim_status
        
        # セパレータ
        separator = ttk.Separator(status_content_frame, orient="horizontal")
        separator.pack(fill=tk.X, pady=8)
        
        # 採点状況表示ラベル
        grading_status_label = tk.Label(
            status_content_frame,
            text="採点進捗:",
            font=("Meiryo UI", 11, "bold"),
            bg="#f5f5f5",
            anchor="w"
        )
        grading_status_label.pack(fill=tk.X, pady=(0, 8))
        
        # 採点進捗表示フレーム
        progress_frame = tk.Frame(status_content_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=5)
        
        # 採点済み/未採点の割合を表示する進捗バー
        self.progress_frame = tk.Frame(progress_frame, bg="#f5f5f5", height=25)  # 高さを小さめに
        self.progress_frame.pack(fill=tk.X)
        
        # 詳細情報表示エリア
        details_frame = tk.Frame(status_content_frame, bg="#f5f5f5")
        details_frame.pack(fill=tk.X, pady=5)
        
        # 問題数
        self.question_count_var = tk.StringVar(value="問題数: 0")
        question_count_label = tk.Label(
            details_frame,
            textvariable=self.question_count_var,
            font=("Meiryo UI", 9),
            bg="#f5f5f5",
            anchor="w"
        )
        question_count_label.pack(fill=tk.X, pady=2)
        
        # 採点済み
        self.graded_count_var = tk.StringVar(value="採点済み: 0")
        graded_count_label = tk.Label(
            details_frame,
            textvariable=self.graded_count_var,
            font=("Meiryo UI", 9),
            bg="#f5f5f5",
            anchor="w"
        )
        graded_count_label.pack(fill=tk.X, pady=2)
        
        # 未採点
        self.ungraded_count_var = tk.StringVar(value="未採点: 0")
        ungraded_count_label = tk.Label(
            details_frame,
            textvariable=self.ungraded_count_var,
            font=("Meiryo UI", 9),
            bg="#f5f5f5",
            anchor="w"
        )
        ungraded_count_label.pack(fill=tk.X, pady=2)
        
        # 採点率
        self.grade_rate_var = tk.StringVar(value="採点率: 0%")
        grade_rate_label = tk.Label(
            details_frame,
            textvariable=self.grade_rate_var,
            font=("Meiryo UI", 9, "bold"),
            bg="#f5f5f5",
            anchor="w"
        )
        grade_rate_label.pack(fill=tk.X, pady=2)
        
        # 更新ボタン
        refresh_button = tk.Button(
            status_content_frame,
            text="状態を更新",
            command=self._update_all_status,
            width=15,
            height=1,
            font=("Meiryo UI", 9),
            bg="#f0f0f0"
        )
        refresh_button.pack(side=tk.RIGHT, pady=(8, 0))

    def _update_button_states(self) -> None:
        """ボタンの有効/無効状態を設定フォルダの状態に基づいて更新します"""
        setting_exists = SETTING_DIR.exists()
        
        # 初期設定後のみ有効になるボタン
        dependent_buttons = ["trim_define", "trim_all", "grade", "excel", "write_img"]
        
        for button_id in dependent_buttons:
            if button_id in self.buttons:
                if setting_exists:
                    self.buttons[button_id].config(state=tk.NORMAL)
                else:
                    self.buttons[button_id].config(state=tk.DISABLED)

    def _update_grading_status(self) -> None:
        """採点状況の表示を更新します"""
        import datetime
        
        # 設定フォルダがなければ状態を「未作成」に
        if not SETTING_DIR.exists():
            self.status_bars["setting"].config(text="未作成", fg="red")
            # 進捗バーを空にする
            for widget in self.progress_frame.winfo_children():
                widget.destroy()
            return
        else:
            self.status_bars["setting"].config(text="作成済み", fg="green")
        
        # 入力ファイルの確認
        input_dir = SETTING_DIR / "input"
        if input_dir.exists():
            from ..utils.file_utils import get_sorted_image_files
            input_files = get_sorted_image_files(str(input_dir / "*"))
            if input_files:
                self.status_bars["input"].config(text=f"{len(input_files)}件", fg="green")
            else:
                self.status_bars["input"].config(text="ファイルなし", fg="red")
        else:
            self.status_bars["input"].config(text="フォルダなし", fg="red")
        
        # 切り取り定義の確認
        trim_file = SETTING_DIR / "trimData.csv"
        if trim_file.exists():
            import csv
            try:
                with open(trim_file, "r") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    if len(rows) > 1:  # ヘッダー行を除く
                        self.status_bars["trim"].config(text=f"{len(rows)-1}問定義済み", fg="green")
                    else:
                        self.status_bars["trim"].config(text="定義なし", fg="red")
            except:
                self.status_bars["trim"].config(text="読み取りエラー", fg="red")
        else:
            self.status_bars["trim"].config(text="未定義", fg="red")
        
        # 採点状況の計算
        output_dir = SETTING_DIR / "output"
        if not output_dir.exists():
            # 進捗バーを空にする
            for widget in self.progress_frame.winfo_children():
                widget.destroy()
            
            # カウンタを0に設定
            self.question_count_var.set("問題数: 0")
            self.graded_count_var.set("採点済み: 0")
            self.ungraded_count_var.set("未採点: 0")
            self.grade_rate_var.set("採点率: 0%")
            return
        
        # 問題フォルダを探す
        question_dirs = []
        total_graded = 0
        total_ungraded = 0
        
        try:
            for item in output_dir.iterdir():
                if item.is_dir() and item.name.startswith("Q_"):
                    question_dirs.append(item)
                    
                    # 各問題の採点状況を確認
                    graded_files = 0
                    ungraded_files = 0
                    
                    # 採点済みファイル(数字フォルダにあるファイル)
                    for score_dir in item.iterdir():
                        if score_dir.is_dir() and score_dir.name.isdigit():
                            graded_files += len([f for f in score_dir.iterdir() if f.is_file()])
                    
                    # 未採点ファイル(問題フォルダの直下にあるファイル)
                    ungraded_files = len([f for f in item.iterdir() if f.is_file()])
                    
                    total_graded += graded_files
                    total_ungraded += ungraded_files
            
            # 進捗バーの描画
            for widget in self.progress_frame.winfo_children():
                widget.destroy()
            
            total = total_graded + total_ungraded
            if total > 0:
                graded_ratio = total_graded / total
                
                # 採点済みバー
                if graded_ratio > 0:
                    graded_bar = tk.Frame(self.progress_frame, bg="#4CAF50", height=20)
                    graded_bar.place(relx=0, rely=0, relwidth=graded_ratio, relheight=1)
                
                # 未採点バー
                if graded_ratio < 1:
                    ungraded_bar = tk.Frame(self.progress_frame, bg="#f0f0f0", height=20)
                    ungraded_bar.place(relx=graded_ratio, rely=0, relwidth=1-graded_ratio, relheight=1)
                
                # パーセント表示
                percent_label = tk.Label(
                    self.progress_frame, 
                    text=f"{int(graded_ratio * 100)}%", 
                    bg="#f5f5f5" if graded_ratio < 0.5 else "#4CAF50",
                    fg="black" if graded_ratio < 0.5 else "white",
                    font=("Meiryo UI", 9, "bold")
                )
                percent_label.place(relx=0.5, rely=0.5, anchor="center")
            
                # 情報更新
                self.question_count_var.set(f"問題数: {len(question_dirs)}")
                self.graded_count_var.set(f"採点済み: {total_graded}件")
                self.ungraded_count_var.set(f"未採点: {total_ungraded}件")
                self.grade_rate_var.set(f"採点率: {int(graded_ratio * 100)}%")
            else:
                # データがない場合
                no_data_label = tk.Label(
                    self.progress_frame,
                    text="採点データがありません",
                    font=("Meiryo UI", 9),
                    bg="#f0f0f0"
                )
                no_data_label.pack(fill=tk.BOTH, expand=True)
                
                # カウンタを0に設定
                self.question_count_var.set(f"問題数: {len(question_dirs)}")
                self.graded_count_var.set("採点済み: 0件")
                self.ungraded_count_var.set("未採点: 0件")
                self.grade_rate_var.set("採点率: 0%")
        
        except Exception as e:
            print(f"採点状況の更新エラー: {e}")
            error_label = tk.Label(
                self.progress_frame,
                text="データ読み込みエラー",
                font=("Meiryo UI", 9),
                bg="#ffcccc"
            )
            error_label.pack(fill=tk.BOTH, expand=True)

    def _update_all_status(self) -> None:
        """すべての状態表示を更新します"""
        self._update_button_states()
        self._update_grading_status()
        
    def _show_other_features(self, event=None) -> None:
        """その他の機能画面を表示します"""
        other_features_window = OtherFeaturesWindow(self.root)
        
    def _show_help(self, event=None) -> None:
        """ヘルプ情報を表示します"""
        self.show_info()
    
    def show_info(self) -> None:
        """アプリケーションの情報を表示します"""
        messagebox.showinfo(
            "ヘルプ", 
            "採点斬りへようこそ！\n\n"
            "このアプリでは解答用紙の斬り取り・採点・結果出力が行えます。\n"
            "操作手順は以下の通りです：\n\n"
            "1. 「初期設定をする」で必要なフォルダを作成\n"
            "2. 「setting/input」フォルダに解答用紙画像を配置\n"
            "3. 「どこを斬るか決める」で斬り取り範囲を設定\n"
            "4. 「全員の解答用紙を斬る」で画像を問題ごとに斬り取り\n"
            "5. 「斬った画像を採点する」で採点作業\n"
            "6. 「Excelに出力」または「採点済み答案を出力」で結果の保存\n\n"
            "詳しいヘルプはこちら：\n"
            "https://github.com/phys-ken/saitenGiri2021"
        )
    
    def initialize_settings(self) -> None:
        """初期設定を行います"""
        if not SETTING_DIR.exists():
            ret = messagebox.askyesno(
                '初回設定', 
                '解答用紙の配置を行うため、設定用フォルダーを作成します。よろしいですか？'
            )
            if ret:
                from ..utils.file_utils import ensure_directories, initialize_csv_file
                ensure_directories()
                initialize_csv_file()
                messagebox.showinfo(
                    '初期設定完了', 
                    '解答用紙を「setting/input」フォルダーにJPEGまたはPNG形式で配置してください。'
                )
                # 状態を更新
                self._update_all_status()
            else:
                messagebox.showinfo('設定キャンセル', 'フォルダーの作成を中止しました。')
        else:
            messagebox.showinfo(
                '確認', 
                '初期設定は完了しています。解答用紙を「setting/input」フォルダーに配置し、斬り取りを開始してください。'
            )
    
    def launch_trim_define(self) -> None:
        """切り取り領域定義画面を起動します"""
        # 初期設定確認
        if not SETTING_DIR.exists():
            messagebox.showerror(
                '設定エラー', 
                '初期設定が完了していません。まず「初期設定をする」ボタンを押してください。'
            )
            return
        
        # ファイルの存在チェック
        from ..utils.file_utils import get_sorted_image_files
        files = get_sorted_image_files(str(SETTING_DIR / "input" / "*"))
        
        if not files:
            messagebox.showerror(
                '入力エラー', 
                '「setting/input」に解答用紙の画像が見つかりません。画像を追加してから再度実行してください。'
            )
            return
        
        # 切り取り定義画面を表示
        from .components.trim_definer import TrimDefinerWindow
        TrimDefinerWindow(self.root, files[0])
        
        # 戻ってきたら状態を更新
        self._update_all_status()
    
    def trim_all_papers(self) -> None:
        """すべての解答用紙を切り取ります"""
        # 初期設定確認
        if not SETTING_DIR.exists():
            messagebox.showerror(
                '設定エラー', 
                '初期設定が完了していません。まず「初期設定をする」ボタンを押してください。'
            )
            return
            
        # 入力ファイルの確認
        input_dir = SETTING_DIR / "input"
        if not input_dir.exists() or not any(input_dir.iterdir()):
            messagebox.showerror(
                '入力エラー', 
                '「setting/input」フォルダにファイルが見つかりません。'
                'まず解答用紙の画像を配置してください。'
            )
            return
            
        # 切り取り定義の確認
        trim_file = SETTING_DIR / "trimData.csv"
        if not trim_file.exists():
            messagebox.showerror(
                '設定エラー', 
                '斬り取り定義ファイルが見つかりません。'
                'まず「どこを斬るか決める」ボタンから斬り取り範囲を設定してください。'
            )
            return
        
        ret = messagebox.askyesno(
            '確認', 
            '全員分の解答用紙を斬り取ります。\n'
            '処理を続行しますか？\n\n'
            '①大量の画像では時間がかかる場合があります。\n'
            '②「setting/input」の画像はそのまま保持されます。\n'
            '③既存の「setting/output」は上書きされます。'
        )
        
        if ret:
            trimmer = ImageTrimmer(input_dir=str(SETTING_DIR / "input"), output_dir=str(SETTING_DIR / "output"))
            success = trimmer.trim_all_images()
            
            if success:
                messagebox.showinfo('完了', '全員分の解答用紙の斬り取りが完了しました。')
                # 状態を更新
                self._update_all_status()
            else:
                messagebox.showerror('エラー', '斬り取り処理中にエラーが発生しました。')

    # その他のメソッドは変更なし
    def launch_grading(self) -> None:
        """採点画面を起動します"""
        # 初期設定確認
        if not SETTING_DIR.exists():
            messagebox.showerror(
                '設定エラー', 
                '初期設定が完了していません。まず「初期設定をする」ボタンを押してください。'
            )
            return
            
        # 出力フォルダの確認
        output_dir = SETTING_DIR / "output"
        if not output_dir.exists() or not any(output_dir.iterdir()):
            messagebox.showerror(
                '入力エラー', 
                '「setting/output」フォルダにファイルが見つかりません。'
                'まず「全員の解答用紙を斬る」ボタンから画像を切り取ってください。'
            )
            return
            
        from .components.grading_selector import GradingSelectorWindow
        from .components.grading_window import GradingWindow
        from .components.grid_grading_window import GridGradingWindow
        
        # 問題選択時のコールバック関数
        def on_question_selected(question_id, grade_mode):
            if grade_mode == "grid":
                # 一覧採点モード
                GridGradingWindow(self.root, question_id)
            else:
                # 1枚ずつ採点モード
                GradingWindow(self.root, question_id)
            
            # 採点画面から戻ったら状態を更新
            self._update_all_status()
            
        GradingSelectorWindow(self.root, on_question_selected)
    
    def export_excel(self) -> None:
        """採点結果をExcelに出力します"""
        # 初期設定確認
        if not SETTING_DIR.exists():
            messagebox.showerror(
                '設定エラー', 
                '初期設定が完了していません。まず「初期設定をする」ボタンを押してください。'
            )
            return
            
        # 出力フォルダの確認
        output_dir = SETTING_DIR / "output"
        if not output_dir.exists() or not any(output_dir.iterdir()):
            messagebox.showerror(
                '入力エラー', 
                '「setting/output」フォルダにファイルが見つかりません。'
                '先に採点を行ってください。'
            )
            return
            
        try:
            grader = Grader(output_dir=str(SETTING_DIR / "output"), excel_path=str(SETTING_DIR / "saiten.xlsx"))
            success = grader.create_excel_report()
            
            if success:
                messagebox.showinfo('完了', '「setting/saiten.xlsx」に採点結果を出力しました。')
            else:
                messagebox.showerror('エラー', 'Excelへの出力に失敗しました。')
        except Exception as e:
            messagebox.showerror('エラー', f'処理中にエラーが発生しました。{e}')
    
    def write_graded_images(self) -> None:
        """採点結果を解答用紙に書き込みます"""
        # 初期設定確認
        if not SETTING_DIR.exists():
            messagebox.showerror(
                '設定エラー', 
                '初期設定が完了していません。まず「初期設定をする」ボタンを押してください。'
            )
            return
            
        # 出力フォルダの確認
        output_dir = SETTING_DIR / "output"
        if not output_dir.exists() or not any(output_dir.iterdir()):
            messagebox.showerror(
                '入力エラー', 
                '「setting/output」フォルダにファイルが見つかりません。'
                '先に採点を行ってください。'
            )
            return
            
        try:
            # 出力オプション選択ダイアログを表示
            def on_options_selected(options):
                self._process_graded_images(options)
            
            ExportOptionsDialog(self.root, on_options_selected)
                
        except Exception as e:
            messagebox.showerror('エラー', f'処理中にエラーが発生しました。{e}')
    
    def _process_graded_images(self, options) -> None:
        """
        選択されたオプションに基づいて採点済み画像を出力します
        
        Args:
            options: 出力オプション設定
        """
        try:
            # 出力フォルダをexportに変更
            export_dir = str(SETTING_DIR / "export")
            
            # 表示するオプションをリスト化（UI表示用）
            options_text = []
            if options.get('question_scores', False):
                options_text.append("・設問ごとの得点")
            if options.get('total_score', False):
                options_text.append("・合計得点")
            if options.get('symbols', False):
                options_text.append("・〇×△マーク")
                
                # 透過度情報も追加
                transparency = options.get('transparency', 50)
                options_text.append(f"  - 透過度: {transparency}%")
                
                # 得点表示位置
                score_position = options.get('score_position', 'right')
                position_text = '右端'
                if score_position == 'center':
                    position_text = 'マークの横（中央）'
                elif score_position == 'left':
                    position_text = '左端'
                options_text.append(f"  - 得点表示位置: {position_text}")
                
                # 得点表示色
                score_color = options.get('score_color', 'red')
                color_text = '赤'
                if score_color == 'same':
                    color_text = 'マークと同じ'
                elif score_color == 'black':
                    color_text = '黒'
                options_text.append(f"  - 得点表示色: {color_text}")
            
            options_str = "\n".join(options_text)
            ret = messagebox.askyesno(
                '採点済み答案の出力',
                f'以下の内容を含む採点済み答案を出力します：\n\n{options_str}\n\n'
                f'出力先: setting/export\n\n'
                '既存のファイルは上書きされます。続行しますか？'
            )
            
            if not ret:
                return
            
            # マーカーインスタンス生成
            marker = AnswerMarker(
                input_dir=str(SETTING_DIR / "input"), 
                output_dir=export_dir, 
                grading_data_path=str(SETTING_DIR / "trimData.csv")
            )
            
            # 選択されたオプションに基づいて処理
            if options.get('symbols', False) and not self._check_opencv_available():
                # OpenCVが必要な場合はチェック
                return
            
            success = marker.mark_all_answer_sheets(options)
            
            if success:
                messagebox.showinfo(
                    '完了', 
                    '採点結果を反映した解答用紙を作成しました。\n'
                    '保存先: setting/export'
                )
            else:
                messagebox.showerror('エラー', '採点済み画像の作成に失敗しました。')
        except Exception as e:
            messagebox.showerror('エラー', f'処理中にエラーが発生しました。{e}')
    
    def _check_opencv_available(self) -> bool:
        """OpenCVがインストールされているか確認"""
        try:
            import cv2
            import numpy as np
            return True
        except ImportError:
            messagebox.showerror(
                '必要なライブラリがありません', 
                '〇×△マーク機能には OpenCV(cv2) ライブラリが必要です。\n'
                'pip install opencv-python コマンドでインストールしてください。'
            )
            return False
    
    def exit_app(self) -> None:
        """アプリケーションを終了します"""
        self.root.destroy()
        
    def run(self) -> None:
        """アプリケーションを実行します"""
        self.root.mainloop()


class OtherFeaturesWindow:
    """「その他の機能」ウィンドウ"""
    
    def __init__(self, parent: tk.Tk):
        """
        初期化処理
        
        Args:
            parent: 親ウィンドウ
        """
        self.parent = parent
        
        # ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("その他の機能")
        self.window.geometry("500x350")
        self.window.configure(bg="#f5f5f5")
        
        # モーダルウィンドウとして表示
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # ウィンドウの中央配置
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.parent.winfo_width() - width) // 2 + self.parent.winfo_x()
        y = (self.parent.winfo_height() - height) // 2 + self.parent.winfo_y()
        self.window.geometry(f"+{x}+{y}")
        
        # UI要素の作成
        self._create_ui()
        
    def _create_ui(self) -> None:
        """UI要素を作成します"""
        # ヘッダー
        header_label = tk.Label(
            self.window,
            text="その他の機能",
            font=("Meiryo UI", 16, "bold"),
            bg="#f5f5f5",
            padx=20,
            pady=10
        )
        header_label.pack(fill=tk.X)
        
        # 説明
        description = tk.Label(
            self.window,
            text="このセクションでは追加の機能にアクセスできます。",
            font=("Meiryo UI", 10),
            bg="#f5f5f5",
            wraplength=450
        )
        description.pack(pady=(0, 10))
        
        # 機能ボタンのコンテナフレーム
        buttons_frame = tk.Frame(self.window, bg="#f5f5f5")
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 模範解答斬り取りボタン
        trim_answers_button = tk.Button(
            buttons_frame,
            text="模範解答のみ斬る",
            command=self._trim_sample_answers,
            width=25,
            height=2,
            font=("Meiryo UI", 11),
            bg="#ffe6cc"
        )
        trim_answers_button.pack(pady=10)
        
        # 説明テキスト
        sample_desc = tk.Label(
            buttons_frame,
            text="setting/answerdata フォルダに配置した模範解答画像のみを\n"
                 "設定済みの領域定義に従って斬ります。",
            font=("Meiryo UI", 9),
            bg="#f5f5f5",
            justify=tk.LEFT
        )
        sample_desc.pack(pady=5)
        
        # フッターフレーム
        footer_frame = tk.Frame(self.window, bg="#f5f5f5", padx=20, pady=20)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 閉じるボタン
        close_button = tk.Button(
            footer_frame,
            text="閉じる",
            command=self.window.destroy,
            width=15,
            height=1
        )
        close_button.pack(side=tk.RIGHT)
        
    def _trim_sample_answers(self) -> None:
        """模範解答のみを斬る機能"""
        from ..core.trimmer import ImageTrimmer
        from ..utils.file_utils import SETTING_DIR, ANSWER_DATA_DIR
        import os
        from tkinter import messagebox
        
        # 初期設定確認
        if not SETTING_DIR.exists():
            messagebox.showerror(
                '設定エラー', 
                '初期設定が完了していません。まず「初期設定をする」ボタンを押してください。'
            )
            return
            
        # 切り取り定義の確認
        trim_file = SETTING_DIR / "trimData.csv"
        if not trim_file.exists():
            messagebox.showerror(
                '設定エラー', 
                '斬り取り定義ファイルが見つかりません。'
                'まず「どこを斬るか決める」ボタンから斬り取り範囲を設定してください。'
            )
            return
            
        # 模範解答画像の確認
        if not ANSWER_DATA_DIR.exists() or not any(ANSWER_DATA_DIR.iterdir()):
            messagebox.showerror(
                '入力エラー', 
                '「setting/answerdata」フォルダにファイルが見つかりません。'
                'まず模範解答用の画像を配置してください。'
            )
            return
            
        # 確認ダイアログ
        ret = messagebox.askyesno(
            '確認', 
            '模範解答画像を斬り取ります。\n'
            '処理を続行しますか？\n\n'
            '既存の斬り取り結果は上書きされます。'
        )
        
        if ret:
            # トリマーインスタンス作成
            trimmer = ImageTrimmer(answer_dir=str(ANSWER_DATA_DIR))
            
            # 模範解答のみ斬る
            success = trimmer.trim_sample_answers()
            
            if success:
                messagebox.showinfo(
                    '完了', 
                    '模範解答画像の斬り取りが完了しました。\n'
                    '「setting/answerdata/output」内に保存されました。'
                )
            else:
                messagebox.showerror(
                    'エラー', 
                    '斬り取り処理中にエラーが発生しました。'
                )