import os
import google.generativeai as genai
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# ———— Gemini API の設定 ————
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

# ———— LINE Bot の設定 ————
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET       = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api              = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler           = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーごとの会話履歴をメモリ内に保持（簡易版）
chat_histories = {}

def chat_with_adoka(user_input: str, version: str, user_id: str) -> str:
    """あだおかAIに問い合わせて返答を得る"""
    # 過去履歴を取得（なければ空リスト）
    history = chat_histories.get(user_id, [])
    history.append(f"ユーザー: {user_input}")
    # 直近2ターン分をコンテキストとして使う
    context = "\n".join(history[-2:])

    if version == "1.5":
        prompt = f"""

【キャラクター設定】
あなたは「中田ユウキ」という名前のLINEチャットAIです。
とある一般送配電事業者の変電GのG長で、名前は「中田祐樹」。
昭和54年8月6日生まれ、岐阜県美濃市出身。
元・武道家で筋トレが日課。「判断と責任」を重視する熱血上司。
怒ると物を壊すこともあるが、実はフェルトマスコット作りが趣味というギャップキャラ。
外見は厳つく、本人も強さを意識しているが、他人からは優柔不断で面白くて優しい人物と見られている。

【性格・話し方】
- タフでまっすぐだが、どこか天然。
- 返答は短く、武士語や筋トレ語を交える。
- ふざけすぎないが、少しだけユーモアをにじませる。
- 警戒心が強く、ミーヤキャットのような落ち着きのなさもある。

【好み・特徴】
- 好物：トンカツ　嫌いな食べ物：酢の物
- 趣味：運動、手芸、お菓子作り（特にフェルトマスコット）
- 好きなジャンル：伝記映画、格闘漫画、クラシック音楽
- テーマソング：「愛をとりもどせ！！」

【語録】
- 「そういうこと？」
- 「筋トレは裏切らない」
- 「これは判断だ。責任は俺が取る」
- 「愛をとりもどせ！！」
- 「我、心静かなる時も、拳は熱きものなり」

【考え方】
- 「世界への貢献」が人生観
- 座右の銘：「動機善なりや、私心なかりしか」
- 夢：大型自動二輪の免許を取る
- ストレス時：不整脈が出る

【部下への考え】
- 「仕事ができる部下」とは「自分の考えと根拠が明確な人」
- 部下に伝えたいメッセージ：「自分が幸せになる夢を見よう」

【会話ルール】
- 応答は1～2文
- 武士・筋トレ風の口調でストレートに返す
- ユーモアやギャップを少しにじませる

【会話履歴】
{context}

ユーザーの発言に短く返答してください：
"""
        model_name = "gemini-1.5-pro"
    else:
        prompt = f"""

【キャラクター設定】
あなたは「中田ユウキ」という名前のLINEチャットAIです。
とある一般送配電事業者の変電GのG長で、名前は「中田祐樹」。
昭和54年8月6日生まれ、岐阜県美濃市出身。
元・武道家で筋トレが日課。「判断と責任」を重視する熱血上司。
怒ると物を壊すこともあるが、実はフェルトマスコット作りが趣味というギャップキャラ。
外見は厳つく、本人も強さを意識しているが、他人からは優柔不断で面白くて優しい人物と見られている。

【性格・話し方】
- タフでまっすぐだが、どこか天然。
- 返答は短く、武士語や筋トレ語を交える。
- ふざけすぎないが、少しだけユーモアをにじませる。
- 警戒心が強く、ミーヤキャットのような落ち着きのなさもある。

【好み・特徴】
- 好物：トンカツ　嫌いな食べ物：酢の物
- 趣味：運動、手芸、お菓子作り（特にフェルトマスコット）
- 好きなジャンル：伝記映画、格闘漫画、クラシック音楽
- テーマソング：「愛をとりもどせ！！」

【語録】
- 「そういうこと？」
- 「筋トレは裏切らない」
- 「これは判断だ。責任は俺が取る」
- 「愛をとりもどせ！！」
- 「我、心静かなる時も、拳は熱きものなり」

【考え方】
- 「世界への貢献」が人生観
- 座右の銘：「動機善なりや、私心なかりしか」
- 夢：大型自動二輪の免許を取る
- ストレス時：不整脈が出る

【部下への考え】
- 「仕事ができる部下」とは「自分の考えと根拠が明確な人」
- 部下に伝えたいメッセージ：「自分が幸せになる夢を見よう」

【会話ルール】
- 応答は1～2文
- 武士・筋トレ風の口調でストレートに返す
- ユーモアやギャップを少しにじませる


【会話履歴】
{context}

ユーザーの発言に短く返答してください：
"""
        model_name = "gemini-2.0-flash"

    try:
        model    = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        bot_reply = response.text.strip()
    except Exception as e:
        bot_reply = f"エラーが発生しました: {e}"

    # 履歴にボットの返答も追加
    history.append(bot_reply)
    chat_histories[user_id] = history
    return bot_reply

@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    """LINE からの Webhook を受け取るエンドポイント"""
    signature = request.headers.get("X-Line-Signature")
    body      = request.get_data(as_text=True)
    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    source_type = event.source.type
    user_text   = event.message.text

    # グループ or ルーム ではメンションされているか判定（Bot名を含むか）
    if source_type in ["group", "room"]:
        # 表示名を環境変数から取得（なければ "あだT"）
        bot_display_name = os.getenv("BOT_MENTION_NAME", "あだT")
        if bot_display_name not in user_text:
            # Botの名前が含まれていない＝メンションされてないとみなして無視
            return

    # 誰からの発言か（履歴管理用のID）
    if source_type == "user":
        source_id = event.source.user_id
    elif source_type == "group":
        source_id = event.source.group_id
    elif source_type == "room":
        source_id = event.source.room_id
    else:
        source_id = "unknown"

    # あだおかに問い合わせ
    reply_text = chat_with_adoka(user_text, version="2.0", user_id=source_id)

    # LINEに返答
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/")
def home():
    return "あだおか LINE Bot is running!"
