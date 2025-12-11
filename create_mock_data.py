"""テスト用のモックデータ生成スクリプト"""
import json
from pathlib import Path

# テスト用のチャットデータを生成（yt-dlpのJSON3形式）
def create_mock_chat_data(video_id: str = "test_video"):
    """モックチャットデータを生成"""
    chat_data = {
        "events": []
    }

    # 100個のモックコメントを生成
    base_time = 0
    for i in range(100):
        timestamp_usec = (base_time + i * 5) * 1000000  # 5秒ごとにコメント

        # ランダムなメッセージを生成
        messages = ["草", "ww", "すごい", "やばい", "！！", "笑", "www", "面白い", "なるほど"]
        message = messages[i % len(messages)]

        event = {
            "replayChatItemAction": {
                "actions": [
                    {
                        "addChatItemAction": {
                            "item": {
                                "liveChatTextMessageRenderer": {
                                    "timestampUsec": str(timestamp_usec),
                                    "authorName": {
                                        "simpleText": f"User{i % 10}"
                                    },
                                    "message": {
                                        "runs": [
                                            {
                                                "text": message
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        chat_data["events"].append(event)

    # ピーク時のコメントを追加（200-250秒あたり）
    for i in range(50):
        timestamp_usec = (200 + i) * 1000000
        event = {
            "replayChatItemAction": {
                "actions": [
                    {
                        "addChatItemAction": {
                            "item": {
                                "liveChatTextMessageRenderer": {
                                    "timestampUsec": str(timestamp_usec),
                                    "authorName": {
                                        "simpleText": f"User{i % 10}"
                                    },
                                    "message": {
                                        "runs": [
                                            {
                                                "text": "草生える"
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        chat_data["events"].append(event)

    # データを保存
    output_path = Path("data") / f"{video_id}_chat.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=2)

    print(f"モックチャットデータを作成しました: {output_path}")
    return output_path


def create_mock_subtitle_data(video_id: str = "test_video"):
    """モック字幕データを生成"""
    subtitle_data = {
        "video_id": video_id,
        "language": "ja",
        "is_generated": True,
        "subtitles": []
    }

    # テスト用の字幕を生成
    sample_texts = [
        "こんにちは、今日はゲーム実況をします",
        "まずはこのステージから始めます",
        "敵が出てきました",
        "次はボス戦です",
        "ここが難しいですね",
        "やった！クリアしました",
        "それでは次のステージに行きます",
        "このアイテムが重要です",
        "最後のボスです",
        "ありがとうございました"
    ]

    current_time = 0.0
    for i, text in enumerate(sample_texts * 5):  # 50個の字幕
        subtitle_data["subtitles"].append({
            "text": text,
            "start": current_time,
            "duration": 4.0
        })
        current_time += 5.0  # 5秒ごとに字幕

    # データを保存
    output_path = Path("data") / f"{video_id}_subtitle.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(subtitle_data, f, ensure_ascii=False, indent=2)

    print(f"モック字幕データを作成しました: {output_path}")
    return output_path


if __name__ == "__main__":
    # モックデータを作成
    chat_path = create_mock_chat_data("qK0vz3WcBpQ")
    subtitle_path = create_mock_subtitle_data("qK0vz3WcBpQ")

    print("\nモックデータの作成が完了しました！")
    print(f"チャット: {chat_path}")
    print(f"字幕: {subtitle_path}")
