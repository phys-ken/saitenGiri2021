"""
採点済み答案の出力オプションを選択するダイアログ
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Callable, Union, Any


class ExportOptionsDialog:
    """
    採点済み答案の出力オプションを選択するダイアログウィンドウ
    
    このダイアログでは、以下のオプションを選択できます：
    - 設問ごとの得点を表示する
    - 合計得点を表示する
    - 〇×△マークを表示する
    - マークの透過度設定
    - 得点表示位置設定
    - 得点表示色設定
    """
    
    def __init__(self, parent: tk.Tk, callback: Callable[[Dict[str, Any]], None]):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            callback: オプション選択後に呼び出される関数
        """
        self.parent = parent
        self.callback = callback
        
        # ダイアログウィンドウを作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("採点済み答案の出力オプション")
        self.dialog.geometry("500x600")  # 高さを増やしてコンテンツが収まるようにする
        self.dialog.minsize(500, 600)  # 最小サイズも同様に設定
        self.dialog.transient(parent)  # 親ウィンドウに対してモーダルに設定
        self.dialog.grab_set()  # モーダルモードに設定
        
        # ウィンドウの中央揃え
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # ウィジェットを作成
        self._create_widgets()
        
        # フォーカスを設定
        self.dialog.focus_set()
        
    def _create_widgets(self):
        """ダイアログのウィジェットを作成"""
        # メインフレーム（スクロール可能に）
        self.canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # メインフレーム
        main_frame = ttk.Frame(self.scrollable_frame, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトルラベル
        title_label = ttk.Label(
            main_frame, 
            text="採点済み答案に表示する情報を選択してください", 
            font=("", 12, "bold")
        )
        title_label.pack(pady=(0, 15))  # 下部のパディングを調整
        
        # --- 基本オプションフレーム ---
        options_frame = ttk.LabelFrame(main_frame, text="基本表示オプション")
        options_frame.pack(fill=tk.X, pady=10)
        
        # チェックボックス用変数
        self.question_scores_var = tk.BooleanVar(value=True)
        self.total_score_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=False)
        
        # 設問ごとの得点チェックボックス
        question_scores_cb = ttk.Checkbutton(
            options_frame, 
            text="設問ごとの得点を表示する", 
            variable=self.question_scores_var,
            command=self._check_selection
        )
        question_scores_cb.pack(anchor=tk.W, padx=30, pady=8)
        
        # 合計得点チェックボックス
        total_score_cb = ttk.Checkbutton(
            options_frame, 
            text="合計得点を表示する", 
            variable=self.total_score_var,
            command=self._check_selection
        )
        total_score_cb.pack(anchor=tk.W, padx=30, pady=8)
        
        # 〇×△マークチェックボックス
        symbols_cb = ttk.Checkbutton(
            options_frame, 
            text="〇×△マークを表示する", 
            variable=self.symbols_var,
            command=self._update_ui_state
        )
        symbols_cb.pack(anchor=tk.W, padx=30, pady=8)
        
        # --- マーク設定フレーム ---
        self.mark_options_frame = ttk.LabelFrame(main_frame, text="マークと文字の設定")
        self.mark_options_frame.pack(fill=tk.X, pady=10)
        
        # 文字の濃さ設定
        transparency_frame = ttk.Frame(self.mark_options_frame)
        transparency_frame.pack(fill=tk.X, padx=30, pady=8)
        
        transparency_label = ttk.Label(
            transparency_frame,
            text="文字の濃さ:"
        )
        transparency_label.pack(side=tk.LEFT)
        
        self.transparency_var = tk.IntVar(value=50)  # デフォルト50%
        
        # 左側のラベル（薄い）
        light_label = ttk.Label(
            transparency_frame,
            text="薄い",
            font=("Meiryo UI", 8, "bold")
        )
        light_label.pack(side=tk.LEFT, padx=(10, 0))
        
        transparency_slider = ttk.Scale(
            transparency_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.transparency_var,
            length=160
        )
        transparency_slider.pack(side=tk.LEFT, padx=(0, 0))
        
        # 右側のラベル（濃い）
        dense_label = ttk.Label(
            transparency_frame,
            text="濃い",
            font=("Meiryo UI", 8, "bold")
        )
        dense_label.pack(side=tk.LEFT, padx=(0, 5))
        
        transparency_value_label = ttk.Label(
            transparency_frame,
            textvariable=tk.StringVar(value="50%")
        )
        transparency_value_label.pack(side=tk.LEFT)
        
        # スライダー値が変更されたときにラベルを更新
        def update_transparency_label(event=None):
            transparency_value_label.config(text=f"{self.transparency_var.get()}%")
        
        transparency_slider.bind("<Motion>", update_transparency_label)
        transparency_slider.bind("<ButtonRelease-1>", update_transparency_label)
        
        # --- 得点表示設定フレーム ---
        self.score_display_frame = ttk.LabelFrame(main_frame, text="得点表示設定")
        self.score_display_frame.pack(fill=tk.X, pady=10)
        
        # 得点表示位置
        position_frame = ttk.Frame(self.score_display_frame)
        position_frame.pack(fill=tk.X, padx=30, pady=8)
        
        position_label = ttk.Label(
            position_frame,
            text="得点表示位置:"
        )
        position_label.pack(side=tk.LEFT)
        
        self.position_var = tk.StringVar(value="right")  # デフォルトは右端
        position_right = ttk.Radiobutton(
            position_frame,
            text="右端",
            variable=self.position_var,
            value="right"
        )
        position_right.pack(side=tk.LEFT, padx=10)
        
        position_center = ttk.Radiobutton(
            position_frame,
            text="マークの横（中央）",
            variable=self.position_var,
            value="center"
        )
        position_center.pack(side=tk.LEFT, padx=10)
        
        position_left = ttk.Radiobutton(
            position_frame,
            text="左端",
            variable=self.position_var,
            value="left"
        )
        position_left.pack(side=tk.LEFT, padx=10)
        
        # 得点表示色
        color_frame = ttk.Frame(self.score_display_frame)
        color_frame.pack(fill=tk.X, padx=30, pady=8)
        
        color_label = ttk.Label(
            color_frame,
            text="得点表示色:"
        )
        color_label.pack(side=tk.LEFT)
        
        self.score_color_var = tk.StringVar(value="red")  # デフォルトは赤
        color_red = ttk.Radiobutton(
            color_frame,
            text="赤",
            variable=self.score_color_var,
            value="red"
        )
        color_red.pack(side=tk.LEFT, padx=10)
        
        color_same = ttk.Radiobutton(
            color_frame,
            text="マークと同じ",
            variable=self.score_color_var,
            value="same"
        )
        color_same.pack(side=tk.LEFT, padx=10)
        
        color_black = ttk.Radiobutton(
            color_frame,
            text="黒",
            variable=self.score_color_var,
            value="black"
        )
        color_black.pack(side=tk.LEFT, padx=10)
        
        # 注意書きフレーム
        note_frame = ttk.Frame(main_frame, relief=tk.GROOVE, borderwidth=1)
        note_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 注意書き
        note_label = ttk.Label(
            note_frame, 
            text="※少なくとも1つのオプションを選択してください\n"
                 "※「〇×△マークを表示する」をオンにすると、マーク色は自動的に設定されます\n"
                 "  〇：青色、×：赤色、△：緑色",
            foreground="#555555",
            justify=tk.LEFT,
            padding=(10, 8)
        )
        note_label.pack(anchor=tk.W, fill=tk.X)
        
        # スペーサーフレーム（下部に余白を作る）
        spacer = ttk.Frame(main_frame)
        spacer.pack(fill=tk.BOTH, expand=True)
        
        # ボタンフレーム - 画面の下部に固定
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0), side=tk.BOTTOM)
        
        # キャンセルボタン
        cancel_button = ttk.Button(
            button_frame, 
            text="キャンセル", 
            command=self._on_cancel,
            padding=(10, 5)
        )
        cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 確認ボタン
        self.ok_button = ttk.Button(
            button_frame, 
            text="出力する", 
            command=self._on_ok,
            padding=(10, 5)
        )
        self.ok_button.pack(side=tk.RIGHT)
        
        # 初期状態を設定
        self._update_ui_state()
        
    def _update_ui_state(self):
        """UI状態を更新（マーク設定がオフのときは関連オプションを無効化）"""
        # 選択状態をチェック（ボタンの有効/無効を設定）
        if not any([
            self.question_scores_var.get(),
            self.total_score_var.get(),
            self.symbols_var.get()
        ]):
            self.ok_button.config(state=tk.DISABLED)
        else:
            self.ok_button.config(state=tk.NORMAL)
        
        # マーク設定フレームの有効/無効を切り替え（文字の濃さスライダーは常に有効）
        mark_enabled = self.symbols_var.get()
        for child in self.mark_options_frame.winfo_children():
            for widget in child.winfo_children():
                # スライダーは常に有効、その他のウィジェットはマーク設定に依存
                if isinstance(widget, ttk.Scale):
                    widget.configure(state="normal")
                elif isinstance(widget, ttk.Radiobutton):
                    widget.configure(state="normal" if mark_enabled else "disabled")
        
        # 得点表示設定フレームの有効/無効を切り替え
        score_enabled = self.question_scores_var.get() or self.total_score_var.get()
        for child in self.score_display_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Radiobutton)):
                    widget.configure(state="normal" if score_enabled else "disabled")
    
    def _check_selection(self):
        """少なくとも1つのオプションが選択されているか確認"""
        # 選択状態に応じてUIを更新（こちらからは_update_ui_stateを呼ばない）
        self._update_ui_state()
    
    def _on_cancel(self):
        """キャンセルボタンが押された時の処理"""
        self.dialog.destroy()
    
    def _on_ok(self):
        """OKボタンが押された時の処理"""
        # 選択されたオプションを収集
        options = {
            'question_scores': self.question_scores_var.get(),
            'total_score': self.total_score_var.get(),
            'symbols': self.symbols_var.get(),
            'transparency': self.transparency_var.get(),
            'score_position': self.position_var.get(),
            'score_color': self.score_color_var.get()
        }
        
        # 一つも選択されていない場合は警告
        if not any([
            options['question_scores'],
            options['total_score'],
            options['symbols']
        ]):
            messagebox.showerror(
                'エラー', 
                '少なくとも1つのオプションを選択してください。'
            )
            return
        
        # コールバック関数を呼び出し
        self.dialog.destroy()
        self.callback(options)