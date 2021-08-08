import os
import sys

import tkinter as f_tk
from tkinter import filedialog

def file_selector(ini_folder_path = str(os.path.dirname(sys.argv[0])), 
                                    multiple= False, dir_select = False):
    """
    ダイアログを開いて、ファイルやフォルダを選択する。
    初期フォルダを指定しなかった場合、ファイル自体のフォルダを開く。
    オプションでフォルダ選択、ファイル選択（複数・単一）を選択できる。

    Parameters
    ----------
    ini_folder_path : str
        初期に開くフォルダ。既定値は実行ファイルのフォルダパス
    multiple : bool
        ファイルを複数選択可能にするか否か。既定値はFalseで単一選択。
    dir_select : bool
        フォルダ選択モード。既定値はFalseでファイル選択モードに。
    """

    root_fileselect=f_tk.Tk()
    root_fileselect.withdraw()  # ウィンドウを非表示する

    if  os.path.isfile(ini_folder_path):
        ini_folder_path = os.path.dirname(ini_folder_path) # 初期フォルダ指定にファイル名が入っていた場合、ファイルのフォルダを返す

    if dir_select:
        select_item = f_tk.filedialog.askdirectory(initialdir=ini_folder_path)  # ディレクトリ選択モード

    elif multiple:
        select_item = f_tk.filedialog.askopenfilenames(initialdir=ini_folder_path)  # ファイル（複数）選択モード
    else:
        select_item = f_tk.filedialog.askopenfilename(initialdir=ini_folder_path)  # ファイル（単一）選択モード

    root_fileselect.destroy()

    if not select_item =="":
        return select_item
