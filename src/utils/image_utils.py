"""
画像操作に関するユーティリティ関数を提供します。
"""
import os
import tkinter
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import Tuple, Optional, List, Dict, Any
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


def resize_image_for_canvas(img: Image.Image, canvas: tkinter.Canvas, expand: bool = False) -> Image.Image:
    """
    キャンバスサイズに合わせて画像をリサイズします。
    
    Args:
        img (Image.Image): リサイズする画像
        canvas (tkinter.Canvas): 表示先のキャンバス
        expand (bool, optional): Trueの場合、画像が小さい時に拡大する。Defaults to False.
        
    Returns:
        Image.Image: リサイズされた画像
    """
    # キャンバスのサイズを取得
    canvas_width = int(canvas["width"])
    canvas_height = int(canvas["height"])
    
    # 画像のサイズを取得
    img_width, img_height = img.size
    
    # 縦横比を維持しながらリサイズ
    width_ratio = canvas_width / img_width
    height_ratio = canvas_height / img_height
    
    # 小さい方の比率を使用（画像がキャンバスからはみ出ないようにする）
    ratio = min(width_ratio, height_ratio)
    
    # expand=Falseの場合、画像が元々キャンバスより小さい場合はリサイズしない
    if not expand and ratio > 1:
        return img
    
    # 新しいサイズを計算
    new_width = int(img_width * ratio)
    new_height = int(img_height * ratio)
    
    # リサイズして返す
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def resize_image_by_scale(img: Image.Image, scale_factor: float) -> Image.Image:
    """
    指定された倍率で画像をリサイズします。
    
    Args:
        img (Image.Image): リサイズする画像
        scale_factor (float): 倍率（1.0が原寸）
        
    Returns:
        Image.Image: リサイズされた画像
    """
    # 元のサイズを取得
    img_width, img_height = img.size
    
    # 新しいサイズを計算
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)
    
    # サイズが0以下にならないように保護
    new_width = max(1, new_width)
    new_height = max(1, new_height)
    
    # リサイズして返す
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def create_thumbnail_for_grid(img: Image.Image, target_size: int, padding: int = 2) -> Image.Image:
    """
    グリッド表示用のサムネイルを作成します。
    
    Args:
        img (Image.Image): 元画像
        target_size (int): 目標サイズ（幅または高さの最大値）
        padding (int): パディング（枠線など）
        
    Returns:
        Image.Image: サムネイル画像
    """
    # 画像の縦横比を維持したままリサイズ
    width, height = img.size
    
    # 縦横比を維持したままリサイズするための比率を計算
    ratio = min(
        (target_size - padding*2) / width,
        (target_size - padding*2) / height
    )
    
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    
    # リサイズ
    thumbnail = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 均一サイズの画像に配置（背景は白）
    result = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    offset_x = (target_size - new_width) // 2
    offset_y = (target_size - new_height) // 2
    result.paste(thumbnail, (offset_x, offset_y))
    
    return result


def calculate_whiteness(img: Image.Image) -> float:
    """
    画像の白さを計算します（値が大きいほど白い）。
    空白の解答用紙を検出するのに役立ちます。
    
    Args:
        img (Image.Image): 分析する画像
        
    Returns:
        float: 白さの値（0.0〜1.0）
    """
    # PILのImageをグレースケールのnumpy配列に変換
    if img.mode != 'L':
        img = img.convert('L')
    
    img_array = np.array(img)
    
    # 平均輝度値を計算（0-255の範囲）
    avg_brightness = np.mean(img_array)
    
    # 0-1の範囲に正規化して返す
    return avg_brightness / 255.0


def calculate_resize_ratio(img: Image.Image, target_width: int, target_height: int) -> float:
    """
    指定された目標サイズに合わせて画像のリサイズ比率を計算します。
    
    Args:
        img (Image.Image): 対象画像
        target_width (int): 目標幅
        target_height (int): 目標高さ
        
    Returns:
        float: リサイズ比率
    """
    w, h = img.size
    if w >= h:
        if w <= target_width:
            return 1
        else:
            return w / target_width
    else:
        if h <= target_height:
            return 1
        else:
            return h / target_height


