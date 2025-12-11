"""YouTube切り抜きツール - Streamlit UI"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path

# モジュールのインポート
from src.data_fetcher.chat_fetcher import ChatFetcher
from src.data_fetcher.subtitle_fetcher import SubtitleFetcher
from src.utils.data_parser import DataParser
from src.analyzer.comment_analyzer import CommentAnalyzer
from src.analyzer.subtitle_analyzer import SubtitleAnalyzer
from src.analyzer.clip_generator import ClipGenerator
from src.visualizer.charts import ChartGenerator


# ページ設定
st.set_page_config(
    page_title="YouTube切り抜きツール",
    page_icon="🎬",
    layout="wide"
)

# タイトル
st.title("🎬 YouTube切り抜きツール")
st.markdown("YouTubeライブ配信のアーカイブから、コメントと字幕を解析して切り抜き候補を検出します")

# サイドバー: 設定
st.sidebar.header("⚙️ 設定")

# データ取得セクション
st.sidebar.subheader("1. データ取得")
video_url = st.sidebar.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=..."
)

col1, col2 = st.sidebar.columns(2)
fetch_chat = col1.checkbox("チャット取得", value=True)
fetch_subtitle = col2.checkbox("字幕取得", value=True)

use_local_data = st.sidebar.checkbox(
    "既存データを使用",
    value=False,
    help="dataディレクトリにある既存のデータファイルを使用します"
)

# 解析パラメータ
st.sidebar.subheader("2. 解析パラメータ")
bin_size = st.sidebar.slider("コメント集計間隔（秒）", 5, 60, 10)
peak_threshold = st.sidebar.slider("ピーク検出閾値（%）", 50, 95, 75)

# 切り抜き候補パラメータ
st.sidebar.subheader("3. 切り抜き候補設定")
min_clip_duration = st.sidebar.slider("最小長さ（秒）", 10, 120, 30)
max_clip_duration = st.sidebar.slider("最大長さ（秒）", 60, 600, 180)

# 反応キーワード
default_keywords = "w+,草,笑,！+,？+,すごい,やばい"
reaction_keywords_str = st.sidebar.text_input(
    "反応キーワード（カンマ区切り）",
    value=default_keywords
)
reaction_keywords = [k.strip() for k in reaction_keywords_str.split(',')]

# 実行ボタン
run_analysis = st.sidebar.button("🚀 解析開始", type="primary", use_container_width=True)

# セッション状態の初期化
if 'chat_df' not in st.session_state:
    st.session_state.chat_df = None
if 'subtitle_df' not in st.session_state:
    st.session_state.subtitle_df = None
if 'video_id' not in st.session_state:
    st.session_state.video_id = None

# メインコンテンツ
if run_analysis and video_url:
    # ビデオIDを抽出
    chat_fetcher = ChatFetcher()
    video_id = chat_fetcher.extract_video_id(video_url)

    if not video_id:
        st.error("❌ 無効なYouTube URLです")
    else:
        st.session_state.video_id = video_id
        st.info(f"📺 ビデオID: {video_id}")

        # データ取得
        with st.spinner("データを取得中..."):
            # 既存データを使用する場合
            if use_local_data:
                st.info("📂 既存データを読み込み中...")

                # チャットデータ
                chat_file = Path(f"data/{video_id}_chat.json")
                if chat_file.exists():
                    st.success(f"✅ チャットデータを発見: {chat_file}")
                    st.session_state.chat_df = DataParser.load_and_parse_chat(chat_file)
                    if st.session_state.chat_df is not None and not st.session_state.chat_df.empty:
                        st.write(f"📊 コメント数: {len(st.session_state.chat_df)}件")
                else:
                    st.warning(f"⚠️ チャットデータが見つかりません: {chat_file}")

                # 字幕データ
                subtitle_file = Path(f"data/{video_id}_subtitle.json")
                if subtitle_file.exists():
                    st.success(f"✅ 字幕データを発見: {subtitle_file}")
                    st.session_state.subtitle_df = DataParser.load_and_parse_subtitle(subtitle_file)
                    if st.session_state.subtitle_df is not None and not st.session_state.subtitle_df.empty:
                        st.write(f"📊 字幕数: {len(st.session_state.subtitle_df)}件")
                else:
                    st.warning(f"⚠️ 字幕データが見つかりません: {subtitle_file}")

            # 新規取得する場合
            elif fetch_chat:
                with st.expander("📥 チャットデータを取得中...", expanded=True):
                    chat_file = chat_fetcher.fetch_chat(video_url)

                    if chat_file:
                        st.success(f"✅ チャットデータ取得完了: {chat_file}")

                        # データをパース
                        st.session_state.chat_df = DataParser.load_and_parse_chat(chat_file)

                        if st.session_state.chat_df is not None and not st.session_state.chat_df.empty:
                            st.write(f"📊 コメント数: {len(st.session_state.chat_df)}件")
                        else:
                            st.warning("⚠️ チャットデータのパースに失敗しました")
                    else:
                        st.error("❌ チャットデータの取得に失敗しました（ライブ配信のアーカイブではない可能性があります）")

            # 字幕データ取得（新規取得の場合のみ）
            if fetch_subtitle and not use_local_data:
                with st.expander("📥 字幕データを取得中...", expanded=True):
                    subtitle_fetcher = SubtitleFetcher()
                    subtitle_file = subtitle_fetcher.fetch_subtitle(video_id)

                    if subtitle_file:
                        st.success(f"✅ 字幕データ取得完了: {subtitle_file}")

                        # データをパース
                        st.session_state.subtitle_df = DataParser.load_and_parse_subtitle(subtitle_file)

                        if st.session_state.subtitle_df is not None and not st.session_state.subtitle_df.empty:
                            st.write(f"📊 字幕数: {len(st.session_state.subtitle_df)}件")
                        else:
                            st.warning("⚠️ 字幕データのパースに失敗しました")
                    else:
                        st.error("❌ 字幕データの取得に失敗しました")

# 解析結果の表示
if st.session_state.chat_df is not None or st.session_state.subtitle_df is not None:
    st.markdown("---")
    st.header("📊 解析結果")

    # タブで結果を整理
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 コメント解析",
        "📝 字幕解析",
        "🎬 切り抜き候補",
        "💾 データエクスポート"
    ])

    # Tab 1: コメント解析
    with tab1:
        if st.session_state.chat_df is not None and not st.session_state.chat_df.empty:
            st.subheader("コメント統計")

            analyzer = CommentAnalyzer(st.session_state.chat_df)
            stats = analyzer.get_statistics()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("総コメント数", f"{stats['total_comments']:,}")
            col2.metric("ユニークユーザー", f"{stats['unique_commenters']:,}")
            col3.metric("動画長さ", f"{stats['duration_seconds']:.0f}秒")
            col4.metric("コメント/分", f"{stats['comments_per_minute']:.1f}")

            # コメント数の時系列グラフ
            st.subheader("コメント数の時系列推移")
            binned_df = analyzer.bin_comments_by_time(bin_size_seconds=bin_size)
            peaks = analyzer.find_peaks(binned_df, threshold_percentile=peak_threshold)

            chart_gen = ChartGenerator()
            fig = chart_gen.plot_comment_timeline_plotly(binned_df, peaks)
            st.plotly_chart(fig, use_container_width=True)

            # ピーク情報
            if peaks:
                st.subheader("検出されたピーク")
                peak_df = pd.DataFrame(peaks)
                peak_df['time_formatted'] = peak_df['time'].apply(DataParser.format_timestamp)
                st.dataframe(
                    peak_df[['time_formatted', 'count', 'comment_rate']],
                    use_container_width=True
                )

            # キーワード解析
            st.subheader("反応キーワード解析")
            keyword_freq_df = analyzer.get_keyword_frequency_over_time(
                reaction_keywords,
                bin_size_seconds=bin_size
            )

            if not keyword_freq_df.empty:
                keyword_fig = chart_gen.plot_keyword_frequency_plotly(keyword_freq_df)
                st.plotly_chart(keyword_fig, use_container_width=True)
            else:
                st.info("反応キーワードが見つかりませんでした")

            # トップコメンター
            st.subheader("トップコメンター")
            top_commenters = analyzer.get_top_commenters(10)
            st.dataframe(top_commenters, use_container_width=True)

        else:
            st.info("チャットデータがありません")

    # Tab 2: 字幕解析
    with tab2:
        if st.session_state.subtitle_df is not None and not st.session_state.subtitle_df.empty:
            st.subheader("字幕統計")

            sub_analyzer = SubtitleAnalyzer(st.session_state.subtitle_df)
            sub_stats = sub_analyzer.get_statistics()

            col1, col2, col3 = st.columns(3)
            col1.metric("総字幕数", f"{sub_stats['total_subtitles']:,}")
            col2.metric("総文字数", f"{sub_stats['total_characters']:,}")
            col3.metric("動画長さ", f"{sub_stats['total_duration']:.0f}秒")

            # 字幕セグメント
            st.subheader("字幕セグメント（無音区間で区切り）")
            segments = sub_analyzer.segment_by_silence(
                min_gap_seconds=2.0,
                min_segment_duration=min_clip_duration
            )

            if segments:
                seg_df = pd.DataFrame(segments)
                seg_df['start_formatted'] = seg_df['start'].apply(DataParser.format_timestamp)
                seg_df['end_formatted'] = seg_df['end'].apply(DataParser.format_timestamp)
                seg_df['duration_formatted'] = seg_df['duration'].apply(lambda x: f"{x:.0f}秒")

                st.dataframe(
                    seg_df[['segment_id', 'start_formatted', 'end_formatted', 'duration_formatted', 'subtitle_count']],
                    use_container_width=True
                )
            else:
                st.info("セグメントが見つかりませんでした")

            # 話題変化
            st.subheader("話題変化の検出")
            topic_changes = sub_analyzer.detect_topic_changes()

            if topic_changes:
                topic_df = pd.DataFrame(topic_changes)
                topic_df['time_formatted'] = topic_df['time'].apply(DataParser.format_timestamp)
                st.dataframe(
                    topic_df[['time_formatted', 'keyword', 'text']],
                    use_container_width=True
                )
            else:
                st.info("話題変化が見つかりませんでした")

        else:
            st.info("字幕データがありません")

    # Tab 3: 切り抜き候補
    with tab3:
        st.subheader("🎬 切り抜き候補")

        # 解析器の準備
        comment_analyzer = None
        subtitle_analyzer = None

        if st.session_state.chat_df is not None and not st.session_state.chat_df.empty:
            comment_analyzer = CommentAnalyzer(st.session_state.chat_df)

        if st.session_state.subtitle_df is not None and not st.session_state.subtitle_df.empty:
            subtitle_analyzer = SubtitleAnalyzer(st.session_state.subtitle_df)

        if comment_analyzer or subtitle_analyzer:
            # 切り抜き候補を生成
            clip_gen = ClipGenerator(comment_analyzer, subtitle_analyzer)
            candidates = clip_gen.generate_candidates(
                min_duration=min_clip_duration,
                max_duration=max_clip_duration,
                reaction_keywords=reaction_keywords
            )

            if candidates:
                st.success(f"✅ {len(candidates)}件の切り抜き候補を検出しました")

                # 候補を表示
                chart_gen = ChartGenerator()
                clip_fig = chart_gen.plot_clip_candidates(candidates)
                st.plotly_chart(clip_fig, use_container_width=True)

                # 候補の詳細をテーブル表示
                st.subheader("候補一覧")
                cand_df = pd.DataFrame(candidates)
                cand_df['start_formatted'] = cand_df['start'].apply(DataParser.format_timestamp)
                cand_df['end_formatted'] = cand_df['end'].apply(DataParser.format_timestamp)
                cand_df['duration'] = cand_df['end'] - cand_df['start']
                cand_df['duration_formatted'] = cand_df['duration'].apply(lambda x: f"{x:.0f}秒")

                display_df = cand_df[['start_formatted', 'end_formatted', 'duration_formatted', 'reason', 'score']].copy()
                display_df.columns = ['開始', '終了', '長さ', '理由', 'スコア']

                st.dataframe(display_df, use_container_width=True)

                # 各候補のYouTubeリンク生成
                if st.session_state.video_id:
                    st.subheader("YouTubeリンク")
                    for i, cand in enumerate(candidates[:10]):  # 上位10件のみ
                        start_time = int(cand['start'])
                        end_time = int(cand['end'])
                        youtube_link = f"https://www.youtube.com/watch?v={st.session_state.video_id}&t={start_time}s"

                        st.markdown(
                            f"**候補 {i+1}:** [{DataParser.format_timestamp(cand['start'])} - {DataParser.format_timestamp(cand['end'])}]({youtube_link}) "
                            f"(スコア: {cand['score']:.2f})"
                        )

            else:
                st.warning("切り抜き候補が見つかりませんでした")
        else:
            st.info("データを取得してください")

    # Tab 4: データエクスポート
    with tab4:
        st.subheader("💾 データエクスポート")

        col1, col2 = st.columns(2)

        # チャットデータのエクスポート
        with col1:
            st.write("**チャットデータ**")
            if st.session_state.chat_df is not None and not st.session_state.chat_df.empty:
                csv_chat = st.session_state.chat_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 チャットをCSVダウンロード",
                    data=csv_chat,
                    file_name=f"{st.session_state.video_id}_chat.csv",
                    mime="text/csv"
                )

                json_chat = st.session_state.chat_df.to_json(orient='records', force_ascii=False, indent=2)
                st.download_button(
                    label="📥 チャットをJSONダウンロード",
                    data=json_chat,
                    file_name=f"{st.session_state.video_id}_chat.json",
                    mime="application/json"
                )
            else:
                st.info("チャットデータがありません")

        # 字幕データのエクスポート
        with col2:
            st.write("**字幕データ**")
            if st.session_state.subtitle_df is not None and not st.session_state.subtitle_df.empty:
                csv_subtitle = st.session_state.subtitle_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 字幕をCSVダウンロード",
                    data=csv_subtitle,
                    file_name=f"{st.session_state.video_id}_subtitle.csv",
                    mime="text/csv"
                )

                json_subtitle = st.session_state.subtitle_df.to_json(orient='records', force_ascii=False, indent=2)
                st.download_button(
                    label="📥 字幕をJSONダウンロード",
                    data=json_subtitle,
                    file_name=f"{st.session_state.video_id}_subtitle.json",
                    mime="application/json"
                )
            else:
                st.info("字幕データがありません")

        # 切り抜き候補のエクスポート
        st.write("**切り抜き候補**")
        if 'candidates' in locals() and candidates:
            candidates_df = pd.DataFrame(candidates)
            candidates_df['start_formatted'] = candidates_df['start'].apply(DataParser.format_timestamp)
            candidates_df['end_formatted'] = candidates_df['end'].apply(DataParser.format_timestamp)

            export_df = candidates_df[['start', 'end', 'start_formatted', 'end_formatted', 'reason', 'score']]

            csv_candidates = export_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 切り抜き候補をCSVダウンロード",
                data=csv_candidates,
                file_name=f"{st.session_state.video_id}_candidates.csv",
                mime="text/csv"
            )

            json_candidates = candidates_df.to_json(orient='records', force_ascii=False, indent=2)
            st.download_button(
                label="📥 切り抜き候補をJSONダウンロード",
                data=json_candidates,
                file_name=f"{st.session_state.video_id}_candidates.json",
                mime="application/json"
            )
        else:
            st.info("切り抜き候補がありません")

else:
    # 初期画面
    st.info("👈 サイドバーからYouTube URLを入力して解析を開始してください")

    st.markdown("""
    ### 使い方

    1. **YouTube URLを入力**: ライブ配信のアーカイブURLを入力
    2. **データ取得**: チャットと字幕のチェックボックスを選択
    3. **パラメータ調整**: 解析パラメータと切り抜き候補の設定を調整
    4. **解析開始**: ボタンをクリックして解析を開始

    ### 機能

    - **コメント盛り上がり解析**: ライブチャットリプレイから盛り上がったタイミングを検出
    - **キーワード集計**: 「草」「ww」「!?」などの反応キーワードを時系列で集計
    - **字幕セグメント化**: 字幕から話題の区切りを自動検出
    - **切り抜き候補生成**: 複数の指標を統合して切り抜き候補を自動提案

    ### 注意事項

    - ライブ配信のアーカイブのみチャットリプレイを取得できます
    - 字幕は自動生成または手動字幕が必要です
    - 初回実行時はデータ取得に時間がかかります
    """)

# フッター
st.markdown("---")
st.caption("YouTube切り抜きツール v0.1.0 | Made with Streamlit")
