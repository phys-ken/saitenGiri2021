##　自分メモ
# Q_000nより深い階層に潜り込まないようにする。
# saitenGiriGiriからフォルダ名を受けて、表示する
# Enter 押したら次にする
# siwakeを実行した後に画面を閉じる。

## できたら
# 押してもいいリストを作る
# 数字に連動して、canvasに○、△、×を表示する。



from file_walker import folder_walker  # 自作関数
from folder_selector import file_selector  # 自作関数

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import Label, Tk, StringVar

from PIL import Image, ImageTk  # 外部ライブラリ


# ファイル読み込み - - - - - - - - - - - - - - - - - - - - - - - -
def load_file(event):

    global img_num, item, dir_name

    # ファイルを読み込み
    tex_var.set("ファイルを読み込んでいます...")
    dir_name = "../setting/output/Q_0007"
    if not dir_name == None:
        file_list = folder_walker(dir_name)

    # ファイルから読み込める画像をリストに列挙
    for f in file_list:
        try:
            img_lst.append(Image.open(f))
            filename_lst.append(f)
        except:
            pass

    # ウィンドウサイズに合わせてキャンバスサイズを再定義
    window_resize()

    # 画像変換
    for f in img_lst:

        # キャンバス内に収まるようリサイズ
        resized_img = img_resize_for_canvas(f, image_canvas)

        # tkinterで表示できるように画像変換
        tk_img_lst.append(ImageTk.PhotoImage(
            image=resized_img, master=image_canvas))

    # キャンバスの中心を取得
    c_width_half = round(int(image_canvas["width"]) / 2)
    c_height_half = round(int(image_canvas["height"]) / 2)

    # キャンバスに表示
    img_num = 0
    item = image_canvas.create_image(
        c_width_half, c_height_half,  image=tk_img_lst[0], anchor=tk.CENTER)
    # ラベルの書き換え
    tex_var.set(filename_lst[img_num])

    # 読み込みボタンの非表示
    load_btn.pack_forget()
    # 仕分け実行ボタンの配置
    assort_btn.pack()

# 次の画像へ - - - - - - - - - - - - - - - - - - - - - - - -
def next_img(event):
    global img_num

    # 読み込んでいる画像の数を取得
    img_count = len(tk_img_lst)

    # 画像が最後でないか判定
    if img_num >= img_count - 1:
        pass
    else:
        # 表示中の画像No.を更新して表示
        img_num += 1
        image_canvas.itemconfig(item, image=tk_img_lst[img_num])
        # ラベルの書き換え
        tex_var.set(filename_lst[img_num])
        # ラベリングを表示
        if filename_lst[img_num] in assort_dict:
            assort_t_var.set(assort_dict[filename_lst[img_num]])
        else:
            assort_t_var.set("")


# 前の画像へ - - - - - - - - - - - - - - - - - - - - - - - -
def prev_img(event):
    global img_num

    # 画像が最初でないか判定
    if img_num <= 0:
        pass
    else:
        # 表示中の画像No.を更新して表示
        img_num -= 1
        image_canvas.itemconfig(item, image=tk_img_lst[img_num])
        # ラベルの書き換え
        tex_var.set(filename_lst[img_num])
        # ラベリングを表示
        if filename_lst[img_num] in assort_dict:
            assort_t_var.set(assort_dict[filename_lst[img_num]])
        else:
            assort_t_var.set("")


# ウィンドウサイズからキャンバスサイズを再定義 - - - - - - - - - - - - - - - - -
def window_resize():

    image_canvas["width"] = image_canvas.winfo_width()
    image_canvas["height"] = image_canvas.winfo_height()


# キャンバスサイズに合わせて画像を縮小 - - - - - - - - - - - - - - - - - - - -
def img_resize_for_canvas(img, canvas, expand=False):

    size_retio_w = int(canvas["width"]) / img.width
    size_retio_h = int(canvas["height"]) / img.height

    if expand == True:
        size_retio = min(size_retio_w, size_retio_h)
    else:
        size_retio = min(size_retio_w, size_retio_h, 1)

    resized_img = img.resize((round(img.width * size_retio),
                              round(img.height * size_retio)))
    return resized_img

