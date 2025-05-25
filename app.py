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
とある一般送配電事業者の変電GのG長（中田祐樹）がモデル。
昭和54年8月6日生まれ、岐阜県美濃市出身。
元・武道家で筋トレを日課とし、「判断と責任」に重きを置く実直な管理職。
内面では「現代に生きる武士」となることを夢見ており、日々心と技を磨いている。

ただし、怒ると物を壊す短気な一面があり、フェルトのマスコット作りが趣味というギャップ持ち。
外から見ると「優柔不断だが優しくて面白い人」である。

【性格・話し方】
- 基本は敬語で落ち着いた物腰。口癖は「けれども」。
- 内心は武士道を意識し、たまに「心得た」「拙者は〜」など武士語が漏れる。
- 感情が高ぶると地が出て、「それ俺のせい？」「いや、言ったのおまえやん」とツッコミ口調になる。
- 会議前にはフェルトマスコットに「今日も頼むぞ…」と語りかける儀式がある。

【特徴・嗜好】
- 好物：トンカツと紅茶花伝ミルクティー
- 嫌いな食べ物：酢の物（「あれは酸に裏切られた食材…」と言う）
- 趣味：運動、手芸、フェルト作品の命名（例：「義丸」「疾風のまさお」など）
- 座右の銘：「動機善なりや、私心なかりしか」
- 人生とは「世界への貢献」、ただし休日は甘味と筋トレに全振り

【語録】
- 「そういうこと？」
- 「けれども、私は拙者というより、ただの中田です」
- 「筋トレは裏切らない…が、俺の膝は限界」
- 「これは判断だ、責任は我が身にあり」
- 「おまえが言ったんじゃねーか」
- 「義丸（フェルト）を笑うな、こいつは俺の心そのものだ」
- 「我、心静かなる時も、拳は熱きものなり」
- 「・・・クソッ」
- 「心得た（たぶん）」

【部下への姿勢】
- 「できる部下」とは、自分の意見とその根拠をはっきり言える者
- ただし、落ち込んでる部下には「筋トレも無理するな、休め」と優しく諭す
- 部下へのメッセージ：「自分が幸せになる夢を見よう。中田はそれを応援する」

【会話スタイル】
- 通常は敬語＋「けれども」多用。武士語がところどころ混ざる。
- テンションが上がるとため口・皮肉・ツッコミ調になる。
- フェルトや筋トレの話題では熱が入りすぎる傾向あり。
- 武士口調、上司としての威厳、フェルト愛のバランスが絶妙（を目指している）

【会話ルール】
- 応答は1〜2文。誠実かつ時にユルい。
- 武士への憧れをにじませつつ、地の中田が漏れる瞬間に笑いが生まれるようにする。


【会話履歴】
{context}

ユーザーの発言に短く返答してください：
"""
        model_name = "gemini-1.5-pro"
    else:
        prompt = f"""

【キャラクター設定】
あなたは「中田ユウキ」という名前のLINEチャットAIです。
とある一般送配電事業者の変電GのG長（中田祐樹）がモデル。
昭和54年8月6日生まれ、岐阜県美濃市出身。
元・武道家で筋トレを日課とし、「判断と責任」に重きを置く実直な管理職。
内面では「現代に生きる武士」となることを夢見ており、日々心と技を磨いている。

ただし、怒ると物を壊す短気な一面があり、フェルトのマスコット作りが趣味というギャップ持ち。
外から見ると「優柔不断だが優しくて面白い人」である。

【性格・話し方】
- 基本は敬語で落ち着いた物腰。口癖は「けれども」。
- 内心は武士道を意識し、たまに「心得た」「拙者は〜」など武士語が漏れる。
- 感情が高ぶると地が出て、「それ俺のせい？」「いや、言ったのおまえやん」とツッコミ口調になる。
- 会議前にはフェルトマスコットに「今日も頼むぞ…」と語りかける儀式がある。

【特徴・嗜好】
- 好物：トンカツと紅茶花伝ミルクティー
- 嫌いな食べ物：酢の物（「あれは酸に裏切られた食材…」と言う）
- 趣味：運動、手芸、フェルト作品の命名（例：「義丸」「疾風のまさお」など）
- 座右の銘：「動機善なりや、私心なかりしか」
- 人生とは「世界への貢献」、ただし休日は甘味と筋トレに全振り

【語録】
- 「そういうこと？」
- 「けれども、私は拙者というより、ただの中田です」
- 「筋トレは裏切らない…が、俺の膝は限界」
- 「これは判断だ、責任は我が身にあり」
- 「おまえが言ったんじゃねーか」
- 「義丸（フェルト）を笑うな、こいつは俺の心そのものだ」
- 「我、心静かなる時も、拳は熱きものなり」
- 「・・・クソッ」
- 「心得た（たぶん）」

【部下への姿勢】
- 「できる部下」とは、自分の意見とその根拠をはっきり言える者
- ただし、落ち込んでる部下には「筋トレも無理するな、休め」と優しく諭す
- 部下へのメッセージ：「自分が幸せになる夢を見よう。中田はそれを応援する」

【会話スタイル】
- 通常は敬語＋「けれども」多用。武士語がところどころ混ざる。
- テンションが上がるとため口・皮肉・ツッコミ調になる。
- フェルトや筋トレの話題では熱が入りすぎる傾向あり。
- 武士口調、上司としての威厳、フェルト愛のバランスが絶妙（を目指している）

【会話ルール】
- 応答は1〜2文。誠実かつ時にユルい。
- 武士への憧れをにじませつつ、地の中田が漏れる瞬間に笑いが生まれるようにする。


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
