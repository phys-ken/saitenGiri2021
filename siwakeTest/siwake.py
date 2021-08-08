##　自分メモ
# saitenGiriGiriからフォルダ名を受けて、表示する
# Enter 押したら次にする
# siwakeを実行した後に画面を閉じる。

## できたら
# 押してもいいリストを作る
# 数字に連動して、canvasに○、△、×を表示する。



import pathlib
import os
import shutil

import tkinter
from tkinter import Label, Tk, StringVar

from PIL import Image, ImageTk  # 外部ライブラリ



def folder_walker(folder_path, recursive = False, file_ext = ".*"):
    """
    指定されたフォルダのファイル一覧を取得する。
    引数を指定することで再帰的にも、非再帰的にも取得可能。

    Parameters
    ----------
    folder_path : str
        対象のフォルダパス
    recursive : bool
        再帰的に取得するか否か。既定値はTrueで再帰的に取得する。
    file_ext : str
        読み込むファイルの拡張子を指定。例：".jpg"のようにピリオドが必要。既定値は".*"で指定なし
    """

    p = pathlib.Path(folder_path)

    if recursive:
        return list(p.glob("**/*" + file_ext))  # **/*で再帰的にファイルを取得
    else:
        return list(p.glob("*" + file_ext))  # 再帰的にファイル取得しない


# ファイル読み込み - - - - - - - - - - - - - - - - - - - - - - - -
def load_file(Qnum):

    global img_num, item, dir_name

    # ファイルを読み込み
    tex_var.set("ファイルを読み込んでいます...")
    dir_name = "../setting/output/" + Qnum
    if not dir_name == None:
        file_list = folder_walker(dir_name)

    # ファイルから読み込める画像をリストに列挙
    for f in file_list:
        try:
            img_lst.append(Image.open(f))
            filename_lst.append(f)
        except:
            pass
    
    if not img_lst:
            tex_var.set("読み込む画像がありません。\n採点は終了しています。")

    # ウィンドウサイズに合わせてキャンバスサイズを再定義
    # window_resize()

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
        c_width_half, c_height_half,  image=tk_img_lst[0], anchor=tkinter.CENTER)
    # ラベルの書き換え
    tex_var.set(filename_lst[img_num])

 
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
        # skipは、無視する。
        print(assort_dict[f])
        if not assort_dict[f] == "skip":
            f_dir = os.path.dirname(f)
            f_basename = os.path.basename(f)
            new_dir = os.path.join(f_dir, assort_dict[f])
            new_path = os.path.join(new_dir, f_basename)

            # ディレクトリの存在チェック
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            # ファイルの移動実行
            shutil.move(f, new_path)

            print(new_path)
        else:
            pass
    siwake_win.destroy()

def siwakeApp():
    # グローバル変数
    global img_lst, tk_img_lst 
    global filename_lst
    global assort_file_list
    global assort_dict

    global tex_var
    global image_canvas
    global assort_btn
    global assort_t_var

    global img_num
    global f_basename
    global siwake_win

    img_lst, tk_img_lst = [], []
    filename_lst = []
    assort_file_list = []
    assort_dict = {}

    img_num = 0
    f_basename = ""

    siwake_win = tkinter.Tk()
    siwake_win.title("採点中...")
    siwake_win.geometry("800x800")
    siwake_frame = tkinter.Frame(siwake_win)
    siwake_frame.grid(column=0,row=0)

    # キャンバス描画設定
    image_canvas = tkinter.Canvas(siwake_frame,
                             width=640,
                             height=480)

    image_canvas.pack(expand=True, fill="both")

    # 仕分け結果表示
    assort_t_var = tkinter.StringVar(siwake_frame)
    assort_label = tkinter.Label(
        siwake_frame, textvariable=assort_t_var, font=("Meiryo UI", 30))
    assort_label.pack()

    # ファイル名ラベル描画設定
    tex_var = tkinter.StringVar(siwake_frame)
    tex_var.set("ファイル名")

    lbl = tkinter.Label(siwake_frame, textvariable=tex_var, font=("Meiryo UI", 10))
    lbl["foreground"] = "gray"
    lbl.pack()

    # 右左キーで画像送りする動作設定
    siwake_win.bind("<Key-Right>", next_img)
    siwake_win.bind("<Key-Left>", prev_img)
    # 「Ctrl」+「P」で画像表示
    siwake_win.bind("<Control-Key-p>", image_show)

    # 数字キーで仕分け対象設定
    siwake_win.bind("<Key>", file_assort)

    # 仕分け実行ボタン
    assort_btn = tkinter.Button(siwake_frame, text="仕分け実行")
    assort_btn.bind("<Button-1>", assort_go)


    # 読み込みボタン描画設定
    load_file("Q_0002")

    siwake_win.mainloop

# メイン処理 -------------------------------------------------------
if __name__ == "__main__":



    # tkinter描画設定
    root = tkinter.Tk()

    root.title(u"表示・仕分けツール")
    root.option_add("*font", ("Meiryo UI", 11))
    root.geometry("200x200")

    # 仕分け実行ボタン
    siwake_btn = tkinter.Button(root, text="仕分け実行" , command= siwakeApp).pack()
    
    


    root.mainloop()