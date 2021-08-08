import tkinter
from tkinter import messagebox
from PIL import Image, ImageTk  # 外部ライブラリ
import csv
import glob
import os
import sys
import shutil

global canvas1
global img_resized
global img_tk
global Giri_cutter
global root
global topimg
global topfig

global RESIZE_RETIO  # 縮小倍率の規定
window_h = 700
window_w = int(window_h * 1.7)
fig_area_w = int(window_h * 1)

global qCnt
qCnt = 0


# 初回起動時にフォルダを展開する。
def initDir():
    os.makedirs("./setting/input", exist_ok=True)
    os.makedirs("./setting/output", exist_ok=True)
    f = open('setting/ini.csv', 'w')  # 既存でないファイル名を作成してください
    writer = csv.writer(f, lineterminator='\n')  # 行末は改行
    writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y"])
    f.close()


# 与えられたフォルダの全てのファイル(フルパス)をソートしてリストで返す
# 拡張子が画像かどうかも判別し、画像のパスのみを返す。
def get_sorted_files(dir_path):
    all_sorted = sorted(glob.glob(dir_path))
    fig_sorted = [s for s in all_sorted if s.endswith(
        ('jpg', "jpeg", "png", "PNG", "JPEG", "JPG", "gif"))]
    return fig_sorted


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
                               tag="nameBox"
                               )

        canvas1.create_text(
            (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2,
            text="name",
            tag="nameText"
        )

        # "rectTmp"タグの画像の座標を元の縮尺に戻して取得
        start_x, start_y, end_x, end_y = [
            round(n * RESIZE_RETIO) for n in canvas1.coords("rectTmp")
        ]
        with open('setting/ini.csv', 'a') as f:
            writer = csv.writer(f, lineterminator='\n')  # 行末は改行
            writer.writerow(["name", start_x, start_y, end_x, end_y])

    else:
        pos = canvas1.bbox("rectTmp")
        # canvas1上に四角形を描画（rectangleは矩形の意味）
        create_rectangle_alpha(pos[0], pos[1], pos[2], pos[3],
                               fill="red",
                               alpha=0.3,
                               tag="qBox" + str(qCnt)
                               )
        canvas1.create_text(
            (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2,
            text="Q_" + str(qCnt),
            tag="qText" + str(qCnt)
        )

        # "rectTmp"タグの画像の座標を元の縮尺に戻して取得
        start_x, start_y, end_x, end_y = [
            round(n * RESIZE_RETIO) for n in canvas1.coords("rectTmp")
        ]
        with open('setting/ini.csv', 'a') as f:
            writer = csv.writer(f, lineterminator='\n')  # 行末は改行
            writer.writerow(["Q_" + str(qCnt).zfill(4),
                            start_x, start_y, end_x, end_y])

    qCnt = qCnt + 1


# 透過画像の作成 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# https://stackoverflow.com/questions/54637795/how-to-make-a-tkinter-canvas-rectangle-transparent/54645103
# 透過画像を削除するときは、imagesの配列から消す。
images = []  # to hold the newly created image


def create_rectangle_alpha(x1, y1, x2, y2, **kwargs):
    if 'alpha' in kwargs:
        alpha = int(kwargs.pop('alpha') * 255)
        fill = kwargs.pop('fill')
        fill = Giri_cutter.winfo_rgb(fill) + (alpha,)
        image = Image.new('RGBA', (x2-x1, y2-y1), fill)
        images.append(ImageTk.PhotoImage(image, master=Giri_cutter))
        canvas1.create_image(x1, y1, image=images[-1], anchor='nw')
    canvas1.create_rectangle(x1, y1, x2, y2, **kwargs)


def back_one():
    global qCnt
    if qCnt == 0:
        return
    qCnt = qCnt - 1
    # タグに基づいて画像を削除
    if qCnt == 0:
        canvas1.delete("nameBox", "nameText", "rectTmp")
        images.pop(-1)
    else:
        canvas1.delete("qBox" + str(qCnt), "qText" + str(qCnt), "rectTmp")
        images.pop(-1)
    # csvの最終行を削除
    readFile = open("setting/ini.csv")
    lines = readFile.readlines()
    readFile.close()
    w = open("setting/ini.csv", 'w')
    w.writelines([item for item in lines[:-1]])
    w.close()


def trim_fin():
    global Giri_cutter
    ret = messagebox.askyesno('終了します', '斬り方を決定し、ホームに戻っても良いですか？')
    if ret == True:
        cur = os.getcwd()
        beforePath = cur + "/setting/ini.csv"
        afterPath = cur + "/setting/trimData.csv"
        shutil.move(beforePath, afterPath)
        Giri_cutter.destroy()


def setting_ck():
    if not os.path.exists("./setting/"):
        ret = messagebox.askyesno(
            '初回起動です', '採点のために、いくつかのフォルダーをこのファイルと同じ場所に作成します。\nよろしいですか？')
        if ret == True:
            initDir()
            messagebox.showinfo(
                '準備ができました。', '解答用紙を、setting/input の中に保存してください。jpeg または png に対応しています。')
        else:
            # メッセージボックス（情報）
            messagebox.showinfo('終了', 'フォルダは作成しません。')
    else:
        messagebox.showinfo(
            '確認', '初期設定は完了しています。解答用紙を、setting/inputに入れてから、解答用紙分割をしてください。')


def input_ck():
    # 表示する画像の取得
    files = get_sorted_files(os.getcwd() + "/setting/input/*")
    if not files:
        # メッセージボックス（警告）
        messagebox.showerror(
            "エラー", "setting/inputの中に、解答用紙のデータが存在しません。画像を入れてから、また開いてね。")
    else:
        GiriActivate()


def GiriActivate():
    global RESIZE_RETIO
    global img_resized
    global canvas1
    global img_tk
    global Giri_cutter

    def toTop():
        ret = messagebox.askyesno(
            '保存しません', '作業中のデータは保存されません。\n画面を移動しますか？')
        if ret == True:
            Giri_cutter.destroy()
        else:
            pass

    # 表示する画像の取得
    files = get_sorted_files(os.getcwd() + "/setting/input/*")
    print(files)

    # ini.csvは、起動のたびに初期化する。
    f = open('setting/ini.csv', 'w')  # 既存でないファイル名を作成してください
    writer = csv.writer(f, lineterminator='\n')  # 行末は改行
    writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y"])
    f.close()

    img = Image.open(files[0])

    # 画面サイズに合わせて画像をリサイズする
    # 画像サイズが縦か横かに合わせて、RESIZE_RETIOを決める。
    w, h = img.size
    if w >= h:
        if w <= fig_area_w:
            RESIZE_RETIO = 1
        else:
            RESIZE_RETIO = w / fig_area_w
    else:
        if h <= window_h:
            RESIZE_RETIO = 1
        else:
            RESIZE_RETIO = h / window_h

    # 画像リサイズ
    img_resized = img.resize(size=(int(img.width / RESIZE_RETIO),
                                   int(img.height / RESIZE_RETIO)),
                             resample=Image.BILINEAR)

    Giri_cutter = tkinter.Tk()
    Giri_cutter.geometry(str(window_w) + "x" + str(window_h))
    Giri_cutter.title("解答用紙を斬る")

    cutting_frame = tkinter.Frame(Giri_cutter)
    cutting_frame.pack()
    canvas_frame = tkinter.Frame(cutting_frame)
    canvas_frame.grid(column=0, row=0)
    button_frame = tkinter.Frame(cutting_frame)
    button_frame.grid(column=1, row=0)

    # tkinterで表示できるように画像変換
    img_tk = ImageTk.PhotoImage(img_resized, master=Giri_cutter)

    # Canvasウィジェットの描画
    canvas1 = tkinter.Canvas(canvas_frame,
                             bg="black",
                             width=img_resized.width,
                             height=img_resized.height,
                             highlightthickness=0)
    # Canvasウィジェットに取得した画像を描画
    canvas1.create_image(0, 0, image=img_tk, anchor=tkinter.NW)

    # Canvasウィジェットを配置し、各種イベントを設定
    canvas1.pack()

    # 戻るボタン
    backB = tkinter.Button(
        button_frame, text='一つ前に戻る', command=back_one , width = 10 ,height = 4).pack()

    # 入力完了
    finB = tkinter.Button(
        button_frame, text='入力完了\n(保存して戻る)', command=trim_fin , width = 10 ,height = 4).pack()
    topB = tkinter.Button(
        button_frame, text='topに戻る\n(保存はされません)', command=toTop , width = 10 ,height = 4).pack()

    canvas1.bind("<ButtonPress-1>", start_point_get)
    canvas1.bind("<Button1-Motion>", rect_drawing)
    canvas1.bind("<ButtonRelease-1>", release_action)
    Giri_cutter.mainloop()


def trimck():
        ret = messagebox.askyesno(
            'すべての解答用紙を斬っちゃいます。', '全員の解答用紙を、斬ります。\n以下の注意を読んで、よければ始めてください。\n①10分くらい時間がかかります。\n②inputに保存された画像は、削除されません。\n③現在のoutputは全て消えます。')
        if ret == True:
            allTrim()
        else:
            pass


def allTrim():
    # トリミング前の画像の格納先
    ORIGINAL_FILE_DIR = "./setting/input"
    # トリミング後の画像の格納先
    TRIMMED_FILE_DIR = "./setting/output"

    def trim(path, left, top, right, bottom):
        im = Image.open(path)
        im_trimmed = im.crop((left, top, right, bottom))
        return im_trimmed

    def readCSV():
        # もしcsvが無ければ、全部止める
        if os.path.isfile("./setting/trimData.csv") == False:
            return 0
        else:
            with open('./setting/trimData.csv') as f:
                reader = csv.reader(f)
                data = [row for row in reader]
                data.pop(0)
                return data

    data = readCSV()

    try:
        shutil.rmtree("./setting/output")
    except OSError as err:
        pass

    if data == 0:
      messagebox.showinfo('終了', 'どうやって斬ればいいかわかりません。\nまずはどこを斬るかを決めてください。')
      return 0

    while data:
        title, left, top, right, bottom = data.pop(0)
        print(title)
        print(left, top, right, bottom)

        outputDir = TRIMMED_FILE_DIR + "/" + title

        # もしトリミング後の画像の格納先が存在しなければ作る
        if os.path.isdir(outputDir) == False:
            os.makedirs(outputDir)

        # 画像ファイル名を取得
        files = os.listdir(ORIGINAL_FILE_DIR)
        # 特定の拡張子のファイルだけを採用。実際に加工するファイルの拡張子に合わせる
        files = [name for name in files if name.split(
            ".")[-1] in ['jpg', "jpeg", "png", "PNG", "JPEG", "JPG", "gif"]]

        try:
          for val in files:
              # オリジナル画像へのパス
              path = ORIGINAL_FILE_DIR + "/" + val
              # トリミングされたimageオブジェクトを取得
              im_trimmed = trim(path, int(left), int(top),
                                int(right), int(bottom))
              # トリミング後のディレクトリに保存。ファイル名の頭に"cut_"をつけている
              # qualityは95より大きい値は推奨されていないらしい
              im_trimmed.save(outputDir + "/" + val, quality=95)

          print("トリミングが終了しました。")
          print("********************************")
        except:
          messagebox.showinfo('エラー', 'エラーが検出されました。中断します。\n\n' + str(sys.stderr))
          try:
            shutil.rmtree("./setting/output")
          except OSError as err:
            pass
          return 0
    messagebox.showinfo('斬りました', '全員分の解答用紙を斬りました。')

def exitGiri():
  sys.exit()


def info():
    pass



def saitenSelect():
    def show_selection():
        for i in lb.curselection():
            print(lb.get(i))
            messagebox.showinfo("採点へ",str(lb.get(i) )+ "を採点します。")
            selectQ.destroy()
            

    def backTop():
        selectQ.destroy()


    selectQ = tkinter.Tk()
    selectQ.geometry("500x500")
    selectQ.title("採点する問題を選ぶ")



    #outputの中のフォルダを取得
    path = "./setting/output/"
    files = os.listdir(path)
    files_dir = [f for f in files if os.path.isdir(os.path.join(path, f))]
    files_dir.sort()
    lb = tkinter.Listbox(selectQ,selectmode='single', height=20 , width =20 )
    for i in files_dir:
        lb.insert(tkinter.END , i)

    lb.grid(row=0, column=0)
    button_frame = tkinter.Frame(selectQ)
    button_frame.grid(row = 0,column=1)

    button1 = tkinter.Button(
        button_frame, text='OK', width = 15 ,height = 3 , 
        command=lambda: show_selection()).pack()


    totopB = tkinter.Button(
        button_frame, text='Topに戻る',width = 15 ,height = 3,
        command=backTop).pack()


    selectQ.mainloop


def top_activate():

    val = 0.4
    fifwid = 500
    fifhet = 400
    global root
    global topimg
    global topfig

    global top_frame
    top_frame = tkinter.Frame(root , bg = "white")
    top_frame.pack()
    fig_frame = tkinter.Frame(top_frame ,width=fifwid,height=fifhet)
    fig_frame.grid(column=0,row=0)

    topimg = Image.open("./appfigs/top.png")
    topimg = topimg.resize((int(topimg.width * val) , int(topimg.height * val )), 0)
    topfig = ImageTk.PhotoImage(topimg , master = root)
    canvas_top = tkinter.Canvas(bg = "white" , master = fig_frame ,width=fifwid + 30,height=fifhet , highlightthickness=0)
    canvas_top.place(x=0,y=0)
    canvas_top.create_image(0,0,image=topfig,anchor = tkinter.NW)
    canvas_top.pack()

    button_frame = tkinter.Frame(top_frame ,bg="white" , highlightthickness=0)
    button_frame.grid(column=1,row=0)

    infoB = tkinter.Button(
        button_frame, text="はじめに", command=info,width = 15 ,height = 3 , highlightthickness=0).pack()


    initB = tkinter.Button(
        button_frame, text="初期設定をする", command=setting_ck,width = 15 ,height = 3 , highlightthickness=0).pack()

    GiriGoB = tkinter.Button(
        button_frame, text="どこを斬るか決める", command=input_ck, width = 15 ,height = 3 , highlightthickness=0).pack()

    initB = tkinter.Button(
        button_frame, text="全員の解答用紙を斬る", command=trimck, width = 15 ,height = 3 , highlightthickness=0).pack()

    saitenB = tkinter.Button(
        button_frame, text="斬った画像を採点する", command=saitenSelect, width = 15 ,height = 3 , highlightthickness=0).pack()


    exitB = tkinter.Button(
        button_frame, text="アプリを閉じる", command=exitGiri, width = 15 ,height = 3 , highlightthickness=0).pack()



# メイン処理 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == "__main__":

    # 画面処理
    root = tkinter.Tk()
    root.title("採点ギリギリ")
    root.geometry("800x400")
    root.configure(bg='white')

    top_activate()

    root.mainloop()
