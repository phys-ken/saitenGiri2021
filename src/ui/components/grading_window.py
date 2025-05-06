"""
採点を行うウィンドウクラス
"""
import os
import shutil
import tkinter as tk
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk
from typing import List, Dict, Optional, Any

from ...core.grader import Grader
from ...utils.image_utils import resize_image_for_canvas
from ...utils.file_utils import SETTING_DIR, ANSWER_DATA_DIR, get_sorted_image_files


class GradingWindow:
    """採点ウィンドウ"""
    
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
        self.tk_images = []  # tkinter用画像オブジェクトのリスト
        self.current_index = 0  # 現在表示中の画像インデックス
        self.filename_list = []  # ファイル名リスト
        
        # 採点データ
        self.score_dict = {}  # {ファイルパス: スコア}
        
        # 許可されている点数のリスト
        self.allowed_scores = []
        
        # 模範解答関連の変数
        self.has_sample_answer = self._check_sample_answer()
        self.sample_window = None  # 模範解答表示ウィンドウの参照
        self.sample_tk_img = None  # 模範解答画像の参照
        self.sample_original_img = None  # オリジナル画像の参照（拡大縮小用）
        self.sample_scale = 1.0  # 画像の拡大縮小率

        # ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("採点中...")
        self.window.geometry("1000x800")
        
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
    
    def _check_sample_answer(self) -> bool:
        """
        模範解答が利用可能かどうか確認します
        
        Returns:
            bool: 模範解答が利用可能な場合はTrue
        """
        # 模範解答ディレクトリと出力ディレクトリのチェック
        answer_output_dir = os.path.join(ANSWER_DATA_DIR, "output", self.question_id)
        return os.path.exists(answer_output_dir) and any(os.path.isfile(os.path.join(answer_output_dir, f)) 
                                                       for f in os.listdir(answer_output_dir))
    
    def _create_ui(self) -> None:
        """UI要素を作成します"""
        # メインフレーム
        self.main_frame = tk.Frame(self.window)
        self.main_frame.grid(column=0, row=0)
        
        # 採点設定フレーム
        self.settings_frame = tk.Frame(self.window)
        self.settings_frame.grid(column=1, row=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # キャンバス（画像表示領域）
        self.image_canvas = tk.Canvas(
            self.main_frame,
            bg="green",
            width=640,
            height=480
        )
        self.image_canvas.pack(expand=True, fill="both")
        
        # 採点結果表示ラベル
        self.score_var = tk.StringVar()
        self.score_var.set("1 ~ 9のキーで点数を入力してください\n[space]で採点をskipします")
        
        self.score_label = tk.Label(
            self.main_frame,
            textvariable=self.score_var,
            font=("Meiryo UI", 30),
            bg="white",
            relief="sunken"
        )
        self.score_label.pack()
        
        # ファイル名表示ラベル
        self.filename_var = tk.StringVar()
        self.filename_var.set("ファイル名")
        
        self.filename_label = tk.Label(
            self.main_frame,
            textvariable=self.filename_var,
            font=("Meiryo UI", 20),
            foreground="gray"
        )
        self.filename_label.pack()
        
        # 操作案内フレーム
        nav_frame = tk.Frame(self.main_frame)
        nav_frame.pack(fill=tk.X, expand=True)
        
        # 操作案内ラベル（左）
        back_label = tk.Label(
            nav_frame,
            text="←前へ\nキーボードの←ボタン",
            font=("Meiryo UI", 20)
        )
        back_label.pack(side=tk.LEFT, expand=True)
        
        # 模範解答表示リンク
        if self.has_sample_answer:
            self.sample_answer_link = tk.Label(
                nav_frame,
                text="模範解答を表示",
                font=("Meiryo UI", 12, "underline"),
                fg="#0066cc",
                cursor="hand2"
            )
            self.sample_answer_link.pack(side=tk.BOTTOM, pady=10)
            self.sample_answer_link.bind("<Button-1>", self.show_sample_answer)
        
        # 操作案内ラベル（右）
        next_label = tk.Label(
            nav_frame,
            text="次へ→\nキーボードの→ボタン",
            font=("Meiryo UI", 20)
        )
        next_label.pack(side=tk.RIGHT, expand=True)
        
        # 採点設定UI
        explanation1 = tk.Label(
            self.settings_frame,
            text="入力可能な点数にチェックをつけてください。"
        )
        explanation1.pack(side=tk.TOP)
        
        explanation2 = tk.Label(
            self.settings_frame,
            text="誤った数字キーを押すのを防ぎます。"
        )
        explanation2.pack(side=tk.TOP)
        
        # チェックボックス（0〜9の各点数）
        self.score_vars = {}
        checkbutton_font = ("Meiryo UI", 10)
        
        for i in range(10):
            self.score_vars[str(i)] = tk.BooleanVar(master=self.window)
            checkbutton = tk.Checkbutton(
                master=self.settings_frame,
                variable=self.score_vars[str(i)],
                text=str(i),
                font=checkbutton_font
            )
            checkbutton.pack(side=tk.TOP)
        
        # 進捗表示ラベル
        self.progress_var = tk.StringVar()
        self.progress_var.set("")
        
        progress_label = tk.Label(
            self.settings_frame,
            textvariable=self.progress_var,
            font=("Meiryo UI", 20)
        )
        progress_label.pack(side=tk.TOP)
        
        # 戻るボタン
        exit_button = tk.Button(
            self.settings_frame,
            text="トップに戻る\n保存はされません",
            height=3,
            width=15,
            command=self.exit_grading
        )
        exit_button.pack()
        
        # 採点実行ボタン
        self.grade_button = tk.Button(
            self.settings_frame,
            text="採点実行",
            height=3,
            width=15
        )
        self.grade_button.bind("<Button-1>", self.execute_grading)
        
        # キーボードイベントのバインド
        self.window.bind("<Key-Right>", self.next_image)
        self.window.bind("<Key-Left>", self.prev_image)
        self.window.bind("<Control-Key-p>", self.show_image_info)
        self.window.bind("<Key>", self.input_score)
    
    def _load_files(self) -> None:
        """問題フォルダから未採点ファイルを読み込みます"""
        # 問題ディレクトリのパス
        question_dir = os.path.join(SETTING_DIR, "output", self.question_id)
        print(f"問題ディレクトリ: {question_dir}")
        
        if not os.path.exists(question_dir):
            messagebox.showerror("エラー", f"問題ディレクトリが見つかりません: {question_dir}")
            self.window.destroy()
            return
        
        # ディレクトリ直下の（未採点の）ファイルのみを取得
        self.image_files = []
        self.filename_list = []
        
        for file in os.listdir(question_dir):
            file_path = os.path.join(question_dir, file)
            if os.path.isfile(file_path) and not file.startswith('.') and file.lower().endswith(('.jpg', '.jpeg', '.png')):
                self.image_files.append(file_path)
                self.filename_list.append(file)
        
        # ファイルを名前順にソート
        self.image_files.sort()
        self.filename_list.sort()
        
        if not self.image_files:
            messagebox.showinfo("完了", "すべてのファイルが採点済みです。")
            self.window.destroy()
            return
        
        print(f"読み込んだファイル数: {len(self.image_files)}")
        
        # 画像を読み込み
        self.tk_images = []
        for file_path in self.image_files:
            # 画像を読み込んでキャンバスサイズに合わせる
            try:
                img = Image.open(file_path)
                resized_img = resize_image_for_canvas(img, self.image_canvas, expand=True)
                
                # tkinter用の画像オブジェクトに変換
                tk_img = ImageTk.PhotoImage(image=resized_img, master=self.image_canvas)
                self.tk_images.append(tk_img)
            except Exception as e:
                print(f"画像の読み込みエラー: {file_path} - {e}")
                # エラーが発生した場合、ダミー画像を作成
                dummy_img = Image.new('RGB', (200, 100), color='red')
                tk_img = ImageTk.PhotoImage(dummy_img, master=self.image_canvas)
                self.tk_images.append(tk_img)
        
        # 最初の画像を表示
        self.current_index = 0
        self.update_display()
        
        # 採点ボタンを表示
        self.grade_button.pack(expand=True)
    
    def update_display(self) -> None:
        """現在の画像インデックスに基づいて表示を更新します"""
        if not self.tk_images:
            return
        
        # キャンバスの中心座標を計算
        canvas_width = int(self.image_canvas["width"])
        canvas_height = int(self.image_canvas["height"])
        center_x = canvas_width // 2
        center_y = canvas_height // 2
        
        # キャンバスをクリア
        self.image_canvas.delete("all")
        
        # 画像を表示
        self.image_canvas.create_image(
            center_x, center_y,
            image=self.tk_images[self.current_index],
            anchor=tk.CENTER
        )
        
        # ラベルを更新
        current_file = self.filename_list[self.current_index]
        self.filename_var.set(current_file)
        
        # 進捗表示を更新
        progress_text = f"{self.current_index + 1}/{len(self.filename_list)}"
        self.progress_var.set(progress_text)
        
        # スコア表示を更新
        current_path = self.image_files[self.current_index]
        if current_path in self.score_dict:
            self.score_var.set(self.score_dict[current_path])
        else:
            self.score_var.set("")
    
    def next_image(self, event=None) -> None:
        """次の画像を表示します"""
        if not self.tk_images or self.current_index >= len(self.tk_images) - 1:
            return
        
        self.current_index += 1
        self.update_display()
    
    def prev_image(self, event=None) -> None:
        """前の画像を表示します"""
        if not self.tk_images or self.current_index <= 0:
            return
        
        self.current_index -= 1
        self.update_display()
    
    def input_score(self, event) -> None:
        """キー入力に基づいて点数を設定します"""
        # 許可された点数のリストを更新
        self.allowed_scores = []
        for i in range(10):
            if self.score_vars[str(i)].get():
                self.allowed_scores.append(str(i))
        
        # キーボードからの入力がない場合は何もしない
        if not hasattr(event, 'keysym') or not event.keysym:
            return
            
        key = event.keysym
        
        # 画像ファイルがない場合は何もしない
        if not self.image_files or self.current_index >= len(self.image_files):
            return
            
        current_path = self.image_files[self.current_index]
        
        if key in self.allowed_scores:
            # 許可された数字キーが押された場合
            self.score_dict[current_path] = key
            print(f"スコア設定: {os.path.basename(current_path)} → {key}")
        elif key == "space":
            # スペースキーが押された場合
            self.score_dict[current_path] = "skip"
            print(f"スコア設定: {os.path.basename(current_path)} → skip")
        elif key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            # 許可されていない数字キーが押された場合
            self.score_dict[current_path] = "その点数は入力できません。\n右のチェックを確認してください。"
            print(f"無効なスコア: {key} - チェックボックスで許可されていません")
        else:
            # その他のキーが押された場合
            self.score_dict[current_path] = "そのキーは対応してません。"
            print(f"無効なキー: {key}")
        
        # スコア表示を更新
        if current_path in self.score_dict:
            self.score_var.set(self.score_dict[current_path])
    
    def show_image_info(self, event=None) -> None:
        """画像の情報を表示します（デバッグ用）"""
        if not self.image_files:
            return
        
        current_path = self.image_files[self.current_index]
        messagebox.showinfo("画像情報", f"パス: {current_path}")
    
    def execute_grading(self, event=None) -> None:
        """採点結果を保存します"""
        if not self.image_files:
            messagebox.showinfo("情報", "採点対象の画像がありません。")
            return
        
        success_count = 0
        for file_path, score in self.score_dict.items():
            # スコアが有効かどうかをチェック
            valid_score = False
            try:
                if score in self.allowed_scores:
                    valid_score = True
                elif score == "skip":
                    valid_score = True
            except:
                valid_score = False
            
            # 有効なスコアの場合のみ処理
            if valid_score:
                student_file = os.path.basename(file_path)
                question_dir = os.path.join(SETTING_DIR, "output", self.question_id)
                original_path = os.path.join(question_dir, student_file)
                
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
        else:
            messagebox.showinfo("採点保存", "採点対象がありませんでした。")
        
        # ウィンドウを閉じる
        self.window.destroy()
    
    def exit_grading(self) -> None:
        """採点を中断してトップ画面に戻ります"""
        ret = messagebox.askyesno('終了します', '採点を中断し、ホームに戻っても良いですか？')
        if ret:
            # 模範解答ウィンドウが開いていれば閉じる
            if self.sample_window and self.sample_window.winfo_exists():
                self.sample_window.destroy()
            self.window.destroy()
    
    def on_closing(self) -> None:
        """ウィンドウを閉じる際の処理"""
        # 模範解答ウィンドウが開いていれば閉じる
        if self.sample_window and self.sample_window.winfo_exists():
            self.sample_window.destroy()
        self.exit_grading()
    
    def show_sample_answer(self, event=None) -> None:
        """模範解答を別ウィンドウで表示します"""
        if not self.has_sample_answer:
            messagebox.showinfo("情報", "この問題の模範解答は登録されていません。")
            return
        
        try:
            # すでにウィンドウが開いている場合は前面表示して終了
            if self.sample_window and self.sample_window.winfo_exists():
                self.sample_window.lift()
                return
                
            # 模範解答画像のパスを取得
            answer_output_dir = os.path.join(ANSWER_DATA_DIR, "output", self.question_id)
            
            if not os.path.exists(answer_output_dir):
                messagebox.showinfo("情報", "模範解答が見つかりません。")
                return
                
            answer_files = [os.path.join(answer_output_dir, f) for f in os.listdir(answer_output_dir) 
                          if os.path.isfile(os.path.join(answer_output_dir, f)) and 
                          f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                
            if not answer_files:
                messagebox.showinfo("情報", "模範解答画像が見つかりません。")
                return
                
            # 画像を読み込み
            self.sample_original_img = Image.open(answer_files[0])
            img = self.sample_original_img.copy()
            
            # 画像サイズを取得（ウィンドウサイズ決定用）
            img_width, img_height = img.size
            
            # 画面の解像度を取得
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # 画像が大きすぎる場合はリサイズ
            if img_width > screen_width * 0.8 or img_height > screen_height * 0.8:
                ratio = min((screen_width * 0.8) / img_width, (screen_height * 0.8) / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img_width, img_height = new_width, new_height
                self.sample_scale = ratio  # 縮小率を保存
            else:
                self.sample_scale = 1.0
            
            # 模範解答表示ウィンドウを作成
            self.sample_window = tk.Toplevel(self.window)
            self.sample_window.title(f"模範解答 - {self.question_id}")
            
            # ウィンドウ位置を設定（親ウィンドウの隣に表示）
            window_x = self.window.winfo_x() + self.window.winfo_width() + 10
            window_y = self.window.winfo_y()
            
            # ウィンドウサイズを画像に合わせて設定（コントロールボタン用に余裕を持たせる）
            self.sample_window.geometry(f"{img_width}x{img_height + 80}+{window_x}+{window_y}")
            self.sample_window.minsize(300, 200)  # 最小サイズを設定
            
            # キャンバスフレーム
            canvas_frame = tk.Frame(self.sample_window)
            canvas_frame.pack(fill=tk.BOTH, expand=True)
            
            # 表示用のキャンバス
            canvas = tk.Canvas(
                canvas_frame,
                bg="black",
                width=img_width,
                height=img_height
            )
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # tkinter用の画像オブジェクトに変換
            self.sample_tk_img = ImageTk.PhotoImage(img)
            
            # 画像をキャンバスの中央に配置
            self.canvas_img_id = canvas.create_image(
                img_width // 2, 
                img_height // 2, 
                image=self.sample_tk_img,
                anchor=tk.CENTER
            )
            
            # ウィンドウサイズ変更イベント
            def on_resize(event):
                # キャンバスの中心に画像を再配置
                canvas.coords(
                    self.canvas_img_id, 
                    event.width // 2,
                    event.height // 2
                )
            
            canvas.bind("<Configure>", on_resize)
            
            # コントロールフレーム
            control_frame = tk.Frame(self.sample_window, height=50)
            control_frame.pack(fill=tk.X, pady=5)
            
            # 拡大ボタン
            zoom_in_btn = tk.Button(
                control_frame,
                text="拡大 (+)",
                command=lambda: self._resize_sample_image(canvas, 1.2),
                width=8
            )
            zoom_in_btn.pack(side=tk.LEFT, padx=10)
            
            # 縮小ボタン
            zoom_out_btn = tk.Button(
                control_frame,
                text="縮小 (-)",
                command=lambda: self._resize_sample_image(canvas, 0.8),
                width=8
            )
            zoom_out_btn.pack(side=tk.LEFT, padx=5)
            
            # 元のサイズに戻すボタン
            reset_btn = tk.Button(
                control_frame,
                text="リセット",
                command=lambda: self._reset_sample_image(canvas),
                width=8
            )
            reset_btn.pack(side=tk.LEFT, padx=5)
            
            # スケール表示
            self.scale_var = tk.StringVar()
            self.scale_var.set(f"倍率: {self.sample_scale:.1f}x")
            scale_label = tk.Label(
                control_frame,
                textvariable=self.scale_var,
                font=("Meiryo UI", 9)
            )
            scale_label.pack(side=tk.LEFT, padx=10)
            
            # 閉じるボタン
            close_button = tk.Button(
                control_frame,
                text="閉じる",
                command=self.sample_window.destroy,
                width=8
            )
            close_button.pack(side=tk.RIGHT, padx=10)
            
            # 非モーダル表示（親ウィンドウも操作可能に）
            self.sample_window.transient(self.window)
            
            # キーボードショートカット
            self.sample_window.bind("<plus>", lambda e: self._resize_sample_image(canvas, 1.2))
            self.sample_window.bind("<minus>", lambda e: self._resize_sample_image(canvas, 0.8))
            self.sample_window.bind("<0>", lambda e: self._reset_sample_image(canvas))
            
        except Exception as e:
            messagebox.showerror("エラー", f"模範解答の表示中にエラーが発生しました：{e}")
    
    def _resize_sample_image(self, canvas, factor: float) -> None:
        """
        模範解答画像のサイズを変更します
        
        Args:
            canvas: 画像を表示しているキャンバス
            factor: サイズ変更係数（1.0より大きいと拡大、小さいと縮小）
        """
        if self.sample_original_img is None:
            return
        
        # 新しいスケールを計算
        new_scale = self.sample_scale * factor
        
        # スケールが極端に小さくなりすぎないよう制限
        if new_scale < 0.1:
            new_scale = 0.1
        # スケールが極端に大きくなりすぎないよう制限
        elif new_scale > 5.0:
            new_scale = 5.0
            
        # 実際のスケール変更が行われる場合のみ処理
        if new_scale != self.sample_scale:
            self.sample_scale = new_scale
            
            # オリジナル画像からリサイズ
            orig_width, orig_height = self.sample_original_img.size
            new_width = int(orig_width * self.sample_scale)
            new_height = int(orig_height * self.sample_scale)
            
            # リサイズした画像を作成
            resized_img = self.sample_original_img.resize(
                (new_width, new_height), 
                Image.Resampling.LANCZOS
            )
            
            # 新しい画像をセット
            self.sample_tk_img = ImageTk.PhotoImage(resized_img)
            canvas.itemconfig(self.canvas_img_id, image=self.sample_tk_img)
            
            # スケール表示を更新
            self.scale_var.set(f"倍率: {self.sample_scale:.1f}x")
    
    def _reset_sample_image(self, canvas) -> None:
        """模範解答画像を元のサイズにリセットします"""
        # 画面サイズを考慮した適切な初期スケールを計算
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        orig_width, orig_height = self.sample_original_img.size
        
        if orig_width > screen_width * 0.8 or orig_height > screen_height * 0.8:
            # 画面の80%を超えるサイズは縮小
            init_scale = min((screen_width * 0.8) / orig_width, (screen_height * 0.8) / orig_height)
        else:
            # それ以外は等倍
            init_scale = 1.0
            
        # スケールを設定してリサイズ
        self.sample_scale = init_scale
        self._resize_sample_image(canvas, 1.0)  # 現在のスケールで再描画