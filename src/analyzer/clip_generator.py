"""切り抜き候補の生成"""
import pandas as pd
from typing import List, Dict, Optional
from .comment_analyzer import CommentAnalyzer
from .subtitle_analyzer import SubtitleAnalyzer


class ClipGenerator:
    """切り抜き候補を生成するクラス"""

    def __init__(
        self,
        comment_analyzer: Optional[CommentAnalyzer] = None,
        subtitle_analyzer: Optional[SubtitleAnalyzer] = None
    ):
        """
        Args:
            comment_analyzer: コメント解析器
            subtitle_analyzer: 字幕解析器
        """
        self.comment_analyzer = comment_analyzer
        self.subtitle_analyzer = subtitle_analyzer

    def generate_candidates(
        self,
        min_duration: float = 30.0,
        max_duration: float = 180.0,
        reaction_keywords: List[str] = None
    ) -> List[Dict]:
        """切り抜き候補を生成

        Args:
            min_duration: 候補の最小長さ（秒）
            max_duration: 候補の最大長さ（秒）
            reaction_keywords: 反応キーワードのリスト

        Returns:
            切り抜き候補のリスト
            各要素: {start, end, reason, score, details}
        """
        if reaction_keywords is None:
            reaction_keywords = [
                r'w+',      # ww, www
                r'草',      # 草
                r'笑',      # 笑
                r'！+',     # !!
                r'？+',     # ??
                r'すごい',  # すごい
                r'やばい'   # やばい
            ]

        candidates = []

        # 1. コメントピークベースの候補
        if self.comment_analyzer is not None:
            peak_candidates = self._generate_from_comment_peaks(
                min_duration, max_duration
            )
            candidates.extend(peak_candidates)

        # 2. キーワード反応ベースの候補
        if self.comment_analyzer is not None:
            keyword_candidates = self._generate_from_keywords(
                reaction_keywords, min_duration, max_duration
            )
            candidates.extend(keyword_candidates)

        # 3. 字幕セグメントベースの候補
        if self.subtitle_analyzer is not None:
            segment_candidates = self._generate_from_subtitle_segments(
                min_duration, max_duration
            )
            candidates.extend(segment_candidates)

        # 4. 話題変化ベースの候補
        if self.subtitle_analyzer is not None:
            topic_candidates = self._generate_from_topic_changes(
                min_duration, max_duration
            )
            candidates.extend(topic_candidates)

        # 候補をマージ・スコアリング
        merged_candidates = self._merge_and_score_candidates(
            candidates, min_duration, max_duration
        )

        # スコアでソート（降順）
        merged_candidates.sort(key=lambda x: x['score'], reverse=True)

        return merged_candidates

    def _generate_from_comment_peaks(
        self,
        min_duration: float,
        max_duration: float
    ) -> List[Dict]:
        """コメントピークから候補を生成"""
        candidates = []

        # コメントをビニング
        binned_df = self.comment_analyzer.bin_comments_by_time(bin_size_seconds=10)

        # ピークを検出
        peaks = self.comment_analyzer.find_peaks(
            binned_df,
            threshold_percentile=75,
            min_gap_seconds=30
        )

        for peak in peaks:
            # ピーク前後を含めた候補区間を作成
            start = max(0, peak['time'] - 15)  # ピークの15秒前から
            end = min(peak['time_end'] + 30, peak['time'] + 60)  # ピークの30〜60秒後まで

            duration = end - start

            if min_duration <= duration <= max_duration:
                candidates.append({
                    'start': start,
                    'end': end,
                    'reason': 'コメント急増',
                    'score': 0.0,  # 後で計算
                    'details': {
                        'peak_count': peak['count'],
                        'peak_time': peak['time']
                    }
                })

        return candidates

    def _generate_from_keywords(
        self,
        keywords: List[str],
        min_duration: float,
        max_duration: float
    ) -> List[Dict]:
        """キーワード反応から候補を生成"""
        candidates = []

        # キーワード頻度を取得
        keyword_freq_df = self.comment_analyzer.get_keyword_frequency_over_time(
            keywords, bin_size_seconds=10
        )

        if keyword_freq_df.empty:
            return candidates

        # キーワード出現が多い区間を抽出
        keyword_freq_df = keyword_freq_df.groupby(['bin_start', 'bin_end']).sum().reset_index()
        threshold = keyword_freq_df['count'].quantile(0.75)

        high_keyword_bins = keyword_freq_df[keyword_freq_df['count'] >= threshold]

        # 連続する区間をグループ化
        current_group = []
        for _, row in high_keyword_bins.iterrows():
            if not current_group:
                current_group.append(row)
            else:
                # 連続しているかチェック
                if row['bin_start'] - current_group[-1]['bin_end'] <= 20:
                    current_group.append(row)
                else:
                    # グループを候補として追加
                    candidate = self._create_candidate_from_group(
                        current_group, 'キーワード多発', min_duration, max_duration
                    )
                    if candidate:
                        candidates.append(candidate)
                    current_group = [row]

        # 最後のグループを追加
        if current_group:
            candidate = self._create_candidate_from_group(
                current_group, 'キーワード多発', min_duration, max_duration
            )
            if candidate:
                candidates.append(candidate)

        return candidates

    def _generate_from_subtitle_segments(
        self,
        min_duration: float,
        max_duration: float
    ) -> List[Dict]:
        """字幕セグメントから候補を生成"""
        candidates = []

        # セグメントを取得
        segments = self.subtitle_analyzer.segment_by_silence(
            min_gap_seconds=2.0,
            min_segment_duration=min_duration
        )

        for segment in segments:
            duration = segment['duration']

            if min_duration <= duration <= max_duration:
                candidates.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'reason': '字幕セグメント',
                    'score': 0.0,
                    'details': {
                        'segment_id': segment['segment_id'],
                        'subtitle_count': segment['subtitle_count'],
                        'text_preview': segment['text'][:100] + '...' if len(segment['text']) > 100 else segment['text']
                    }
                })

        return candidates

    def _generate_from_topic_changes(
        self,
        min_duration: float,
        max_duration: float
    ) -> List[Dict]:
        """話題変化から候補を生成"""
        candidates = []

        # 話題変化を検出
        topic_changes = self.subtitle_analyzer.detect_topic_changes()

        for i, change in enumerate(topic_changes):
            # 話題変化から次の変化（または終了）までを候補とする
            start = change['time']

            if i < len(topic_changes) - 1:
                end = topic_changes[i + 1]['time']
            else:
                # 最後の変化の場合は、適当な長さを設定
                end = start + 60

            duration = end - start

            if min_duration <= duration <= max_duration:
                candidates.append({
                    'start': start,
                    'end': end,
                    'reason': f'話題転換: {change["keyword"]}',
                    'score': 0.0,
                    'details': {
                        'keyword': change['keyword'],
                        'text': change['text']
                    }
                })

        return candidates

    def _create_candidate_from_group(
        self,
        group: List,
        reason: str,
        min_duration: float,
        max_duration: float
    ) -> Optional[Dict]:
        """ビングループから候補を作成"""
        if not group:
            return None

        start = group[0]['bin_start']
        end = group[-1]['bin_end']

        # 前後にバッファを追加
        start = max(0, start - 10)
        end = end + 10

        duration = end - start

        if min_duration <= duration <= max_duration:
            total_count = sum(row['count'] for row in group)
            return {
                'start': start,
                'end': end,
                'reason': reason,
                'score': 0.0,
                'details': {
                    'total_count': total_count
                }
            }

        return None

    def _merge_and_score_candidates(
        self,
        candidates: List[Dict],
        min_duration: float,
        max_duration: float
    ) -> List[Dict]:
        """重複する候補をマージしてスコアリング"""
        if not candidates:
            return []

        # 開始時刻でソート
        candidates.sort(key=lambda x: x['start'])

        merged = []
        current = candidates[0].copy()
        current['reasons'] = [current['reason']]
        current['all_details'] = [current['details']]

        for candidate in candidates[1:]:
            # 重複チェック（50%以上重なっている場合）
            overlap = self._calculate_overlap(current, candidate)

            if overlap > 0.5:
                # マージ
                current['start'] = min(current['start'], candidate['start'])
                current['end'] = max(current['end'], candidate['end'])
                current['reasons'].append(candidate['reason'])
                current['all_details'].append(candidate['details'])
            else:
                # 現在の候補を確定してスコア計算
                current['score'] = self._calculate_score(current)
                merged.append(current)

                # 新しい候補を開始
                current = candidate.copy()
                current['reasons'] = [current['reason']]
                current['all_details'] = [current['details']]

        # 最後の候補を追加
        current['score'] = self._calculate_score(current)
        merged.append(current)

        # 長さ制限をチェック
        valid_merged = []
        for candidate in merged:
            duration = candidate['end'] - candidate['start']
            if min_duration <= duration <= max_duration:
                # reasonsを文字列に変換
                candidate['reason'] = ', '.join(set(candidate['reasons']))
                valid_merged.append(candidate)

        return valid_merged

    def _calculate_overlap(self, c1: Dict, c2: Dict) -> float:
        """2つの候補の重複率を計算"""
        overlap_start = max(c1['start'], c2['start'])
        overlap_end = min(c1['end'], c2['end'])

        if overlap_end <= overlap_start:
            return 0.0

        overlap_duration = overlap_end - overlap_start
        min_duration = min(c1['end'] - c1['start'], c2['end'] - c2['start'])

        return overlap_duration / min_duration

    def _calculate_score(self, candidate: Dict) -> float:
        """候補のスコアを計算（0.0〜1.0）"""
        score = 0.0

        # 理由の数でスコア加算（複数の理由がある方が良い）
        num_reasons = len(candidate.get('reasons', []))
        score += min(num_reasons * 0.3, 0.6)

        # 詳細情報からスコア加算
        for details in candidate.get('all_details', []):
            # コメント数が多い場合
            if 'peak_count' in details:
                score += min(details['peak_count'] / 100, 0.3)

            # キーワード出現が多い場合
            if 'total_count' in details:
                score += min(details['total_count'] / 50, 0.2)

        # スコアを0.0〜1.0に正規化
        return min(score, 1.0)


if __name__ == "__main__":
    # テスト用
    print("ClipGeneratorのテストはStreamlit UIから実行してください")
