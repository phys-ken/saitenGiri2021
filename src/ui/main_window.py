"""
アプリケーションのメインウィンドウを管理するモジュール
"""
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

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
        self.top_image = None
        self.top_figure = None
        
        # ウィンドウの設定
        self.root.title("採点斬り")
        self.root.geometry("800x420")  # 少し高さを増やして新しいボタン用のスペースを確保
        self.root.configure(bg='white')
        
        # ウィンドウの初期化
        self._init_top_frame()
    
    def _init_top_frame(self) -> None:
        """トップ画面を初期化します"""
        # 既存のフレームがあれば削除
        if self.top_frame:
            self.top_frame.destroy()
        
        # トップフレームを作成
        self.top_frame = tk.Frame(self.root, bg="white")
        self.top_frame.pack()
        
        # 画像表示フレームの設定
        fig_frame = tk.Frame(self.top_frame, width=500, height=400)
        fig_frame.grid(column=0, row=0)
        
        # トップ画像の読み込みと表示
        try:
            top_img_path = resource_path("resources/top.png")
            val = 0.4  # リサイズ比率
            
            top_img = Image.open(top_img_path)
            top_img = top_img.resize(
                (int(top_img.width * val), int(top_img.height * val)), 
                Image.Resampling.LANCZOS
            )
            self.top_figure = ImageTk.PhotoImage(top_img, master=self.root)
            
            canvas_top = tk.Canvas(
                bg="white", master=fig_frame, width=500, height=400, highlightthickness=0
            )
            canvas_top.place(x=0, y=0)
            canvas_top.create_image(0, 0, image=self.top_figure, anchor=tk.NW)
            canvas_top.pack()
        except Exception as e:
            print(f"トップ画像の読み込みに失敗しました: {e}")
        
        # ボタンフレームの設定
        button_frame = tk.Frame(self.top_frame, bg="white", highlightthickness=0)
        button_frame.grid(column=1, row=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # ボタンの共通設定
        button_width = 20
        expand_bool = True
        
        # ボタンの作成
        info_button = tk.Button(
            button_frame, text="はじめに", command=self.show_info,
            width=button_width, height=2, highlightthickness=0
        )
        info_button.pack(expand=expand_bool)
        
        init_button = tk.Button(
            button_frame, text="初期設定をする", command=self.initialize_settings,
            width=button_width, height=2, highlightthickness=0
        )
        init_button.pack(expand=expand_bool)
        
        trim_define_button = tk.Button(
            button_frame, text="どこを斬るか決める", command=self.launch_trim_define,
            width=button_width, height=2, highlightthickness=0
        )
        trim_define_button.pack(expand=expand_bool)
        
        trim_all_button = tk.Button(
            button_frame, text="全員の解答用紙を斬る", command=self.trim_all_papers,
            width=button_width, height=2, highlightthickness=0
        )
        trim_all_button.pack(expand=expand_bool)
        
        grade_button = tk.Button(
            button_frame, text="斬った画像を採点する", command=self.launch_grading,
            width=button_width, height=2, highlightthickness=0
        )
        grade_button.pack(expand=expand_bool)
        
        excel_button = tk.Button(
            button_frame, text="Excelに出力", command=self.export_excel,
            width=button_width, height=2, highlightthickness=0
        )
        excel_button.pack(expand=expand_bool)
        
        # ボタン名を「採点済み答案を出力」に変更
        write_img_button = tk.Button(
            button_frame, text="採点済み答案を出力", command=self.write_graded_images,
            width=button_width, height=2, highlightthickness=0
        )
        write_img_button.pack(expand=expand_bool)
        
        exit_button = tk.Button(
            button_frame, text="アプリを閉じる", command=self.exit_app,
            width=button_width, height=2, highlightthickness=0
        )
        exit_button.pack(expand=expand_bool)
    
    def show_info(self) -> None:
        """アプリケーションの情報を表示します"""
        messagebox.showinfo(
            "はじめに", 
            "オンラインヘルプをご覧ください。\n"
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
            else:
                messagebox.showinfo('設定キャンセル', 'フォルダーの作成を中止しました。')
        else:
            messagebox.showinfo(
                '確認', 
                '初期設定は完了しています。解答用紙を「setting/input」フォルダーに配置し、切り取りを開始してください。'
            )
    
    def launch_trim_define(self) -> None:
        """切り取り領域定義画面を起動します"""
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
    
    def trim_all_papers(self) -> None:
        """すべての解答用紙を切り取ります"""
        ret = messagebox.askyesno(
            '確認', 
            '全員分の解答用紙を切り取ります。\n'
            '処理を続行しますか？\n\n'
            '①大量の画像では時間がかかる場合があります。\n'
            '②「setting/input」の画像はそのまま保持されます。\n'
            '③既存の「setting/output」は上書きされます。'
        )
        
        if ret:
            trimmer = ImageTrimmer(input_dir=str(SETTING_DIR / "input"), output_dir=str(SETTING_DIR / "output"))
            success = trimmer.trim_all_images()
            
            if success:
                messagebox.showinfo('完了', '全員分の解答用紙の切り取りが完了しました。')
            else:
                messagebox.showerror('エラー', '切り取り処理中にエラーが発生しました。')
    
    def launch_grading(self) -> None:
        """採点画面を起動します"""
        from .components.grading_selector import GradingSelectorWindow
        from .components.grading_window import GradingWindow
        
        # 問題選択時のコールバック関数
        def on_question_selected(question_id):
            GradingWindow(self.root, question_id)
            
        GradingSelectorWindow(self.root, on_question_selected)
    
    def export_excel(self) -> None:
        """採点結果をExcelに出力します"""
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
            
            # 確認ダイアログ
            options_text = []
            if options.get('question_scores', False):
                options_text.append("・設問ごとの得点")
            if options.get('total_score', False):
                options_text.append("・合計得点")
            if options.get('symbols', False):
                options_text.append("・〇×△マーク")
            
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