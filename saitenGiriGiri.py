import tkinter
from tkinter import messagebox
from PIL import Image, ImageTk  # 外部ライブラリ
import csv
import glob
import os
import sys
import shutil

RESIZE_RETIO = 3  # 縮小倍率の規定

global qCnt
qCnt = 0

# 初回起動時にフォルダを展開する。
def initDir():
  os.makedirs("./setting/input", exist_ok=True)
  os.makedirs("./setting/output", exist_ok=True)
  f = open('setting/ini.csv', 'w')    #既存でないファイル名を作成してください
  writer = csv.writer(f, lineterminator='\n') # 行末は改行
  writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y" ])
  f.close()


# 与えられたフォルダの全てのファイル(フルパス)をソートしてリストで返す
def get_sorted_files(dir_path):
    return sorted(glob.glob(dir_path))


# ドラッグ開始した時のイベント - - - - - - - - - - - - - - - - - - - - - - - - - -
def start_point_get(event):
    global start_x, start_y  # グローバル変数に書き込みを行なうため宣言

    canvas1.delete("rectTmp")  # すでに"rectTmp"タグの図形があれば削除

    # canvas1上に四角形を描画（rectangleは矩形の意味）
    canvas1.create_rectangle(event.x,
                             event.y,
                             event.x + 1,
                             event.y + 1,
                             outline="red",
                             tag="rectTmp")
    # グローバル変数に座標を格納
    start_x, start_y = event.x, event.y

# ドラッグ中のイベント - - - - - - - - - - - - - - - - - - - - - - - - - -


def rect_drawing(event):

    # ドラッグ中のマウスポインタが領域外に出た時の処理
    if event.x < 0:
        end_x = 0
    else:
        end_x = min(img_resized.width, event.x)
    if event.y < 0:
        end_y = 0
    else:
        end_y = min(img_resized.height, event.y)

    # "rectTmp"タグの画像を再描画
    canvas1.coords("rectTmp", start_x, start_y, end_x, end_y)

# ドラッグを離したときのイベント - - - - - - - - - - - - - - - - - - - - - - - - - -


