# YouTube切り抜きツール

YouTubeライブ配信のアーカイブから、コメントの盛り上がりや字幕情報を解析し、切り抜き候補タイミングを自動検出するツール。

## 機能

- **コメント盛り上がり解析**: ライブチャットリプレイから盛り上がったタイミングを検出
- **キーワード集計**: 「草」「ww」「!?」などの反応キーワードを時系列で集計
- **字幕セグメント化**: 字幕から話題の区切りを自動検出
- **可視化**: コメント数の時系列グラフと切り抜き候補の一覧表示

## 技術スタック

- Python 3.10+
- yt-dlp: チャットリプレイ取得
- youtube-transcript-api: 字幕取得
- pandas: データ集計・分析
- matplotlib/plotly: グラフ可視化
- Streamlit: Web UI

## インストール

```bash
pip install -r requirements.txt
```

## 使い方

### Streamlit UIを使用

```bash
streamlit run app.py
```

ブラウザで開いたら：
1. サイドバーでYouTube URLを入力
2. 「既存データを使用」チェックボックスで既存データを利用可能
3. 解析パラメータを調整
4. 「解析開始」ボタンをクリック

### コマンドラインでテスト

```bash
# モックデータを生成してテスト
python3 create_mock_data.py
python3 test_analysis.py
```

## プロジェクト構成

```
clip-sens-claude/
├── requirements.txt          # 依存パッケージ
├── README.md                 # プロジェクト説明
├── app.py                   # Streamlitアプリ
├── create_mock_data.py      # モックデータ生成
├── test_analysis.py         # テストスクリプト
├── src/
│   ├── data_fetcher/        # データ取得モジュール
│   │   ├── chat_fetcher.py  # yt-dlpでチャット取得
│   │   └── subtitle_fetcher.py  # youtube-transcript-apiで字幕取得
│   ├── analyzer/            # 解析モジュール
│   │   ├── comment_analyzer.py  # コメント解析
│   │   ├── subtitle_analyzer.py # 字幕解析
│   │   └── clip_generator.py    # 切り抜き候補生成
│   ├── visualizer/          # 可視化モジュール
│   │   └── charts.py
│   └── utils/               # ユーティリティ
│       └── data_parser.py
└── data/                    # データ保存用
```

## 注意事項

- ライブ配信のアーカイブのみチャットリプレイを取得できます
- 字幕は自動生成または手動字幕が必要です
- 初回実行時はデータ取得に時間がかかります
- ネットワーク環境によってはデータ取得に失敗する場合があります
  - その場合は「既存データを使用」オプションを使用してください
  - または `create_mock_data.py` でテストデータを生成できます

## テスト

```bash
# モックデータを生成
python3 create_mock_data.py

# データ解析をテスト
python3 test_analysis.py
```

## トラブルシューティング

### yt-dlpでネットワークエラーが発生する

ネットワーク接続を確認してください。プロキシ環境の場合は、環境変数を設定する必要がある場合があります。

### チャットリプレイが見つからない

この動画がライブ配信のアーカイブであることを確認してください。通常の動画にはチャットリプレイがありません。

### 既存データを使用したい

サイドバーで「既存データを使用」チェックボックスをオンにして、`data/`ディレクトリに対象のビデオIDのデータファイルがあることを確認してください。

## ライセンス

MIT License
