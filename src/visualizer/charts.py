"""グラフ生成・可視化"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class ChartGenerator:
    """グラフ生成クラス"""

    @staticmethod
    def format_time(seconds: float) -> str:
        """秒数を時:分:秒形式に変換

        Args:
            seconds: 秒数

        Returns:
            MM:SS または HH:MM:SS形式の文字列
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    @staticmethod
    def plot_comment_timeline_matplotlib(
        binned_df: pd.DataFrame,
        peaks: List[Dict] = None,
        title: str = "コメント数の時系列推移",
        figsize: Tuple[int, int] = (14, 6),
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """matplotlibでコメント数の時系列グラフを描画

        Args:
            binned_df: ビニングされたコメントデータ
            peaks: ピーク情報のリスト
            title: グラフタイトル
            figsize: 図のサイズ
            save_path: 保存先パス（Noneの場合は保存しない）

        Returns:
            Figureオブジェクト
        """
        fig, ax = plt.subplots(figsize=figsize)

        # コメント数を棒グラフで描画
        ax.bar(
            binned_df['bin_start'],
            binned_df['count'],
            width=binned_df['bin_end'] - binned_df['bin_start'],
            alpha=0.7,
            color='steelblue',
            label='コメント数'
        )

        # ピークをマーク
        if peaks:
            peak_times = [p['time'] for p in peaks]
            peak_counts = [p['count'] for p in peaks]

            ax.scatter(
                peak_times,
                peak_counts,
                color='red',
                s=100,
                marker='*',
                label='ピーク',
                zorder=5
            )

            # ピークに注釈を追加
            for i, peak in enumerate(peaks):
                ax.annotate(
                    ChartGenerator.format_time(peak['time']),
                    xy=(peak['time'], peak['count']),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    fontsize=8,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
                )

        ax.set_xlabel('時刻', fontsize=12)
        ax.set_ylabel('コメント数', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # X軸のフォーマット（時:分:秒表示）
        if not binned_df.empty:
            max_time = binned_df['bin_end'].max()
            num_ticks = min(10, len(binned_df))
            tick_positions = np.linspace(0, max_time, num_ticks)
            tick_labels = [ChartGenerator.format_time(t) for t in tick_positions]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"グラフを保存しました: {save_path}")

        return fig

    @staticmethod
    def plot_comment_timeline_plotly(
        binned_df: pd.DataFrame,
        peaks: List[Dict] = None,
        title: str = "コメント数の時系列推移"
    ) -> go.Figure:
        """Plotlyでコメント数の時系列グラフを描画（インタラクティブ）

        Args:
            binned_df: ビニングされたコメントデータ
            peaks: ピーク情報のリスト
            title: グラフタイトル

        Returns:
            Plotly Figureオブジェクト
        """
        # 時刻をフォーマット
        binned_df = binned_df.copy()
        binned_df['time_formatted'] = binned_df['bin_start'].apply(
            ChartGenerator.format_time
        )

        # 棒グラフ
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=binned_df['bin_start'],
            y=binned_df['count'],
            name='コメント数',
            marker_color='steelblue',
            hovertemplate='<b>時刻:</b> %{customdata}<br>' +
                          '<b>コメント数:</b> %{y}<br>' +
                          '<extra></extra>',
            customdata=binned_df['time_formatted']
        ))

        # ピークをマーク
        if peaks:
            peak_df = pd.DataFrame(peaks)
            peak_df['time_formatted'] = peak_df['time'].apply(
                ChartGenerator.format_time
            )

            fig.add_trace(go.Scatter(
                x=peak_df['time'],
                y=peak_df['count'],
                mode='markers+text',
                name='ピーク',
                marker=dict(
                    size=15,
                    color='red',
                    symbol='star',
                    line=dict(color='darkred', width=1)
                ),
                text=peak_df['time_formatted'],
                textposition='top center',
                hovertemplate='<b>ピーク時刻:</b> %{customdata}<br>' +
                              '<b>コメント数:</b> %{y}<br>' +
                              '<extra></extra>',
                customdata=peak_df['time_formatted']
            ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            xaxis_title='時刻',
            yaxis_title='コメント数',
            hovermode='x unified',
            height=600,
            template='plotly_white'
        )

        return fig

    @staticmethod
    def plot_keyword_frequency_plotly(
        keyword_freq_df: pd.DataFrame,
        title: str = "キーワード出現頻度"
    ) -> go.Figure:
        """Plotlyでキーワード出現頻度のグラフを描画

        Args:
            keyword_freq_df: キーワード頻度データ
            title: グラフタイトル

        Returns:
            Plotly Figureオブジェクト
        """
        # 時刻をフォーマット
        keyword_freq_df = keyword_freq_df.copy()
        keyword_freq_df['time_formatted'] = keyword_freq_df['bin_start'].apply(
            ChartGenerator.format_time
        )

        fig = px.line(
            keyword_freq_df,
            x='bin_start',
            y='count',
            color='keyword',
            title=title,
            labels={'bin_start': '時刻', 'count': '出現回数', 'keyword': 'キーワード'},
            markers=True
        )

        fig.update_layout(
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )

        return fig

    @staticmethod
    def plot_clip_candidates(
        candidates: List[Dict],
        title: str = "切り抜き候補タイミング"
    ) -> go.Figure:
        """切り抜き候補をタイムライン形式で表示

        Args:
            candidates: 切り抜き候補のリスト
                各要素: {start, end, reason, score}
            title: グラフタイトル

        Returns:
            Plotly Figureオブジェクト
        """
        if not candidates:
            # 空のグラフを返す
            fig = go.Figure()
            fig.add_annotation(
                text="切り抜き候補が見つかりませんでした",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig

        # データ準備
        df = pd.DataFrame(candidates)

        # Y軸の位置（候補ごとに異なる高さ）
        df['y'] = range(len(df))

        # 時刻をフォーマット
        df['start_formatted'] = df['start'].apply(ChartGenerator.format_time)
        df['end_formatted'] = df['end'].apply(ChartGenerator.format_time)
        df['duration'] = df['end'] - df['start']

        fig = go.Figure()

        # 各候補を横棒で表示
        for _, row in df.iterrows():
            fig.add_trace(go.Bar(
                x=[row['duration']],
                y=[row['y']],
                orientation='h',
                name=f"{row['start_formatted']} - {row['end_formatted']}",
                marker=dict(
                    color=row.get('score', 0.5),
                    colorscale='Viridis',
                    cmin=0,
                    cmax=1
                ),
                hovertemplate=f"<b>開始:</b> {row['start_formatted']}<br>" +
                              f"<b>終了:</b> {row['end_formatted']}<br>" +
                              f"<b>長さ:</b> {row['duration']:.1f}秒<br>" +
                              f"<b>理由:</b> {row.get('reason', 'N/A')}<br>" +
                              f"<b>スコア:</b> {row.get('score', 0):.2f}<br>" +
                              "<extra></extra>",
                base=row['start'],
                showlegend=False
            ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            xaxis_title='時刻（秒）',
            yaxis_title='候補',
            height=max(400, len(df) * 50),
            template='plotly_white',
            yaxis=dict(
                tickmode='array',
                tickvals=df['y'],
                ticktext=[f"候補 {i+1}" for i in range(len(df))]
            )
        )

        return fig

    @staticmethod
    def create_summary_stats_chart(
        stats: Dict,
        title: str = "解析統計サマリー"
    ) -> go.Figure:
        """統計情報をカード形式で表示

        Args:
            stats: 統計情報の辞書
            title: グラフタイトル

        Returns:
            Plotly Figureオブジェクト
        """
        # 統計情報をテキストとして整形
        stats_text = "<br>".join([
            f"<b>{key}:</b> {value}"
            for key, value in stats.items()
        ])

        fig = go.Figure()

        fig.add_annotation(
            text=stats_text,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14),
            align="left",
            bgcolor="lightgray",
            borderpad=20
        )

        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            height=400,
            template='plotly_white',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )

        return fig


if __name__ == "__main__":
    # テスト用
    import matplotlib
    matplotlib.use('Agg')  # GUIなし環境用

    # テストデータ
    test_binned = pd.DataFrame({
        'bin_start': [0, 10, 20, 30, 40, 50],
        'bin_end': [10, 20, 30, 40, 50, 60],
        'count': [5, 15, 30, 20, 10, 8],
        'comment_rate': [0.5, 1.5, 3.0, 2.0, 1.0, 0.8]
    })

    test_peaks = [
        {'time': 20, 'count': 30, 'comment_rate': 3.0},
        {'time': 30, 'count': 20, 'comment_rate': 2.0}
    ]

    generator = ChartGenerator()

    # Matplotlibグラフのテスト
    fig = generator.plot_comment_timeline_matplotlib(test_binned, test_peaks)
    print("Matplotlibグラフ生成成功")

    # Plotlyグラフのテスト
    plotly_fig = generator.plot_comment_timeline_plotly(test_binned, test_peaks)
    print("Plotlyグラフ生成成功")
