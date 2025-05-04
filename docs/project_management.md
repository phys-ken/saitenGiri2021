# 採点斬り2021 プロジェクト管理ドキュメント

## プロジェクト概要

採点斬り2021は、教育現場での試験採点作業を効率化するためのPythonベースのアプリケーションです。スキャンした解答用紙から特定領域を切り出し、採点プロセスを自動化・効率化します。

## プロジェクト構成

```
saitenGiri2021/
├── src/                   # ソースコード
│   ├── core/             # 採点、マーキング、トリミングなどのコア機能
│   ├── models/           # データモデル定義
│   ├── ui/               # ユーザーインターフェース
│   │   └── components/   # UIコンポーネント
│   └── utils/            # ユーティリティ関数
├── resources/             # アイコン、画像などのリソース
├── setting/               # 設定ファイルとデータディレクトリ
│   ├── input/            # スキャン画像の入力ディレクトリ
│   ├── output/           # 採点結果の出力ディレクトリ
│   └── export/           # エクスポートされたデータ
├── test_figs/            # テスト用の画像ファイル (gitignore対象)
├── tests/                # テストコード
│   └── samples/          # テスト用サンプル画像
├── legacy/               # 旧バージョンのコード
├── docs/                 # ドキュメント
└── main.py               # エントリーポイント
```

## 開発環境

- Python 3.10以上
- 必要なライブラリ：
  - OpenCV (画像処理)
  - NumPy (数値計算)
  - Pandas (データ処理)
  - Tkinter (UI)
  - Pillow (画像処理)
  - openpyxl (Excel出力)

## ビルドプロセス

アプリケーションはPyInstallerを使用して実行可能ファイルにパッケージ化されます：

```bash
# Windows
pyinstaller --onefile --windowed --icon=resources/icon.ico --name="採点斬り2021" main.py

# Mac
pyinstaller --onefile --windowed --icon=resources/icon.ico --name="saitenGiri2021" main.py
```

## テスト

テストはpytestを使用して実行します：

```bash
pytest tests/
```

主要なテストケース：
- `test_grade_process.py`: 採点処理のテスト
- `test_marubatu_function.py`: マルバツ機能のテスト
- `test_export_options.py`: エクスポート機能のテスト
- `test_temp_files.py`: 一時ファイル処理のテスト

## リリースプロセス

1. テストの実行と確認
2. バージョン番号の更新（main.pyのVERSION変数）
3. PyInstallerでの実行ファイル作成
4. GitHubリリースの作成

## 今後の開発予定

- [ ] 採点履歴の確認機能
- [ ] バッチ処理の高速化
- [ ] カラー保存時の最適化改善
- [ ] クラウド連携オプションの追加

## メンテナンス情報

- 最終更新日: 2025年5月4日
- メンテナー: phys_ken (@phys_ken on Twitter)
- ライセンス: GPLv3.0