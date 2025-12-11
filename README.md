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

```bash
streamlit run app.py
```

## プロジェクト構成

```
clip-sens-claude/
├── requirements.txt          # 依存パッケージ
├── README.md                 # プロジェクト説明
├── src/
│   ├── data_fetcher/        # データ取得モジュール
│   │   ├── chat_fetcher.py  # yt-dlpでチャット取得
│   │   └── subtitle_fetcher.py  # youtube-transcript-apiで字幕取得
│   ├── analyzer/            # 解析モジュール
│   │   ├── comment_analyzer.py  # コメント解析
│   │   └── subtitle_analyzer.py # 字幕解析
│   ├── visualizer/          # 可視化モジュール
│   │   └── charts.py
│   └── utils/               # ユーティリティ
│       └── data_parser.py
├── app.py                   # Streamlitアプリ
└── data/                    # データ保存用
```

## ライセンス

MIT License