# 画像表示 - - - - - - - - - - - - - - - - - - - - - - - -
def image_show(event):
    img_lst[img_num].show()


# 画像に対しラベリング - - - - - - - - - - - - - - - - - - - - - - - -
def file_assort(event):

    if str(event.keysym) in ["0","1", "2", "3", "4", "5", "6", "7", "8", "9"]:
        assort_dict[filename_lst[img_num]] = str(event.keysym)
    else:
        assort_dict[filename_lst[img_num]] = str("skip")

    # ラベリングを表示
    if filename_lst[img_num] in assort_dict:
        assort_t_var.set(assort_dict[filename_lst[img_num]])
    else:
        assort_t_var.set("")

    print(assort_dict[filename_lst[img_num]])


# フォルダ分け実行 - - - - - - - - - - - - - - - - - - - - - - - -
def assort_go(event):

    global f_dir

    for f in assort_dict:
        # 仕分け前後のファイル名・フォルダ名を取得
        f_dir = os.path.dirname(f)
        f_basename = os.path.basename(f)
        new_dir = os.path.join(f_dir, assort_dict[f])
        new_path = os.path.join(new_dir, f_basename)

        # ディレクトリの存在チェック
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
        # ファイルの移動実行
        shutil.move(f, new_path)
        assort_btn.pack_forget()

        print(new_path)

# フォルダーを開く - - - - - - - - - - - - - - - - - - - - - - - -
def folder_open(event):
    # パスをエクスプローラーで開けるように変換
    open_dir_name = f_dir.replace("/", "\\")
    # エクスプローラーで開く
    subprocess.Popen(['explorer', open_dir_name])
    # tkinterウィンドウを閉じる
    root.destroy()

    print(open_dir_name)


# メイン処理 -------------------------------------------------------
if __name__ == "__main__":

    # グローバル変数
    img_lst, tk_img_lst = [], []
    filename_lst = []
    assort_file_list = []
    assort_dict = {}

    img_num = 0
    f_basename = ""

    # tkinter描画設定
    root = tk.Tk()

    root.title(u"表示・仕分けツール")
    root.option_add("*font", ("Meiryo UI", 11))

    # 読み込みボタン描画設定
    load_btn = tk.Button(root, text="読み込み")
    load_btn.bind("<Button-1>", load_file)
    load_btn.pack()

    # キャンバス描画設定
    image_canvas = tk.Canvas(root,
                             width=640,
                             height=480)

    image_canvas.pack(expand=True, fill="both")

    # 仕分け結果表示
    assort_t_var = tk.StringVar()
    assort_label = tk.Label(
        root, textvariable=assort_t_var, font=("Meiryo UI", 14))
    assort_label.pack()

    # ファイル名ラベル描画設定
    tex_var = tk.StringVar()
    tex_var.set("ファイル名")

    lbl = tk.Label(root, textvariable=tex_var, font=("Meiryo UI", 8))
    lbl["foreground"] = "gray"
    lbl.pack()

    # 右左キーで画像送りする動作設定
    root.bind("<Key-Right>", next_img)
    root.bind("<Key-Left>", prev_img)
    # 「Ctrl」+「P」で画像表示
    root.bind("<Control-Key-p>", image_show)

    # 数字キーで仕分け対象設定
    root.bind("<Key>", file_assort)

    # 仕分け実行ボタン
    assort_btn = tk.Button(root, text="仕分け実行")
    assort_btn.bind("<Button-1>", assort_go)

    # フォルダを開くボタン
    open_folder_btn = tk.Button(root,text="フォルダーを開く")
    open_folder_btn.bind("<Button-1>", folder_open)

    root.mainloop()