"""
採点する問題を選択するウィンドウ
"""
import os
import tkinter as tk
from tkinter import messagebox
from typing import List, Callable, Optional

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
        
        self.window = tk.Toplevel(parent)
        self.window.title("採点する問題を選ぶ")
        self.window.geometry("500x530")  # 高さを少し大きくして採点モード選択用のスペースを確保
        
        # リストボックスの作成
        self.listbox = tk.Listbox(self.window, selectmode='single', height=20, width=20)
        self.listbox.grid(row=0, column=0)
        
        # スクロールバー
        scrollbar = tk.Scrollbar(
            self.window,
            orient=tk.VERTICAL,
            command=self.listbox.yview
        )
        self.listbox['yscrollcommand'] = scrollbar.set
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.W))
        
        # ボタンフレーム
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=0, column=2, sticky=tk.W + tk.E + tk.N + tk.S, padx=30, pady=30)
        
        # 凡例ラベル
        tk.Label(button_frame, text="未採点", bg="white").pack(side=tk.TOP, fill=tk.X)
        tk.Label(button_frame, text="採点中", bg="pale green").pack(side=tk.TOP, fill=tk.X)
        tk.Label(button_frame, text="採点終了", bg="gray").pack(side=tk.TOP, fill=tk.X)
        
        # 採点モード選択フレーム
        grade_mode_frame = tk.LabelFrame(self.window, text="採点モード")
        grade_mode_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W + tk.E, padx=10, pady=5)
        
        # 採点モードの選択（ラジオボタン）
        self.mode_var = tk.StringVar(value="single")
        
        single_radio = tk.Radiobutton(
            grade_mode_frame, 
            text="1枚ずつ採点", 
            variable=self.mode_var, 
            value="single"
        )
        single_radio.pack(side=tk.LEFT, padx=20, pady=5)
        
        grid_radio = tk.Radiobutton(
            grade_mode_frame, 
            text="一覧採点（タイルビュー）", 
            variable=self.mode_var, 
            value="grid"
        )
        grid_radio.pack(side=tk.LEFT, padx=20, pady=5)
        
        # 採点ボタン
        tk.Button(
            button_frame, 
            text='採点する', 
            width=15, 
            height=3,
            command=self._on_grade_button_clicked
        ).pack(expand=True)
        
        # トップに戻るボタン
        tk.Button(
            button_frame, 
            text='Topに戻る', 
            width=15, 
            height=3,
            command=self._on_back_button_clicked
        ).pack()
        
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
                            if os.path.isfile(os.path.join(item_path, sub_item)) and sub_item.lower().endswith(('.jpg', '.jpeg', '.png')):
                                graded_count += 1
                
                # リストボックスに追加
                self.listbox.insert(tk.END, question_dir)
                
                # 全く未採点の場合は白、すべて採点済みの場合はグレー、一部採点の場合は緑
                if graded_count == 0:
                    # 全問題未採点
                    if file_count > 0:
                        self.listbox.itemconfig(counter, {'bg': 'white'})
                    else:
                        # 問題自体に画像がない場合
                        self.listbox.itemconfig(counter, {'bg': 'pink'})
                elif file_count == 0 and graded_count == max_student_count:
                    # 全問題採点済み
                    self.listbox.itemconfig(counter, {'bg': 'gray'})
                else:
                    # 一部採点済み
                    self.listbox.itemconfig(counter, {'bg': 'pale green'})
                
                counter += 1
                
        except Exception as e:
            print(f"問題フォルダの読み込みエラー: {e}")
            messagebox.showerror("エラー", f"問題フォルダの読み込み中にエラーが発生しました:\n{e}")
    
    def _on_grade_button_clicked(self) -> None:
        """採点ボタンがクリックされたときの処理"""
        try:
            # 選択された問題IDを取得
            selection = self.listbox.curselection()
            if not selection:
                messagebox.showinfo("選択エラー", "問題を選択してください")
                return
            
            question_id = self.listbox.get(selection[0])
            print(f"選択された問題: {question_id}")
            
            # 選択された採点モードを取得
            grade_mode = self.mode_var.get()
            print(f"選択された採点モード: {grade_mode}")
            
            # 出力ディレクトリ内の問題フォルダをチェック
            question_path = os.path.join(SETTING_DIR, "output", question_id)
            if not os.path.exists(question_path):
                messagebox.showerror("エラー", f"問題フォルダが見つかりません: {question_path}")
                return
            
            # 未採点の画像があるか確認
            has_ungraded = False
            for item in os.listdir(question_path):
                item_path = os.path.join(question_path, item)
                if os.path.isfile(item_path) and item.lower().endswith(('.jpg', '.jpeg', '.png')):
                    has_ungraded = True
                    break
            
            # 採点済みの画像があるか確認
            has_graded = False
            for item in os.listdir(question_path):
                item_path = os.path.join(question_path, item)
                if os.path.isdir(item_path):
                    for sub_item in os.listdir(item_path):
                        if os.path.isfile(os.path.join(item_path, sub_item)) and sub_item.lower().endswith(('.jpg', '.jpeg', '.png')):
                            has_graded = True
                            break
                    if has_graded:
                        break
            
            if not (has_ungraded or has_graded):
                messagebox.showinfo("情報", f"問題 {question_id} には採点可能な画像がありません。")
                return
            
            # コールバック関数を呼び出して選択された問題IDと採点モードを渡す
            if self.on_question_selected:
                self.on_question_selected(question_id, grade_mode)
            
            # ウィンドウを閉じる
            self.window.destroy()
        except Exception as e:
            print(f"採点ボタンクリック時のエラー: {e}")
            messagebox.showerror("エラー", f"採点処理の開始中にエラーが発生しました:\n{e}")
    
    def _on_back_button_clicked(self) -> None:
        """戻るボタンがクリックされたときの処理"""
        self.window.destroy()