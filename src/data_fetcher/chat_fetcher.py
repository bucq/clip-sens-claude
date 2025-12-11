"""yt-dlpを使用したYouTubeライブチャットリプレイ取得"""
import json
import subprocess
import re
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class ChatFetcher:
    """YouTubeライブチャットリプレイを取得するクラス"""

    def __init__(self, output_dir: str = "data"):
        """
        Args:
            output_dir: チャットデータの保存先ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """YouTube URLからビデオIDを抽出

        Args:
            url: YouTube URL

        Returns:
            ビデオID（抽出できない場合はNone）
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/live/([a-zA-Z0-9_-]{11})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # URLがビデオIDそのものの場合
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url

        return None

    def fetch_chat(self, video_url: str, force: bool = False) -> Optional[Path]:
        """ライブチャットリプレイを取得

        Args:
            video_url: YouTube動画のURL
            force: 既存ファイルがあっても再取得するか

        Returns:
            保存したJSONファイルのパス（失敗時はNone）
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            print(f"エラー: 無効なYouTube URL: {video_url}")
            return None

        output_file = self.output_dir / f"{video_id}_chat.json"

        # 既存ファイルチェック
        if output_file.exists() and not force:
            print(f"チャットデータが既に存在します: {output_file}")
            return output_file

        print(f"チャットリプレイを取得中: {video_id}")

        try:
            # yt-dlpでライブチャットを取得
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--sub-lang", "live_chat",
                "--sub-format", "json3",
                "--no-check-certificate",
                "--proxy", "",
                "-o", str(self.output_dir / f"{video_id}"),
                f"https://www.youtube.com/watch?v={video_id}"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分のタイムアウト
            )

            if result.returncode != 0:
                stderr = result.stderr
                if "Failed to resolve" in stderr or "Unable to connect" in stderr:
                    print(f"エラー: ネットワーク接続エラー")
                    print(f"ヒント: インターネット接続を確認してください")
                    print(f"詳細: {stderr[:200]}...")
                elif "Private video" in stderr or "Video unavailable" in stderr:
                    print(f"エラー: 動画が非公開または利用できません")
                elif "does not have live chat" in stderr or "Subtitles are disabled" in stderr:
                    print(f"エラー: この動画にはライブチャットリプレイがありません")
                    print(f"ヒント: ライブ配信のアーカイブのみチャットリプレイを取得できます")
                else:
                    print(f"エラー: yt-dlp実行失敗\n{stderr}")
                return None

            # 生成されたファイルを確認
            live_chat_file = self.output_dir / f"{video_id}.live_chat.json"
            if live_chat_file.exists():
                # リネームして保存
                live_chat_file.rename(output_file)
                print(f"チャットデータを保存しました: {output_file}")
                return output_file
            else:
                print("警告: チャットリプレイが見つかりません（ライブ配信のアーカイブではない可能性があります）")
                return None

        except subprocess.TimeoutExpired:
            print("エラー: タイムアウト（5分以内に完了しませんでした）")
            return None
        except Exception as e:
            print(f"エラー: {e}")
            return None

    def load_chat_data(self, file_path: Path) -> Optional[List[Dict]]:
        """保存されたチャットデータを読み込む

        Args:
            file_path: チャットJSONファイルのパス

        Returns:
            チャットメッセージのリスト
        """
        if not file_path.exists():
            print(f"エラー: ファイルが存在しません: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # JSON3形式のデータから実際のチャットメッセージを抽出
            messages = []
            if isinstance(data, dict) and 'events' in data:
                for event in data['events']:
                    if 'replayChatItemAction' in event:
                        messages.append(event['replayChatItemAction'])

            print(f"チャットメッセージを読み込みました: {len(messages)}件")
            return messages

        except Exception as e:
            print(f"エラー: ファイル読み込み失敗: {e}")
            return None


if __name__ == "__main__":
    # テスト用
    fetcher = ChatFetcher()

    # URLからビデオID抽出のテスト
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "dQw4w9WgXcQ"
    ]

    for url in test_urls:
        video_id = fetcher.extract_video_id(url)
        print(f"{url} -> {video_id}")
