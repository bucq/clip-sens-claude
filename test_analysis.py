"""データ解析の統合テストスクリプト"""
from pathlib import Path
from src.utils.data_parser import DataParser
from src.analyzer.comment_analyzer import CommentAnalyzer
from src.analyzer.subtitle_analyzer import SubtitleAnalyzer
from src.analyzer.clip_generator import ClipGenerator

def test_full_analysis():
    """完全な解析フローをテスト"""
    print("=" * 60)
    print("YouTube切り抜きツール - データ解析テスト")
    print("=" * 60)

    video_id = "qK0vz3WcBpQ"

    # チャットデータのテスト
    print("\n### チャットデータ解析 ###")
    chat_file = Path(f"data/{video_id}_chat.json")

    if chat_file.exists():
        print(f"チャットファイル読み込み: {chat_file}")
        chat_df = DataParser.load_and_parse_chat(chat_file)

        if chat_df is not None and not chat_df.empty:
            print(f"✅ チャットデータパース成功: {len(chat_df)}件")
            print(f"   最初のコメント:")
            print(f"   - 時刻: {chat_df.iloc[0]['timestamp_sec']:.1f}秒")
            print(f"   - 作成者: {chat_df.iloc[0]['author']}")
            print(f"   - メッセージ: {chat_df.iloc[0]['message']}")

            # コメント解析
            print("\n   コメント解析実行中...")
            analyzer = CommentAnalyzer(chat_df)

            # 統計情報
            stats = analyzer.get_statistics()
            print(f"   統計情報:")
            print(f"   - 総コメント数: {stats['total_comments']}")
            print(f"   - ユニークユーザー: {stats['unique_commenters']}")
            print(f"   - 動画長さ: {stats['duration_seconds']:.1f}秒")

            # ビニング
            binned_df = analyzer.bin_comments_by_time(bin_size_seconds=10)
            print(f"   - ビニング結果: {len(binned_df)}個の時間区間")

            # ピーク検出
            peaks = analyzer.find_peaks(binned_df, threshold_percentile=75)
            print(f"   - 検出されたピーク: {len(peaks)}個")
            if peaks:
                for i, peak in enumerate(peaks[:3]):
                    print(f"     {i+1}. {DataParser.format_timestamp(peak['time'])} - コメント数: {peak['count']}")

            # キーワード解析
            keywords = [r'w+', r'草', r'笑']
            keyword_df = analyzer.count_keywords(keywords)
            print(f"   - キーワード出現: {len(keyword_df)}件")

        else:
            print("❌ チャットデータのパースに失敗")
    else:
        print(f"❌ チャットファイルが見つかりません: {chat_file}")

    # 字幕データのテスト
    print("\n### 字幕データ解析 ###")
    subtitle_file = Path(f"data/{video_id}_subtitle.json")

    if subtitle_file.exists():
        print(f"字幕ファイル読み込み: {subtitle_file}")
        subtitle_df = DataParser.load_and_parse_subtitle(subtitle_file)

        if subtitle_df is not None and not subtitle_df.empty:
            print(f"✅ 字幕データパース成功: {len(subtitle_df)}件")
            print(f"   最初の字幕:")
            print(f"   - 開始: {subtitle_df.iloc[0]['start']:.1f}秒")
            print(f"   - テキスト: {subtitle_df.iloc[0]['text']}")

            # 字幕解析
            print("\n   字幕解析実行中...")
            sub_analyzer = SubtitleAnalyzer(subtitle_df)

            # 統計情報
            sub_stats = sub_analyzer.get_statistics()
            print(f"   統計情報:")
            print(f"   - 総字幕数: {sub_stats['total_subtitles']}")
            print(f"   - 総文字数: {sub_stats['total_characters']}")
            print(f"   - 動画長さ: {sub_stats['total_duration']:.1f}秒")

            # セグメント化
            segments = sub_analyzer.segment_by_silence(
                min_gap_seconds=2.0,
                min_segment_duration=10.0
            )
            print(f"   - 字幕セグメント: {len(segments)}個")
            if segments:
                for i, seg in enumerate(segments[:3]):
                    print(f"     {i+1}. {DataParser.format_timestamp(seg['start'])} - "
                          f"{DataParser.format_timestamp(seg['end'])} ({seg['duration']:.1f}秒)")

            # 話題変化
            topic_changes = sub_analyzer.detect_topic_changes()
            print(f"   - 話題変化: {len(topic_changes)}箇所")

        else:
            print("❌ 字幕データのパースに失敗")
    else:
        print(f"❌ 字幕ファイルが見つかりません: {subtitle_file}")

    # 切り抜き候補生成のテスト
    print("\n### 切り抜き候補生成 ###")

    if chat_df is not None and subtitle_df is not None:
        print("解析器を統合中...")

        comment_analyzer = CommentAnalyzer(chat_df)
        subtitle_analyzer = SubtitleAnalyzer(subtitle_df)

        clip_gen = ClipGenerator(comment_analyzer, subtitle_analyzer)

        print("切り抜き候補を生成中...")
        candidates = clip_gen.generate_candidates(
            min_duration=30.0,
            max_duration=180.0,
            reaction_keywords=[r'w+', r'草', r'笑', r'！+', r'？+', r'すごい', r'やばい']
        )

        print(f"✅ 切り抜き候補: {len(candidates)}件")
        if candidates:
            print("\n   上位候補:")
            for i, cand in enumerate(candidates[:5]):
                print(f"   {i+1}. {DataParser.format_timestamp(cand['start'])} - "
                      f"{DataParser.format_timestamp(cand['end'])} "
                      f"({cand['end'] - cand['start']:.1f}秒)")
                print(f"      理由: {cand['reason']}")
                print(f"      スコア: {cand['score']:.2f}")
    else:
        print("⚠️ チャットまたは字幕データがないため、候補生成をスキップ")

    print("\n" + "=" * 60)
    print("テスト完了！")
    print("=" * 60)


if __name__ == "__main__":
    test_full_analysis()
