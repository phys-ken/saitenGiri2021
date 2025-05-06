"""
採点する問題を選択するウィンドウ
"""
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Callable, Optional, Dict

from ...utils.file_utils import SETTING_DIR, get_sorted_image_files


class GradingSelectorWindow:
    """採点問題選択ウィンドウ"""

    def __init__(self, parent: tk.Tk, on_question_selected: Callable[[str, str], None]):
        """
        初期化処理
        
        Args:
            parent: 親ウィンドウ
            on_question_selected: 問題選択時のコールバック関数
        """
        self.parent = parent
        self.on_question_selected = on_question_selected
        
        # 問題データ管理用の変数
        self.question_data = {}  # 問題IDと採点状況を管理する辞書
        self.selected_question_id = None  # 選択された問題ID
        self.grade_button = None  # 採点ボタン参照（有効/無効切り替え用）
        
        # ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("採点する問題を選ぶ")
        self.window.geometry("900x600")  # ウィンドウサイズを大きくして要素がつぶれないようにする
        self.window.configure(bg="#f5f5f5")
        self.window.minsize(900, 600)  # 最小サイズも設定
        
        # メインフレーム（余白を設ける）
        main_frame = tk.Frame(self.window, padx=15, pady=15, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 説明ラベル
        header_label = tk.Label(
            main_frame, 
            text="採点したい問題を選択してください", 
            font=("Meiryo UI", 12, "bold"),
            bg="#f5f5f5",
            anchor="w"
        )
        header_label.pack(fill=tk.X, pady=(0, 15))
        
        # リスト領域とコントロール領域を含むフレーム
        content_frame = tk.Frame(main_frame, bg="#f5f5f5")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側：問題リスト領域
        list_frame = tk.LabelFrame(
            content_frame, 
            text="問題一覧", 
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10, 
            pady=10
        )
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # リスト表示用フレーム（スクロール付き）
        list_view_frame = tk.Frame(list_frame, bg="white")
        list_view_frame.pack(fill=tk.BOTH, expand=True)
        
        # リストボックスの作成（背景色を白に設定）
        self.listbox = tk.Listbox(
            list_view_frame, 
            selectmode='single',
            height=20,  # 高さを増加
            width=25,
            font=("Meiryo UI", 11),  # フォントサイズを少し大きく
            bg="white",
            activestyle="none",
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self._on_question_selected)
        
        # スクロールバー
        scrollbar = tk.Scrollbar(
            list_view_frame,
            orient=tk.VERTICAL,
            command=self.listbox.yview
        )
        self.listbox['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右側：情報と操作領域
        info_frame = tk.Frame(content_frame, bg="#f5f5f5", padx=10)
        info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 10), pady=0, expand=False)
        # 右側のフレームに幅を指定して、十分なスペースを確保
        info_frame.config(width=400)
        
        # 選択状況表示領域
        selection_frame = tk.LabelFrame(
            info_frame, 
            text="選択状況", 
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10, 
            pady=10
        )
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 選択問題表示ラベル
        self.selected_question_label = tk.Label(
            selection_frame, 
            text="選択された問題: なし", 
            font=("Meiryo UI", 10),
            bg="#f5f5f5", 
            anchor="w"
        )
        self.selected_question_label.pack(fill=tk.X, pady=5)
        
        # 採点状況表示ラベル
        self.grading_status_label = tk.Label(
            selection_frame, 
            text="採点状況: -", 
            font=("Meiryo UI", 10),
            bg="#f5f5f5", 
            anchor="w"
        )
        self.grading_status_label.pack(fill=tk.X, pady=5)
        
        # 凡例フレーム
        legend_frame = tk.LabelFrame(
            info_frame, 
            text="凡例",
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10, 
            pady=10
        )
        legend_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 凡例ラベル（各状態をより見やすく表示）
        legend_items = [
            ("未採点", "white", "未採点の問題"),
            ("採点中", "pale green", "一部採点済みの問題"),
            ("採点終了", "gray", "すべて採点済みの問題")
        ]
        
        for text, color, desc in legend_items:
            legend_item_frame = tk.Frame(legend_frame, bg="#f5f5f5")
            legend_item_frame.pack(fill=tk.X, pady=3)
            
            color_box = tk.Label(
                legend_item_frame, 
                text="", 
                bg=color, 
                width=3, 
                height=1,
                borderwidth=1,
                relief="solid"
            )
            color_box.pack(side=tk.LEFT, padx=(0, 5))
            
            label = tk.Label(
                legend_item_frame, 
                text=f"{text}: {desc}", 
                font=("Meiryo UI", 9),
                bg="#f5f5f5",
                anchor="w"
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 採点モード選択フレーム
        grade_mode_frame = tk.LabelFrame(
            info_frame, 
            text="採点モード", 
            font=("Meiryo UI", 10, "bold"),
            bg="#f5f5f5",
            padx=10, 
            pady=10
        )
        grade_mode_frame.pack(fill=tk.X, pady=(0, 15))
        # 最小の高さを設定して、内容が潰れないようにする
        grade_mode_frame.config(height=150)
        
        # 採点モードの選択（ラジオボタン）
        self.mode_var = tk.StringVar(value="grid")  # デフォルトは一覧採点
        
        # 一覧採点ラジオボタンと解説テキスト（ラジオボタンを先に表示）
        grid_radio_frame = tk.Frame(grade_mode_frame, bg="#f5f5f5")
        grid_radio_frame.pack(fill=tk.X, pady=(5, 10), anchor=tk.W)
        
        grid_radio = tk.Radiobutton(
            grid_radio_frame, 
            text="一覧採点", 
            variable=self.mode_var, 
            value="grid",
            font=("Meiryo UI", 10),
            bg="#f5f5f5",
            command=self._update_grade_button_state
        )
        grid_radio.pack(side=tk.LEFT, anchor=tk.W)
        
        # 一覧採点の解説テキスト（ラジオボタンの下に配置）
        grid_desc_frame = tk.Frame(grade_mode_frame, bg="#f5f5f5")
        grid_desc_frame.pack(fill=tk.X, pady=(0, 10), padx=(25, 5))
        
        grid_desc_label = tk.Label(
            grid_desc_frame,
            text="一覧形式で複数の解答を同時に表示し、効率的に採点できます。",
            font=("Meiryo UI", 8),
            wraplength=250,
            justify=tk.LEFT,
            bg="#f5f5f5",
            fg="#666666"
        )
        grid_desc_label.pack(anchor=tk.W, fill=tk.X)
        
        # 1枚ずつ採点ラジオボタンと解説テキスト（ラジオボタンを先に表示）
        single_radio_frame = tk.Frame(grade_mode_frame, bg="#f5f5f5")
        single_radio_frame.pack(fill=tk.X, pady=(0, 5), anchor=tk.W)
        
        single_radio = tk.Radiobutton(
            single_radio_frame, 
            text="1枚ずつ採点", 
            variable=self.mode_var, 
            value="single",
            font=("Meiryo UI", 10),
            bg="#f5f5f5",
            command=self._update_grade_button_state
        )
        single_radio.pack(side=tk.LEFT, anchor=tk.W)
        
        # 1枚ずつ採点の解説テキスト（ラジオボタンの下に配置）
        single_desc_frame = tk.Frame(grade_mode_frame, bg="#f5f5f5")
        single_desc_frame.pack(fill=tk.X, pady=(0, 5), padx=(25, 5))
        
        single_desc_label = tk.Label(
            single_desc_frame,
            text="1枚ずつ表示して順番に採点します。採点済みの問題は選択できません。",
            font=("Meiryo UI", 8),
            wraplength=250,
            justify=tk.LEFT,
            bg="#f5f5f5",
            fg="#666666"
        )
        single_desc_label.pack(anchor=tk.W, fill=tk.X)
        
        # 操作ボタンフレーム
        button_frame = tk.Frame(info_frame, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=15)
        
        # 採点ボタン（より目立つデザイン）- サイズを固定して潰れないようにする
        self.grade_button = tk.Button(
            button_frame, 
            text='採点する', 
            width=15, 
            height=2,
            font=("Meiryo UI", 11, "bold"),
            bg="#4CAF50",  # 緑色
            fg="white",   # 白い文字
            relief=tk.RAISED,
            state=tk.DISABLED,  # 初期状態は無効
            command=self._on_grade_button_clicked
        )
        self.grade_button.pack(side=tk.LEFT, padx=5)
        
        # トップに戻るボタン - サイズを固定
        back_button = tk.Button(
            button_frame, 
            text='戻る', 
            width=15, 
            height=2,
            font=("Meiryo UI", 10),
            command=self._on_back_button_clicked
        )
        back_button.pack(side=tk.RIGHT, padx=5)
        
        # ボタンフレームに最小の高さを設定
        button_frame.config(height=60)
        button_frame.pack_propagate(False)  # サイズが子要素に合わせて変わらないようにする
        
        # フッターフレーム（エラーメッセージ表示用）
        footer_frame = tk.Frame(main_frame, bg="#f5f5f5", height=30)
        footer_frame.pack(fill=tk.X, pady=(15, 0))
        
        # エラーメッセージ表示用ラベル（目立つ背景色で警告表示）
        self.error_frame = tk.Frame(footer_frame, bg="#ffebee", bd=1, relief=tk.FLAT)
        self.error_label = tk.Label(
            self.error_frame,
            text="",
            font=("Meiryo UI", 9),
            fg="#d32f2f",  # 濃い赤色
            bg="#ffebee",  # 薄い赤色の背景
            anchor="w",
            padx=10,
            pady=5
        )
        self.error_label.pack(fill=tk.X)
        # 初期状態ではエラーフレームは非表示
        
        # 問題フォルダを読み込み、リストに表示
        self._load_question_folders()
        
        # モーダルウィンドウとして表示
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_set()
        self.window.wait_window()
    
    def _load_question_folders(self) -> None:
        """問題フォルダを読み込み、リストに表示します"""
        # 入出力フォルダ
        input_dir = os.path.join(SETTING_DIR, "input")
        output_dir = os.path.join(SETTING_DIR, "output")
        
        # 全受験者数を計算（解答用紙数）        
        try:
            max_student_count = len([f for f in os.listdir(input_dir) 
                                   if os.path.isfile(os.path.join(input_dir, f)) 
                                   and f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            print(f"解答用紙の総数: {max_student_count}")
        except Exception as e:
            print(f"入力ディレクトリの読み込みエラー: {e}")
            max_student_count = 0
        
        # 出力フォルダ内の問題フォルダを取得
        try:
            question_dirs = []
            if os.path.exists(output_dir):
                for item in os.listdir(output_dir):
                    item_path = os.path.join(output_dir, item)
                    if os.path.isdir(item_path) and item != "name":
                        question_dirs.append(item)
            question_dirs.sort()
            
            if not question_dirs:
                self._show_error("採点可能な問題フォルダが見つかりません。先に「全員の解答用紙を斬る」を実行してください。")
                return
            
            # リストボックスに問題フォルダを追加
            counter = 0
            for question_dir in question_dirs:
                # ディレクトリ内のファイル数を取得（採点済みのサブフォルダも確認）
                question_path = os.path.join(output_dir, question_dir)
                file_count = 0
                
                # ルートレベルのファイル数（未採点）
                for item in os.listdir(question_path):
                    item_path = os.path.join(question_path, item)
                    if os.path.isfile(item_path) and item.lower().endswith(('.jpg', '.jpeg', '.png')):
                        file_count += 1
                
                # サブフォルダ内のファイル数（採点済み）
                graded_count = 0
                for item in os.listdir(question_path):
                    item_path = os.path.join(question_path, item)
                    if os.path.isdir(item_path):
                        for sub_item in os.listdir(item_path):
                            sub_item_path = os.path.join(item_path, sub_item)
                            if os.path.isfile(sub_item_path) and sub_item.lower().endswith(('.jpg', '.jpeg', '.png')):
                                graded_count += 1
                
                # ステータス情報を保存
                self.question_data[question_dir] = {
                    "ungraded_count": file_count,
                    "graded_count": graded_count,
                    "total_count": file_count + graded_count,
                    "is_complete": file_count == 0 and graded_count > 0
                }
                
                # リストボックスに追加
                # 問題IDと採点状況を表示
                display_text = question_dir
                if graded_count > 0 or file_count > 0:
                    total = graded_count + file_count
                    percent = int((graded_count / total) * 100) if total > 0 else 0
                    display_text = f"{question_dir} ({percent}%)"
                
                self.listbox.insert(tk.END, display_text)
                
                # 全く未採点の場合は白、すべて採点済みの場合はグレー、一部採点の場合は緑
                if graded_count == 0:
                    # 全問題未採点
                    if file_count > 0:
                        self.listbox.itemconfig(counter, {'bg': 'white'})
                    else:
                        # 問題自体に画像がない場合
                        self.listbox.itemconfig(counter, {'bg': 'pink'})
                elif file_count == 0 and graded_count > 0:
                    # 全問題採点済み
                    self.listbox.itemconfig(counter, {'bg': 'gray'})
                else:
                    # 一部採点済み
                    self.listbox.itemconfig(counter, {'bg': 'pale green'})
                
                counter += 1
                
        except Exception as e:
            print(f"問題フォルダの読み込みエラー: {e}")
            self._show_error(f"問題フォルダの読み込み中にエラーが発生しました")
    
    def _on_question_selected(self, event=None) -> None:
        """問題が選択されたときの処理"""
        selection = self.listbox.curselection()
        if not selection:
            self.selected_question_id = None
            self.selected_question_label.config(text="選択された問題: なし")
            self.grading_status_label.config(text="採点状況: -")
            self._update_grade_button_state()
            return
        
        # 選択された問題IDを取得（表示用テキストから問題IDを抽出）
        selected_text = self.listbox.get(selection[0])
        # "Q_0001 (50%)" のような形式から "Q_0001" 部分を抽出
        question_id = selected_text.split(" ")[0]
        
        self.selected_question_id = question_id
        self.selected_question_label.config(text=f"選択された問題: {question_id}")
        
        # 採点状況を表示
        if question_id in self.question_data:
            data = self.question_data[question_id]
            graded = data["graded_count"]
            ungraded = data["ungraded_count"]
            total = data["total_count"]
            
            if total > 0:
                percent = int((graded / total) * 100)
                status_text = f"採点状況: {graded}/{total}件 ({percent}%)"
                self.grading_status_label.config(text=status_text)
            else:
                self.grading_status_label.config(text="採点状況: 対象ファイルなし")
        else:
            self.grading_status_label.config(text="採点状況: 不明")
        
        # 採点ボタンの状態を更新
        self._update_grade_button_state()
    
    def _update_grade_button_state(self) -> None:
        """採点モードと選択状態に基づいて採点ボタンの有効/無効を切り替えます"""
        # エラーメッセージをクリア
        self._hide_error()
        
        if not self.selected_question_id:
            # 問題が選択されていない場合は無効
            self.grade_button.config(state=tk.DISABLED)
            return
        
        # 問題データを取得
        data = self.question_data.get(self.selected_question_id, {})
        grade_mode = self.mode_var.get()
        
        # 採点完了している問題は「1枚ずつ採点」で選択できないようにする
        if grade_mode == "single" and data.get("is_complete", False):
            self.grade_button.config(state=tk.DISABLED)
            self._show_error("すべて採点済みの問題は「一覧採点」モードでのみ確認できます")
            return
        
        # 画像が存在するか確認
        if data.get("total_count", 0) == 0:
            self.grade_button.config(state=tk.DISABLED)
            self._show_error("この問題には採点対象の画像がありません")
            return
            
        # それ以外の場合は有効化
        self.grade_button.config(state=tk.NORMAL)
    
    def _on_grade_button_clicked(self) -> None:
        """採点ボタンがクリックされたときの処理"""
        try:
            if not self.selected_question_id:
                self._show_error("問題を選択してください")
                return
            
            question_id = self.selected_question_id
            
            # 選択された採点モードを取得
            grade_mode = self.mode_var.get()
            print(f"選択された問題: {question_id}, 採点モード: {grade_mode}")
            
            # 出力ディレクトリ内の問題フォルダをチェック
            question_path = os.path.join(SETTING_DIR, "output", question_id)
            if not os.path.exists(question_path):
                self._show_error(f"問題フォルダが見つかりません: {question_id}")
                return
            
            # 採点完了している問題は「1枚ずつ採点」で選択できないことを再確認
            data = self.question_data.get(question_id, {})
            if grade_mode == "single" and data.get("is_complete", False):
                self._show_error("すべて採点済みの問題は「一覧採点」モードでのみ確認できます")
                return
            
            # 問題フォルダに画像があるか確認
            if data.get("total_count", 0) == 0:
                self._show_error(f"問題 {question_id} には採点可能な画像がありません")
                return
            
            # コールバック関数を呼び出して選択された問題IDと採点モードを渡す
            if self.on_question_selected:
                self.on_question_selected(question_id, grade_mode)
            
            # ウィンドウを閉じる
            self.window.destroy()
        except Exception as e:
            print(f"採点ボタンクリック時のエラー: {e}")
            self._show_error("採点処理の開始中にエラーが発生しました")
    
    def _on_back_button_clicked(self) -> None:
        """戻るボタンがクリックされたときの処理"""
        self.window.destroy()
        
    def _show_error(self, message: str) -> None:
        """
        エラーメッセージを表示します
        
        Args:
            message: 表示するエラーメッセージ
        """
        if message:
            self.error_label.config(text=message)
            self.error_frame.pack(fill=tk.X, pady=(5, 0))
        
    def _hide_error(self) -> None:
        """エラーメッセージを非表示にします"""
        self.error_label.config(text="")
        self.error_frame.pack_forget()