"""
採点済み答案の出力オプションを選択するダイアログ
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Callable


class ExportOptionsDialog:
    """
    採点済み答案の出力オプションを選択するダイアログウィンドウ
    
    このダイアログでは、以下のオプションを選択できます：
    - 設問ごとの得点を表示する
    - 合計得点を表示する
    - 〇×△マークを表示する
    """
    
    def __init__(self, parent: tk.Tk, callback: Callable[[Dict[str, bool]], None]):
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
        self.dialog.geometry("400x250")
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
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトルラベル
        title_label = ttk.Label(
            main_frame, 
            text="採点済み答案に表示する情報を選択してください", 
            font=("", 12, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # オプションフレーム
        options_frame = ttk.LabelFrame(main_frame, text="表示オプション")
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
        question_scores_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # 合計得点チェックボックス
        total_score_cb = ttk.Checkbutton(
            options_frame, 
            text="合計得点を表示する", 
            variable=self.total_score_var,
            command=self._check_selection
        )
        total_score_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # 〇×△マークチェックボックス
        symbols_cb = ttk.Checkbutton(
            options_frame, 
            text="〇×△マークを表示する", 
            variable=self.symbols_var,
            command=self._check_selection
        )
        symbols_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # 注意書き
        note_label = ttk.Label(
            main_frame, 
            text="※少なくとも1つのオプションを選択してください\n※〇×△マーク機能はOpenCVライブラリが必要です",
            foreground="gray",
            justify=tk.LEFT
        )
        note_label.pack(anchor=tk.W, pady=(10, 0))
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # キャンセルボタン
        cancel_button = ttk.Button(
            button_frame, 
            text="キャンセル", 
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 確認ボタン
        self.ok_button = ttk.Button(
            button_frame, 
            text="出力する", 
            command=self._on_ok
        )
        self.ok_button.pack(side=tk.RIGHT)
        
    def _check_selection(self):
        """少なくとも1つのオプションが選択されているか確認"""
        if not any([
            self.question_scores_var.get(),
            self.total_score_var.get(),
            self.symbols_var.get()
        ]):
            self.ok_button.config(state=tk.DISABLED)
        else:
            self.ok_button.config(state=tk.NORMAL)
    
    def _on_cancel(self):
        """キャンセルボタンが押された時の処理"""
        self.dialog.destroy()
    
    def _on_ok(self):
        """OKボタンが押された時の処理"""
        # 選択されたオプションを収集
        options = {
            'question_scores': self.question_scores_var.get(),
            'total_score': self.total_score_var.get(),
            'symbols': self.symbols_var.get()
        }
        
        # 一つも選択されていない場合は警告
        if not any(options.values()):
            messagebox.showerror(
                'エラー', 
                '少なくとも1つのオプションを選択してください。'
            )
            return
        
        # コールバック関数を呼び出し
        self.dialog.destroy()
        self.callback(options)