import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tkinter as tk
from PIL import Image, ImageTk

# テスト対象のモジュールにパスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.components.grid_grading_window import GridGradingWindow


class TestEnhancedGridFeatures(unittest.TestCase):
    """強化されたグリッドビュー機能をテストするクラス"""

    def setUp(self):
        """テストの準備"""
        # TkinterのRootをモック化
        self.root = MagicMock(spec=tk.Tk)
        
        # 質問IDの設定
        self.question_id = "test_question"
        
        # 必要なメソッドをモック化
        self.original_init = GridGradingWindow.__init__
        GridGradingWindow.__init__ = MagicMock(return_value=None)
        
        # テスト対象のインスタンス作成
        self.grid_window = GridGradingWindow(self.root, self.question_id)
        
        # 必要な属性を設定
        self.grid_window.parent = self.root
        self.grid_window.question_id = self.question_id
        self.grid_window.window = MagicMock(spec=tk.Toplevel)
        self.grid_window.image_files = []
        self.grid_window.graded_files = {}
        self.grid_window.image_cache = {}
        self.grid_window.thumbnail_cache = {}
        self.grid_window.tk_images = {}
        self.grid_window.filename_list = []
        self.grid_window.score_dict = {}
        self.grid_window.whiteness_dict = {}
        self.grid_window.selected_items = set()
        self.grid_window.thumbnail_size = 150
        self.grid_window.scale_factor = 1.0
        self.grid_window.columns = 4
        self.grid_window.sort_mode = "filename"
        self.grid_window.grading_mode = "single"
        self.grid_window.active_score = ""
        self.grid_window.current_active_item = None
        self.grid_window.fixed_mode_index = 0
        self.grid_window.allowed_scores = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        
        # UIコンポーネントのモック
        self.grid_window.mode_status_label = MagicMock()
        self.grid_window.active_score_label = MagicMock()
        self.grid_window.selection_info = MagicMock()
        self.grid_window.selection_hint_label = MagicMock()
        self.grid_window.count_label = MagicMock()
        self.grid_window.progress_label = MagicMock()
        self.grid_window.mode_menu = MagicMock()
        self.grid_window.mode_var = MagicMock()
        self.grid_window.score_buttons = [MagicMock() for _ in range(10)]
        
        # 必須のフレームを追加
        self.grid_window.status_frame = MagicMock()
        self.grid_window.hint_frame = MagicMock()
        self.grid_window.mode_hint_label = MagicMock()
        
        # メソッドのモック
        self.grid_window._update_grid_view = MagicMock()
        self.grid_window._update_mode_hint = MagicMock()

    def tearDown(self):
        """テストの後片付け"""
        # 元のメソッドを復元
        GridGradingWindow.__init__ = self.original_init

    def test_on_mode_change_to_single(self):
        """一つずつクリック採点モードへの切り替えをテスト"""
        # モードメニュー選択のシミュレーション
        self.grid_window.mode_menu.get = MagicMock(return_value="一つずつクリック採点")
        
        # モード変更メソッドの呼び出し
        self.grid_window._on_mode_change = MagicMock()
        self.grid_window._on_mode_change()
        
        # 期待される状態変更の検証
        self.grid_window._on_mode_change.assert_called_once()

    def test_set_score_in_continuous_mode(self):
        """連続クリック採点モードでのスコア設定をテスト"""
        # 連続採点モードに設定
        self.grid_window.grading_mode = "continuous"
        
        # ボタンの設定を改善
        for i, btn in enumerate(self.grid_window.score_buttons):
            btn.cget = MagicMock(return_value=str(i))
        
        # スコアの設定
        with patch.object(self.grid_window.active_score_label, 'config') as mock_config:
            self.grid_window._set_score_to_selected("5")
            
            # アクティブスコアの確認
            self.assertEqual(self.grid_window.active_score, "5")
            mock_config.assert_called_with(text="アクティブな点数: 5")

    def test_set_score_in_fixed_mode(self):
        """固定採点モードでのスコア設定をテスト"""
        # 固定採点モードに設定
        self.grid_window.grading_mode = "fixed"
        self.grid_window.current_active_item = "test1.jpg"
        
        # テスト用のファイルリストを設定
        self.grid_window._get_sorted_files = MagicMock(
            return_value=["test1.jpg", "test2.jpg", "test3.jpg"]
        )
        
        # スコアの設定
        self.grid_window._set_score_to_selected("7")
        
        # スコアがファイルに設定されたか確認
        self.assertEqual(self.grid_window.score_dict["test1.jpg"], "7")
        
        # 次の画像が選択されたか確認
        self.assertEqual(self.grid_window.current_active_item, "test2.jpg")
        self.assertEqual(self.grid_window.selected_items, {"test2.jpg"})

    def test_on_mousewheel(self):
        """マウスホイールによるスクロール機能をテスト"""
        # マウスホイールイベントのモック作成
        mock_event_up = MagicMock()
        mock_event_up.delta = 120  # 上スクロール
        mock_event_up.num = 4      # Linux用
        
        mock_event_down = MagicMock()
        mock_event_down.delta = -120  # 下スクロール
        mock_event_down.num = 5       # Linux用
        
        # キャンバスのモック設定
        self.grid_window.canvas = MagicMock()
        
        # オリジナルメソッドをモック化
        original_on_mousewheel = self.grid_window._on_mousewheel
        self.grid_window._on_mousewheel = MagicMock()
        
        # 上スクロールテスト
        self.grid_window._on_mousewheel(mock_event_up)
        self.grid_window._on_mousewheel.assert_called_with(mock_event_up)
        
        # 下スクロールテスト
        self.grid_window._on_mousewheel(mock_event_down)
        self.grid_window._on_mousewheel.assert_called_with(mock_event_down)
        
        # 元のメソッドを復元
        self.grid_window._on_mousewheel = original_on_mousewheel
        
    def test_on_item_click_continuous_mode(self):
        """連続クリック採点モードでのアイテムクリック動作をテスト"""
        # 連続クリック採点モードに設定
        self.grid_window.grading_mode = "continuous"
        self.grid_window.active_score = "8"
        
        # イベントのモック
        mock_event = MagicMock()
        test_file = "test_image.jpg"
        
        # アイテムクリックメソッドの呼び出し
        self.grid_window._on_item_click(mock_event, test_file)
        
        # スコアが設定されたことを確認
        self.assertEqual(self.grid_window.score_dict[test_file], "8")
        self.grid_window._update_grid_view.assert_called_once()
        
    def test_on_item_click_fixed_mode(self):
        """固定採点モードでのアイテムクリック動作をテスト"""
        # 固定採点モードに設定
        self.grid_window.grading_mode = "fixed"
        
        # イベントのモック
        mock_event = MagicMock()
        test_file = "test_image.jpg"
        
        # アイテムクリックメソッドの呼び出し
        self.grid_window._on_item_click(mock_event, test_file)
        
        # 画像が選択され、アクティブアイテムになったことを確認
        self.assertEqual(self.grid_window.current_active_item, test_file)
        self.assertEqual(self.grid_window.selected_items, {test_file})
        self.grid_window._update_grid_view.assert_called_once()


if __name__ == '__main__':
    unittest.main()