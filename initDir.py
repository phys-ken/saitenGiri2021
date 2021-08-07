import tkinter as tk
import sys
import os
import csv

def yes_no_input():
    while True:
        choice = input("Please respond with 'yes' or 'no' [y/N]: ").lower()
        if choice in ['y', 'ye', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False

print("現在のsettingを初期化し、新しい採点を初めます。よろしいですか？")
print("※ inputフォルダの解答用紙は削除されません。")
if yes_no_input():
  os.makedirs("./setting/input", exist_ok=True)
  os.makedirs("./setting/output", exist_ok=True)
  f = open('setting/ini.csv', 'w')    #既存でないファイル名を作成してください
  writer = csv.writer(f, lineterminator='\n') # 行末は改行
  writer.writerow(["tag", "start_x", "start_y", "end_x", "end_y" ])
  f.close()


else:
  print("処理を中断しました。")
  sys.exit()