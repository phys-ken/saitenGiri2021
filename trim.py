from PIL import Image
import sys
import os
import csv
import shutil

#トリミング前の画像の格納先
ORIGINAL_FILE_DIR = "./setting/input"
#トリミング後の画像の格納先
TRIMMED_FILE_DIR = "./setting/output"


def trim(path, left, top, right, bottom):
  im = Image.open(path)
  im_trimmed = im.crop((left,top,right,bottom))
  return im_trimmed

def readCSV():
  #もしcsvが無ければ、全部止める
  if os.path.isfile("./setting/trimData.csv") == False:
    sys.exit()
  else:
    with open('./setting/trimData.csv') as f:
        reader = csv.reader(f)
        data = [row for row in reader]
        data.pop(0)
        return data


data = readCSV()
print(len(data))

try:
  shutil.rmtree("./setting/output")
except OSError as err:
  pass

while data:
  title , left , top , right ,bottom = data.pop(0)
  print(title)
  print(left , top , right , bottom)

  outputDir = TRIMMED_FILE_DIR + "/" + title

  #もしトリミング後の画像の格納先が存在しなければ作る
  if os.path.isdir(outputDir) == False:
    os.makedirs(outputDir)

  #画像ファイル名を取得
  files = os.listdir(ORIGINAL_FILE_DIR)
  #特定の拡張子のファイルだけを採用。実際に加工するファイルの拡張子に合わせる
  files = [name for name in files if name.split(".")[-1] in ['jpg', "jpeg", "png", "PNG", "JPEG", "JPG", "gif"]]

  for val in files:
    #オリジナル画像へのパス
    path = ORIGINAL_FILE_DIR + "/"  + val
    #トリミングされたimageオブジェクトを取得
    im_trimmed = trim(path, int(left), int(top), int(right), int(bottom))
    #トリミング後のディレクトリに保存。ファイル名の頭に"cut_"をつけている
    im_trimmed.save(outputDir + "/"  + val, quality=95) #qualityは95より大きい値は推奨されていないらしい

  print("トリミングが終了しました。")
  print("********************************")