def release_action(event):
    global qCnt

    if qCnt == 0:
      pos = canvas1.bbox("rectTmp")
      # canvas1上に四角形を描画（rectangleは矩形の意味）
      create_rectangle_alpha(pos[0], pos[1], pos[2], pos[3],
                            fill="green",
                            alpha=0.3,
                            tag = "nameBox"
                            )
      canvas1.create_text(
          (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2,
          text="name",
          tag = "nameText"
      )

      # "rectTmp"タグの画像の座標を元の縮尺に戻して取得
      start_x, start_y, end_x, end_y = [
          round(n * RESIZE_RETIO) for n in canvas1.coords("rectTmp")
      ]
      with open('setting/ini.csv', 'a') as f:
        writer = csv.writer(f, lineterminator='\n') # 行末は改行
        writer.writerow(["name" , start_x, start_y, end_x, end_y ])

    else:
      pos = canvas1.bbox("rectTmp")
      # canvas1上に四角形を描画（rectangleは矩形の意味）
      create_rectangle_alpha(pos[0], pos[1], pos[2], pos[3],
                            fill="red",
                            alpha=0.3,
                            tag = "qBox" + str(qCnt)
                            )
      canvas1.create_text(
          (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2,
          text="Q_" + str(qCnt),
          tag = "qText" + str(qCnt)
      )

      # "rectTmp"タグの画像の座標を元の縮尺に戻して取得
      start_x, start_y, end_x, end_y = [
          round(n * RESIZE_RETIO) for n in canvas1.coords("rectTmp")
      ]
      with open('setting/ini.csv', 'a') as f:
        writer = csv.writer(f, lineterminator='\n') # 行末は改行
        writer.writerow(["Q_" + str(qCnt) , start_x, start_y, end_x, end_y ])

    qCnt = qCnt + 1


# 透過画像の作成 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# https://stackoverflow.com/questions/54637795/how-to-make-a-tkinter-canvas-rectangle-transparent/54645103
# 透過画像を削除するときは、imagesの配列から消す。
images = []  # to hold the newly created image

def create_rectangle_alpha(x1, y1, x2, y2, **kwargs):
    if 'alpha' in kwargs:
        alpha = int(kwargs.pop('alpha') * 255)
        fill = kwargs.pop('fill')
        fill = root.winfo_rgb(fill) + (alpha,)
        image = Image.new('RGBA', (x2-x1, y2-y1), fill)
        images.append(ImageTk.PhotoImage(image))
        canvas1.create_image(x1, y1, image=images[-1], anchor='nw')
    canvas1.create_rectangle(x1, y1, x2, y2, **kwargs)

def back_one():
  global qCnt
  if qCnt ==  0:
    return
  qCnt = qCnt - 1
  ## タグに基づいて画像を削除
  if qCnt == 0:
    canvas1.delete("nameBox", "nameText","rectTmp")
    images.pop(-1)
  else:
    canvas1.delete("qBox" + str(qCnt) , "qText" + str(qCnt) , "rectTmp")
    images.pop(-1)
  ## csvの最終行を削除
  readFile = open("setting/ini.csv")
  lines = readFile.readlines()
  readFile.close()
  w = open("setting/ini.csv",'w')
  w.writelines([item for item in lines[:-1]])
  w.close()

def trim_fin():
  ret = messagebox.askyesno('終了します', '現在のデータを保存し、ウィンドウを閉じますか？')
  if ret == True:
    cur = os.getcwd()
    beforePath = cur + "/setting/ini.csv"
    afterPath = cur + "/setting/trimData.csv"
    shutil.move(beforePath,afterPath)
    sys.exit()





# メイン処理 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == "__main__":

    # 同じ場所にsettingがあるか調べる。無ければ、作るかどうか聞く。
    if not os.path.exists("./setting/"):
      ret = messagebox.askyesno('初回起動です', '採点のために、いくつかのフォルダーをこのファイルと同じ場所に作成します。よろしいですか？')
      if ret == True:
        initDir()
        messagebox.showinfo('準備ができました。', '解答用紙を、setting/input の中に保存してください。jpeg または png に対応しています。')
        sys.exit()
      else:
        # メッセージボックス（情報） 
        messagebox.showinfo('終了', 'アプリを終了します。')
        sys.exit()      

    # 表示する画像の取得
    files = get_sorted_files(os.getcwd() + "/setting/input/*")

    if not files:
      # メッセージボックス（警告） 
      messagebox.showerror("エラー", "setting/inputの中に、解答用紙のデータが存在しません。画像を入れてから、また開いてね。")
      sys.exit()

    # ini.csvは、起動のたびに初期化する。
    f = open('setting/ini.csv', 'w')    #既存でないファイル名を作成してください
    writer = csv.writer(f, lineterminator='\n') # 行末は改行
    writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y" ])
    f.close()


    img = Image.open(files[0])

    # スクリーンショットした画像は表示しきれないので画像リサイズ
    img_resized = img.resize(size=(int(img.width / RESIZE_RETIO),
                                   int(img.height / RESIZE_RETIO)),
                             resample=Image.BILINEAR)

    root = tkinter.Tk()
    root.title("採点ギリギリ")

    ## csvを元に、とりあえず解答用紙に枠を作る。


    #戻るボタン
    backB = tkinter.Button(
          root, text = '一つ戻る' , command = back_one).pack(side = tkinter.RIGHT)


    #入力完了
    finB = tkinter.Button(
          root, text = '入力完了' , command = trim_fin).pack(side = tkinter.RIGHT)


    # tkinterで表示できるように画像変換
    img_tk = ImageTk.PhotoImage(img_resized)

    # Canvasウィジェットの描画
    canvas1 = tkinter.Canvas(root,
                             bg="black",
                             width=img_resized.width,
                             height=img_resized.height)
    # Canvasウィジェットに取得した画像を描画
    canvas1.create_image(0, 0, image=img_tk, anchor=tkinter.NW)

    # Canvasウィジェットを配置し、各種イベントを設定
    canvas1.pack()
    canvas1.bind("<ButtonPress-1>", start_point_get)
    canvas1.bind("<Button1-Motion>", rect_drawing)
    canvas1.bind("<ButtonRelease-1>", release_action)

    root.mainloop()
