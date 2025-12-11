"""字幕データの解析"""
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional


class SubtitleAnalyzer:
    """字幕データを解析するクラス"""

    def __init__(self, subtitle_df: pd.DataFrame):
        """
        Args:
            subtitle_df: パースされた字幕DataFrame
        """
        self.subtitle_df = subtitle_df.copy()

    def detect_silence_gaps(
        self,
        min_gap_seconds: float = 2.0
    ) -> List[Dict]:
        """字幕間の無音区間（ギャップ）を検出

        Args:
            min_gap_seconds: 無音とみなす最小ギャップ（秒）

        Returns:
            ギャップ情報のリスト
            各要素: {gap_start, gap_end, gap_duration}
        """
        if self.subtitle_df.empty or len(self.subtitle_df) < 2:
            return []

        gaps = []

        for i in range(len(self.subtitle_df) - 1):
            current_end = self.subtitle_df.iloc[i]['end']
            next_start = self.subtitle_df.iloc[i + 1]['start']

            gap_duration = next_start - current_end

            if gap_duration >= min_gap_seconds:
                gaps.append({
                    'gap_start': current_end,
                    'gap_end': next_start,
                    'gap_duration': gap_duration
                })

        return gaps

    def segment_by_silence(
        self,
        min_gap_seconds: float = 2.0,
        min_segment_duration: float = 10.0
    ) -> List[Dict]:
        """無音区間で字幕をセグメント化

        Args:
            min_gap_seconds: セグメント区切りとみなす最小ギャップ（秒）
            min_segment_duration: セグメントの最小長さ（秒）

        Returns:
            セグメント情報のリスト
            各要素: {segment_id, start, end, duration, subtitle_count, text}
        """
        if self.subtitle_df.empty:
            return []

        gaps = self.detect_silence_gaps(min_gap_seconds)

        # ギャップの位置でセグメントを分割
        segments = []
        segment_start = self.subtitle_df.iloc[0]['start']
        current_segment_subs = []

        for i, row in self.subtitle_df.iterrows():
            # 現在の字幕の終了時刻
            current_end = row['end']

            # この字幕の後にギャップがあるかチェック
            has_gap = False
            for gap in gaps:
                if abs(gap['gap_start'] - current_end) < 0.1:  # 浮動小数点の誤差を考慮
                    has_gap = True
                    break

            current_segment_subs.append(row)

            if has_gap or i == len(self.subtitle_df) - 1:
                # セグメントを確定
                segment_end = row['end']
                segment_duration = segment_end - segment_start

                # 最小長さを満たす場合のみ追加
                if segment_duration >= min_segment_duration:
                    # セグメント内の字幕テキストを結合
                    segment_text = ' '.join([s['text'] for s in current_segment_subs])

                    segments.append({
                        'segment_id': len(segments),
                        'start': segment_start,
                        'end': segment_end,
                        'duration': segment_duration,
                        'subtitle_count': len(current_segment_subs),
                        'text': segment_text
                    })

                # 次のセグメントの準備
                if i < len(self.subtitle_df) - 1:
                    segment_start = self.subtitle_df.iloc[i + 1]['start']
                    current_segment_subs = []

        return segments

    def detect_topic_changes(
        self,
        keywords: List[str] = None
    ) -> List[Dict]:
        """キーワードから話題の変化を検出

        Args:
            keywords: 話題の区切りを示すキーワード（例: "次は", "それでは", "続いて"）

        Returns:
            話題変化の位置リスト
            各要素: {time, keyword, text}
        """
        if keywords is None:
            keywords = [
                r'次は',
                r'それでは',
                r'続いて',
                r'さて',
                r'ここから',
                r'これから',
                r'まず',
                r'最後に'
            ]

        if self.subtitle_df.empty:
            return []

        topic_changes = []

        for _, row in self.subtitle_df.iterrows():
            text = row['text']

            # 各キーワードをチェック
            for keyword in keywords:
                if re.search(keyword, text):
                    topic_changes.append({
                        'time': row['start'],
                        'keyword': keyword,
                        'text': text
                    })
                    break  # 1つの字幕で複数マッチしても1回だけ記録

        return topic_changes

    def find_keyword_timestamps(
        self,
        keywords: List[str],
        case_sensitive: bool = False
    ) -> pd.DataFrame:
        """字幕内のキーワード出現時刻を検索

        Args:
            keywords: 検索するキーワードのリスト（正規表現可）
            case_sensitive: 大文字小文字を区別するか

        Returns:
            キーワード出現情報
            列: keyword, start, end, text
        """
        if self.subtitle_df.empty:
            return pd.DataFrame(columns=['keyword', 'start', 'end', 'text'])

        results = []

        for keyword in keywords:
            # 正規表現パターンを作成
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(keyword, flags)

            # マッチする行を抽出
            matches = self.subtitle_df[
                self.subtitle_df['text'].str.contains(pattern, na=False, regex=True)
            ].copy()

            if not matches.empty:
                matches['keyword'] = keyword
                results.append(matches[['keyword', 'start', 'end', 'text']])

        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame(columns=['keyword', 'start', 'end', 'text'])

    def get_subtitle_at_time(self, timestamp: float) -> Optional[str]:
        """指定時刻の字幕を取得

        Args:
            timestamp: 取得したい時刻（秒）

        Returns:
            字幕テキスト（見つからない場合はNone）
        """
        matches = self.subtitle_df[
            (self.subtitle_df['start'] <= timestamp) &
            (self.subtitle_df['end'] > timestamp)
        ]

        if not matches.empty:
            return matches.iloc[0]['text']
        else:
            return None

    def get_subtitle_range(
        self,
        start_time: float,
        end_time: float
    ) -> pd.DataFrame:
        """指定時間範囲の字幕を取得

        Args:
            start_time: 開始時刻（秒）
            end_time: 終了時刻（秒）

        Returns:
            字幕のDataFrame
        """
        matches = self.subtitle_df[
            (self.subtitle_df['start'] < end_time) &
            (self.subtitle_df['end'] > start_time)
        ]

        return matches.reset_index(drop=True)

    def get_full_text(self, separator: str = ' ') -> str:
        """全字幕をテキストとして結合

        Args:
            separator: 字幕間の区切り文字

        Returns:
            結合された全文
        """
        if self.subtitle_df.empty:
            return ""

        return separator.join(self.subtitle_df['text'].tolist())

    def get_statistics(self) -> Dict:
        """字幕データの統計情報を取得

        Returns:
            統計情報の辞書
        """
        if self.subtitle_df.empty:
            return {
                'total_subtitles': 0,
                'total_duration': 0,
                'avg_subtitle_duration': 0,
                'total_characters': 0,
                'avg_characters_per_subtitle': 0
            }

        total_duration = (
            self.subtitle_df['end'].max() -
            self.subtitle_df['start'].min()
        )

        total_chars = self.subtitle_df['text'].str.len().sum()

        return {
            'total_subtitles': len(self.subtitle_df),
            'total_duration': total_duration,
            'avg_subtitle_duration': self.subtitle_df['duration'].mean(),
            'total_characters': total_chars,
            'avg_characters_per_subtitle': total_chars / len(self.subtitle_df)
        }


if __name__ == "__main__":
    # テスト用
    test_data = pd.DataFrame({
        'start': [0, 5, 10, 15, 25, 30],
        'duration': [4, 4, 4, 4, 4, 4],
        'end': [4, 9, 14, 19, 29, 34],
        'text': [
            'こんにちは',
            'これからゲームを始めます',
            '次はボス戦です',
            'すごい！',
            'それでは終わります',
            'ありがとうございました'
        ]
    })

    analyzer = SubtitleAnalyzer(test_data)

    # 無音区間の検出
    gaps = analyzer.detect_silence_gaps(min_gap_seconds=4)
    print("無音区間:")
    print(gaps)

    # 話題変化の検出
    topic_changes = analyzer.detect_topic_changes()
    print("\n話題変化:")
    print(topic_changes)

    # 統計情報
    stats = analyzer.get_statistics()
    print("\n統計情報:")
    print(stats)
