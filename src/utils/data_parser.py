"""取得したデータのパース・正規化ユーティリティ"""
import json
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path


class DataParser:
    """チャットデータと字幕データをDataFrameに変換するクラス"""

    @staticmethod
    def parse_chat_to_dataframe(chat_data: List[Dict]) -> pd.DataFrame:
        """チャットデータをDataFrameに変換

        Args:
            chat_data: yt-dlpで取得したチャットデータ

        Returns:
            正規化されたDataFrame
            列: timestamp_ms, timestamp_sec, author, message
        """
        parsed_data = []

        for event in chat_data:
            try:
                # replayChatItemAction内のactionsを取得
                actions = event.get('actions', [])

                for action in actions:
                    # addChatItemActionからメッセージを抽出
                    if 'addChatItemAction' in action:
                        item = action['addChatItemAction'].get('item', {})

                        # liveChatTextMessageRendererを取得
                        renderer = item.get('liveChatTextMessageRenderer', {})

                        if renderer:
                            # タイムスタンプ（マイクロ秒）
                            timestamp_usec = int(renderer.get('timestampUsec', 0))
                            timestamp_ms = timestamp_usec // 1000
                            timestamp_sec = timestamp_ms / 1000

                            # 作成者
                            author_name = renderer.get('authorName', {}).get('simpleText', 'Unknown')

                            # メッセージテキスト
                            message_parts = renderer.get('message', {}).get('runs', [])
                            message_text = ''.join([
                                part.get('text', '') for part in message_parts
                            ])

                            parsed_data.append({
                                'timestamp_ms': timestamp_ms,
                                'timestamp_sec': timestamp_sec,
                                'author': author_name,
                                'message': message_text
                            })

            except Exception as e:
                # パースエラーは無視して続行
                continue

        df = pd.DataFrame(parsed_data)

        if not df.empty:
            # タイムスタンプでソート
            df = df.sort_values('timestamp_sec').reset_index(drop=True)

        return df

    @staticmethod
    def parse_subtitle_to_dataframe(subtitle_data: Dict) -> pd.DataFrame:
        """字幕データをDataFrameに変換

        Args:
            subtitle_data: youtube-transcript-apiで取得した字幕データ

        Returns:
            正規化されたDataFrame
            列: start, duration, end, text
        """
        subtitles = subtitle_data.get('subtitles', [])

        parsed_data = []
        for sub in subtitles:
            start = sub['start']
            duration = sub['duration']
            end = start + duration
            text = sub['text']

            parsed_data.append({
                'start': start,
                'duration': duration,
                'end': end,
                'text': text
            })

        df = pd.DataFrame(parsed_data)

        if not df.empty:
            # 開始時刻でソート
            df = df.sort_values('start').reset_index(drop=True)

        return df

    @staticmethod
    def normalize_timestamps(
        df: pd.DataFrame,
        timestamp_column: str = 'timestamp_sec'
    ) -> pd.DataFrame:
        """タイムスタンプを0秒開始に正規化

        Args:
            df: タイムスタンプを含むDataFrame
            timestamp_column: タイムスタンプの列名

        Returns:
            正規化されたDataFrame
        """
        if df.empty:
            return df

        df = df.copy()
        min_timestamp = df[timestamp_column].min()
        df[f'{timestamp_column}_normalized'] = df[timestamp_column] - min_timestamp

        return df

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """秒数を時:分:秒形式に変換

        Args:
            seconds: 秒数

        Returns:
            HH:MM:SS形式の文字列
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    @staticmethod
    def get_video_duration(df: pd.DataFrame, timestamp_column: str = 'timestamp_sec') -> float:
        """動画の長さを取得

        Args:
            df: タイムスタンプを含むDataFrame
            timestamp_column: タイムスタンプの列名

        Returns:
            動画の長さ（秒）
        """
        if df.empty:
            return 0.0

        return df[timestamp_column].max() - df[timestamp_column].min()

    @staticmethod
    def load_and_parse_chat(file_path: Path) -> Optional[pd.DataFrame]:
        """チャットJSONファイルを読み込んでDataFrameに変換

        Args:
            file_path: チャットJSONファイルのパス

        Returns:
            パースされたDataFrame
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # JSON3形式のデータから実際のチャットメッセージを抽出
            messages = []
            if isinstance(data, dict) and 'events' in data:
                for event in data['events']:
                    if 'replayChatItemAction' in event:
                        messages.append(event['replayChatItemAction'])

            return DataParser.parse_chat_to_dataframe(messages)

        except Exception as e:
            print(f"エラー: チャットデータの読み込みに失敗: {e}")
            return None

    @staticmethod
    def load_and_parse_subtitle(file_path: Path) -> Optional[pd.DataFrame]:
        """字幕JSONファイルを読み込んでDataFrameに変換

        Args:
            file_path: 字幕JSONファイルのパス

        Returns:
            パースされたDataFrame
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return DataParser.parse_subtitle_to_dataframe(data)

        except Exception as e:
            print(f"エラー: 字幕データの読み込みに失敗: {e}")
            return None


if __name__ == "__main__":
    # テスト用
    parser = DataParser()

    # タイムスタンプフォーマットのテスト
    test_times = [45, 125, 3665, 7325]
    for t in test_times:
        formatted = parser.format_timestamp(t)
        print(f"{t}秒 -> {formatted}")
