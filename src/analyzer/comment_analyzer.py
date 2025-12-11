"""コメントデータの解析"""
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter


class CommentAnalyzer:
    """コメントデータを解析するクラス"""

    def __init__(self, chat_df: pd.DataFrame):
        """
        Args:
            chat_df: パースされたチャットDataFrame
        """
        self.chat_df = chat_df.copy()

    def bin_comments_by_time(
        self,
        bin_size_seconds: int = 10,
        timestamp_column: str = 'timestamp_sec'
    ) -> pd.DataFrame:
        """コメント数を時系列でビニング（集計）

        Args:
            bin_size_seconds: ビンのサイズ（秒）
            timestamp_column: タイムスタンプの列名

        Returns:
            集計結果のDataFrame
            列: bin_start, bin_end, count, comment_rate
        """
        if self.chat_df.empty:
            return pd.DataFrame(columns=['bin_start', 'bin_end', 'count', 'comment_rate'])

        # タイムスタンプの範囲を取得
        min_time = self.chat_df[timestamp_column].min()
        max_time = self.chat_df[timestamp_column].max()

        # ビンの境界を作成
        bins = np.arange(
            np.floor(min_time),
            np.ceil(max_time) + bin_size_seconds,
            bin_size_seconds
        )

        # ビニングを実行
        self.chat_df['bin'] = pd.cut(
            self.chat_df[timestamp_column],
            bins=bins,
            labels=False,
            include_lowest=True
        )

        # 各ビンのコメント数を集計
        binned_counts = self.chat_df.groupby('bin').size().reset_index(name='count')

        # ビンの開始・終了時刻を計算
        binned_counts['bin_start'] = binned_counts['bin'].apply(
            lambda x: bins[int(x)] if pd.notna(x) else np.nan
        )
        binned_counts['bin_end'] = binned_counts['bin'].apply(
            lambda x: bins[int(x) + 1] if pd.notna(x) else np.nan
        )

        # コメントレート（コメント数/秒）を計算
        binned_counts['comment_rate'] = binned_counts['count'] / bin_size_seconds

        # 不要な列を削除
        binned_counts = binned_counts[['bin_start', 'bin_end', 'count', 'comment_rate']]

        return binned_counts.sort_values('bin_start').reset_index(drop=True)

    def find_peaks(
        self,
        binned_df: pd.DataFrame,
        threshold_percentile: float = 75,
        min_gap_seconds: int = 30
    ) -> List[Dict]:
        """コメント数のピーク（盛り上がり）を検出

        Args:
            binned_df: bin_comments_by_timeで生成したDataFrame
            threshold_percentile: ピークとみなす閾値（パーセンタイル）
            min_gap_seconds: ピーク間の最小間隔（秒）

        Returns:
            ピーク情報のリスト
            各要素: {time, count, comment_rate, percentile}
        """
        if binned_df.empty:
            return []

        # 閾値を計算
        threshold = np.percentile(binned_df['count'], threshold_percentile)

        # 閾値を超える箇所を抽出
        peaks = binned_df[binned_df['count'] >= threshold].copy()

        if peaks.empty:
            return []

        # ピークをマージ（min_gap_seconds以内のものをグループ化）
        merged_peaks = []
        current_group = []

        for _, row in peaks.iterrows():
            if not current_group:
                current_group.append(row)
            else:
                # 前のピークとの間隔をチェック
                time_gap = row['bin_start'] - current_group[-1]['bin_end']

                if time_gap <= min_gap_seconds:
                    current_group.append(row)
                else:
                    # グループを確定して新しいグループを開始
                    merged_peaks.append(self._merge_peak_group(current_group))
                    current_group = [row]

        # 最後のグループを追加
        if current_group:
            merged_peaks.append(self._merge_peak_group(current_group))

        return merged_peaks

    def _merge_peak_group(self, group: List) -> Dict:
        """ピークグループを1つのピークにマージ

        Args:
            group: ピーク行のリスト

        Returns:
            マージされたピーク情報
        """
        # グループ内で最大のコメント数を持つ行を代表として使用
        max_row = max(group, key=lambda x: x['count'])

        return {
            'time': max_row['bin_start'],
            'time_end': max_row['bin_end'],
            'count': max_row['count'],
            'comment_rate': max_row['comment_rate'],
            'percentile': 0  # 後で計算
        }

    def count_keywords(
        self,
        keywords: List[str],
        case_sensitive: bool = False
    ) -> pd.DataFrame:
        """特定キーワードの出現をカウント

        Args:
            keywords: 検索するキーワードのリスト（正規表現可）
            case_sensitive: 大文字小文字を区別するか

        Returns:
            キーワードごとの出現時刻リスト
            列: keyword, timestamp_sec, message
        """
        if self.chat_df.empty:
            return pd.DataFrame(columns=['keyword', 'timestamp_sec', 'message'])

        results = []

        for keyword in keywords:
            # 正規表現パターンを作成
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(keyword, flags)

            # マッチする行を抽出
            matches = self.chat_df[
                self.chat_df['message'].str.contains(pattern, na=False, regex=True)
            ].copy()

            if not matches.empty:
                matches['keyword'] = keyword
                results.append(matches[['keyword', 'timestamp_sec', 'message']])

        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame(columns=['keyword', 'timestamp_sec', 'message'])

    def get_keyword_frequency_over_time(
        self,
        keywords: List[str],
        bin_size_seconds: int = 10
    ) -> pd.DataFrame:
        """キーワードの時系列出現頻度を計算

        Args:
            keywords: 検索するキーワードのリスト
            bin_size_seconds: ビンのサイズ（秒）

        Returns:
            時系列キーワード頻度
            列: bin_start, bin_end, keyword, count
        """
        keyword_df = self.count_keywords(keywords)

        if keyword_df.empty:
            return pd.DataFrame(columns=['bin_start', 'bin_end', 'keyword', 'count'])

        # タイムスタンプの範囲を取得
        min_time = self.chat_df['timestamp_sec'].min()
        max_time = self.chat_df['timestamp_sec'].max()

        # ビンの境界を作成
        bins = np.arange(
            np.floor(min_time),
            np.ceil(max_time) + bin_size_seconds,
            bin_size_seconds
        )

        # ビニングを実行
        keyword_df['bin'] = pd.cut(
            keyword_df['timestamp_sec'],
            bins=bins,
            labels=False,
            include_lowest=True
        )

        # 各ビン・キーワードごとに集計
        binned_keywords = keyword_df.groupby(['bin', 'keyword']).size().reset_index(name='count')

        # ビンの開始・終了時刻を計算
        binned_keywords['bin_start'] = binned_keywords['bin'].apply(
            lambda x: bins[int(x)] if pd.notna(x) else np.nan
        )
        binned_keywords['bin_end'] = binned_keywords['bin'].apply(
            lambda x: bins[int(x) + 1] if pd.notna(x) else np.nan
        )

        # 不要な列を削除
        result = binned_keywords[['bin_start', 'bin_end', 'keyword', 'count']]

        return result.sort_values(['bin_start', 'keyword']).reset_index(drop=True)

    def get_top_commenters(self, top_n: int = 10) -> pd.DataFrame:
        """コメント数の多いユーザーをランキング

        Args:
            top_n: 上位何人を取得するか

        Returns:
            ユーザーランキング
            列: author, comment_count
        """
        if self.chat_df.empty:
            return pd.DataFrame(columns=['author', 'comment_count'])

        commenter_counts = self.chat_df['author'].value_counts().reset_index()
        commenter_counts.columns = ['author', 'comment_count']

        return commenter_counts.head(top_n)

    def get_statistics(self) -> Dict:
        """コメントデータの統計情報を取得

        Returns:
            統計情報の辞書
        """
        if self.chat_df.empty:
            return {
                'total_comments': 0,
                'unique_commenters': 0,
                'avg_comment_length': 0,
                'duration_seconds': 0
            }

        duration = (
            self.chat_df['timestamp_sec'].max() -
            self.chat_df['timestamp_sec'].min()
        )

        return {
            'total_comments': len(self.chat_df),
            'unique_commenters': self.chat_df['author'].nunique(),
            'avg_comment_length': self.chat_df['message'].str.len().mean(),
            'duration_seconds': duration,
            'comments_per_minute': len(self.chat_df) / (duration / 60) if duration > 0 else 0
        }


if __name__ == "__main__":
    # テスト用
    test_data = pd.DataFrame({
        'timestamp_sec': [10, 15, 20, 25, 100, 105, 110],
        'author': ['User1', 'User2', 'User1', 'User3', 'User1', 'User2', 'User1'],
        'message': ['草', 'ww', '笑', '草生える', '!?', 'すごい', 'www']
    })

    analyzer = CommentAnalyzer(test_data)
    binned = analyzer.bin_comments_by_time(bin_size_seconds=30)
    print("ビニング結果:")
    print(binned)

    stats = analyzer.get_statistics()
    print("\n統計情報:")
    print(stats)
