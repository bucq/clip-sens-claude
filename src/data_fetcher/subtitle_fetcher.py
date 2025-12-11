"""youtube-transcript-apiを使用した字幕取得"""
import json
from pathlib import Path
from typing import Optional, List, Dict
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)


class SubtitleFetcher:
    """YouTube動画の字幕を取得するクラス"""

    def __init__(self, output_dir: str = "data"):
        """
        Args:
            output_dir: 字幕データの保存先ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_subtitle(
        self,
        video_id: str,
        languages: List[str] = ['ja', 'en'],
        force: bool = False
    ) -> Optional[Path]:
        """動画の字幕を取得

        Args:
            video_id: YouTube動画のID
            languages: 取得する言語のリスト（優先順）
            force: 既存ファイルがあっても再取得するか

        Returns:
            保存したJSONファイルのパス（失敗時はNone）
        """
        output_file = self.output_dir / f"{video_id}_subtitle.json"

        # 既存ファイルチェック
        if output_file.exists() and not force:
            print(f"字幕データが既に存在します: {output_file}")
            return output_file

        print(f"字幕を取得中: {video_id}")

        try:
            # 字幕を取得（自動生成も含む）
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 優先言語で字幕を取得
            transcript = None
            used_language = None

            # まず手動字幕を試す
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    used_language = lang
                    print(f"手動字幕を取得: {lang}")
                    break
                except NoTranscriptFound:
                    continue

            # 手動字幕がない場合は自動生成字幕を試す
            if transcript is None:
                for lang in languages:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        used_language = lang
                        print(f"自動生成字幕を取得: {lang}")
                        break
                    except NoTranscriptFound:
                        continue

            if transcript is None:
                print(f"エラー: 指定された言語の字幕が見つかりません: {languages}")
                return None

            # 字幕データを取得
            subtitle_data = transcript.fetch()

            # メタデータを追加して保存
            output_data = {
                "video_id": video_id,
                "language": used_language,
                "is_generated": transcript.is_generated,
                "subtitles": subtitle_data
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"字幕データを保存しました: {output_file} ({len(subtitle_data)}件)")
            return output_file

        except TranscriptsDisabled:
            print(f"エラー: この動画は字幕が無効になっています")
            return None
        except VideoUnavailable:
            print(f"エラー: 動画が利用できません: {video_id}")
            return None
        except Exception as e:
            print(f"エラー: {e}")
            return None

    def load_subtitle_data(self, file_path: Path) -> Optional[Dict]:
        """保存された字幕データを読み込む

        Args:
            file_path: 字幕JSONファイルのパス

        Returns:
            字幕データ（メタデータ + 字幕リスト）
        """
        if not file_path.exists():
            print(f"エラー: ファイルが存在しません: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            subtitle_count = len(data.get('subtitles', []))
            print(f"字幕データを読み込みました: {subtitle_count}件")
            return data

        except Exception as e:
            print(f"エラー: ファイル読み込み失敗: {e}")
            return None

    def get_subtitle_at_time(
        self,
        subtitle_data: Dict,
        timestamp: float
    ) -> Optional[str]:
        """指定時刻の字幕テキストを取得

        Args:
            subtitle_data: load_subtitle_dataで取得したデータ
            timestamp: 取得したい時刻（秒）

        Returns:
            字幕テキスト（見つからない場合はNone）
        """
        subtitles = subtitle_data.get('subtitles', [])

        for sub in subtitles:
            start = sub['start']
            duration = sub['duration']
            if start <= timestamp < start + duration:
                return sub['text']

        return None

    def get_subtitle_range(
        self,
        subtitle_data: Dict,
        start_time: float,
        end_time: float
    ) -> List[Dict]:
        """指定時間範囲の字幕を取得

        Args:
            subtitle_data: load_subtitle_dataで取得したデータ
            start_time: 開始時刻（秒）
            end_time: 終了時刻（秒）

        Returns:
            字幕のリスト
        """
        subtitles = subtitle_data.get('subtitles', [])
        result = []

        for sub in subtitles:
            sub_start = sub['start']
            sub_end = sub_start + sub['duration']

            # 範囲内に重なる字幕を抽出
            if sub_start < end_time and sub_end > start_time:
                result.append(sub)

        return result


if __name__ == "__main__":
    # テスト用
    fetcher = SubtitleFetcher()

    # テスト用のビデオID（実際のテストでは有効なIDを使用）
    test_video_id = "dQw4w9WgXcQ"
    print(f"テスト用ビデオID: {test_video_id}")
