import os
import cv2
import shutil
import pandas as pd
from tkinter import messagebox

def imread(path):
    tmp_dir = os.getcwd()
    # 1. 対象ファイルがあるディレクトリに移動
    if len(path.split("/")) > 1:
        file_dir = "/".join(path.split("/")[:-1])
        os.chdir(file_dir)
    # 2. 対象ファイルの名前を変更
    tmp_name = "tmp_name"
    os.rename(path.split("/")[-1], tmp_name)
    # 3. 対象ファイルを読み取る
    img = cv2.imread(tmp_name , 0)
    # 4. 対象ファイルの名前を戻す
    os.rename(tmp_name, path.split("/")[-1])
    # カレントディレクトリをもとに戻す
    os.chdir(tmp_dir)
    return img


def imwrite(filename, img, params=None):
        try:
            ext = os.path.splitext(filename)[1]
            result, n = cv2.imencode(ext, img, params)

            if result:
                with open(filename, mode='w+b') as f:
                    n.tofile(f)
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False


def Saiten_mark():
    if os.path.exists("./setting/kaitoYousi/marubatu"):
        shutil.rmtree("./setting/kaitoYousi/marubatu")
    df_zahyo = pd.read_csv("./setting/trimData.csv", index_col=0)
    Jpg_list = os.listdir("./setting/kaitoYousi")
    print(Jpg_list)
    daimon_list = df_zahyo.index[1:]
    print(daimon_list)
    df_zahyo = df_zahyo.T

    for jpg in Jpg_list:
    # 画像を読み込む
        print( jpg + ":を採点中*****************")
        img = imread("./setting/kaitoYousi/" + jpg)
    # 問題番号リストで回す
        for daimon in daimon_list:
            print(daimon + "を処理中...")
    # 問題番号の座標を取得
            x_s,y_s,x_g,y_g=df_zahyo[daimon]
            x= round(x_s+(x_g-x_s)/2)
            y=round(y_s+(y_g-y_s)/2)
    # 大きさによって〇のサイズを変える
            if x_g-x_s < y_g-y_s:
                size = (x_g-x_s)/3
            elif y_g-y_s < x_g-x_s:
                size = (y_g-y_s)/3
    # 大問フォルダの中の配点フォルダ名を取得
            os.makedirs("./setting/output/"+daimon + "/0", exist_ok=True)
            haiten_list=os.listdir("./setting/output/"+daimon)        
    # 0点フォルダは最初
            haiten_0 = haiten_list[0]
    # 0点フォルダのpass
            img_path_0 = daimon +"/"+ haiten_0 + "/" + jpg
    # バツを付ける
            if os.path.exists("./setting/output/" + img_path_0):
                img = cv2.drawMarker(img, (x, y), (0, 0, 255), thickness=8, markerType=cv2.MARKER_TILTED_CROSS, markerSize=int(size))
            else:
                pass

    # 配点フォルダの要素数が1つなら、全員×なので、〇をつけない
            if len(haiten_list) == 1:
                pass
            else:
    # 正解フォルダは最後
                haiten_cor = haiten_list[-1]
    # 正解フォルダのpath
                img_path_cor = daimon +"/"+ haiten_cor + "/" + jpg
    # 丸を付ける
                if os.path.exists("./setting/output/" + img_path_cor):
                    img = cv2.circle(img, (x, y), int(size), (0, 0, 255), thickness=3, lineType=cv2.LINE_AA)
                else:
                    pass
    # もし配点フォルダが２つなら、○×のみなのでpassする。                          
                if len(haiten_list) == 2:
                    pass
                else:
                    haiten_bubun = haiten_list[1:-1]
                    for bubun in haiten_bubun:
                        img_path_bubun = daimon +"/"+ bubun + "/" + jpg
    # 三角を付ける
                        if os.path.exists("./setting/output/" + img_path_bubun):
                            img = cv2.drawMarker(img, (x, y), (0, 0, 255), thickness=3, markerType=cv2.MARKER_TRIANGLE_UP, markerSize=int(size))
                        else:
                            pass    
    # セーブする
        if not os.path.exists("./setting/kaitoYousi/marubatu"):
            os.makedirs("./setting/kaitoYousi/marubatu")
        imwrite("./setting/kaitoYousi/marubatu"+"/"+ jpg, img)



if os.path.exists("./setting/kaitoYousi"):
  print("採点斬り2021が出力した答案に、○×をつけます。")
  Saiten_mark()
  messagebox.showinfo("○×終了", "採点済み答案に、○×を付けました。kaitoYousiフォルダ内のmarubatuフォルダに、画像が入っています。")

else:
  # メッセージボックス（エラー） 
  messagebox.showerror("フォルダが見つかりません","採点斬り2021で、採点済み答案を出力してください。また、このソフトは『採点斬り2021』と同じ場所においてください。処理を終了します。") 
  print("採点斬り2021で、採点済み答案を出力してください。処理を終了します。")