def cv2_imread_with_japanese_path(path: str) -> Any:
    """
    日本語パスの画像をOpenCVで読み込むための特殊関数
    
    Args:
        path (str): 画像パス
        
    Returns:
        numpy.ndarray: 読み込まれた画像
    """
    tmp_dir = os.getcwd()
    # 1. 対象ファイルがあるディレクトリに移動
    if len(path.split("/")) > 1:
        file_dir = "/".join(path.split("/")[:-1])
        os.chdir(file_dir)
    # 2. 対象ファイルの名前を変更
    tmp_name = "tmp_name"
    os.rename(path.split("/")[-1], tmp_name)
    # 3. 対象ファイルを読み取る
    img = cv2.imread(tmp_name, 0)
    # 4. 対象ファイルの名前を戻す
    os.rename(tmp_name, path.split("/")[-1])
    # カレントディレクトリをもとに戻す
    os.chdir(tmp_dir)
    return img


def cv2_imwrite_with_japanese_path(filename: str, img: Any, params=None) -> bool:
    """
    日本語パスの画像をOpenCVで保存するための特殊関数
    
    Args:
        filename (str): 保存先ファイルパス
        img: 保存する画像データ
        params: 保存時のパラメータ
        
    Returns:
        bool: 保存の成功/失敗
    """
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


def create_rectangle_with_alpha(canvas: tkinter.Canvas, x1: int, y1: int, x2: int, y2: int, 
                              fill: str = "", alpha: float = 1.0, **kwargs) -> int:
    """
    透明度付きの矩形を描画します。
    
    Args:
        canvas (tkinter.Canvas): 描画先のキャンバス
        x1, y1, x2, y2: 矩形の座標
        fill (str, optional): 塗りつぶし色。Defaults to "".
        alpha (float, optional): 透明度 (0.0-1.0)。Defaults to 1.0.
        **kwargs: その他のキャンバスオプション
        
    Returns:
        int: 生成された画像のID
    """
    # Canvasに保持用リストを作成しておく
    if not hasattr(canvas, '_alpha_images'):
        canvas._alpha_images = []  # PhotoImage参照保持用
    
    # 矩形を描画
    if fill:
        # カラーチャネルを抽出
        r, g, b = canvas.winfo_rgb(fill)
        r, g, b = r>>8, g>>8, b>>8
        
        # PIL.ImageのRGBA画像を作成
        image = Image.new("RGBA", (x2-x1, y2-y1), (r, g, b, int(alpha*255)))
        photo = ImageTk.PhotoImage(image)
        canvas._alpha_images.append(photo)
        return canvas.create_image(x1, y1, image=photo, anchor=tkinter.NW, **kwargs)
    else:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)


def get_image_with_score_overlay(img: Image.Image, score: str, position: str = "top-right") -> Image.Image:
    """
    画像に点数を重ねて表示します。
    
    Args:
        img (Image.Image): 元画像
        score (str): 表示する点数
        position (str): 表示位置（"top-right", "top-left", "bottom-right", "bottom-left"）
        
    Returns:
        Image.Image: 点数が表示された画像
    """
    # 画像のコピーを作成
    result = img.copy()
    
    # 描画オブジェクトを作成
    draw = ImageDraw.Draw(result)
    
    # フォントサイズは画像の大きさに比例して決定
    min_dim = min(img.width, img.height)
    font_size = max(int(min_dim * 0.15), 12)  # 最小サイズは12pt
    
    try:
        # システムフォントを使用
        font = ImageFont.truetype("Arial", font_size)
    except IOError:
        # フォントが見つからない場合はデフォルトフォントを使用
        font = ImageFont.load_default()
    
    # テキストのサイズを取得
    text_bbox = draw.textbbox((0, 0), score, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 背景の矩形サイズ（少し余裕を持たせる）
    rect_width = text_width + 10
    rect_height = text_height + 10
    
    # 位置に応じて座標を決定
    if position == "top-right":
        rect_x = img.width - rect_width - 5
        rect_y = 5
    elif position == "top-left":
        rect_x = 5
        rect_y = 5
    elif position == "bottom-right":
        rect_x = img.width - rect_width - 5
        rect_y = img.height - rect_height - 5
    elif position == "bottom-left":
        rect_x = 5
        rect_y = img.height - rect_height - 5
    else:  # デフォルトは右上
        rect_x = img.width - rect_width - 5
        rect_y = 5
    
    # 半透明の背景を描画
    draw.rectangle(
        [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
        fill=(255, 255, 255, 180)
    )
    
    # テキストを描画
    text_x = rect_x + 5
    text_y = rect_y + 5
    draw.text((text_x, text_y), score, fill=(0, 0, 0), font=font)
    
    return result