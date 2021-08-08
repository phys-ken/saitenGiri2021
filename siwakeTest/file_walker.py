import os
import pathlib

def folder_walker(folder_path, recursive = True, file_ext = ".*"):
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