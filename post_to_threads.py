import anthropic, requests, os, random, time

ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
USER_ID = os.environ.get("THREADS_USER_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/headmkyoto-star/honoka-emplay-threads/main/"
GITHUB_API_BASE = "https://api.github.com/repos/headmkyoto-star/honoka-emplay-threads/contents/"

def get_media():
    """画像と動画をランダムにシャッフルして1つ選ぶ"""
    candidates = []  # [(url, type), ...]
    try:
        # 画像取得
        r = requests.get(GITHUB_API_BASE + "images")
        if r.status_code == 200:
            files = r.json()
            if isinstance(files, list):
                for f in files:
                    name = f["name"].lower()
                    if name.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        url = GITHUB_RAW_BASE + "images/" + f["name"].replace(" ", "_")
                        candidates.append((url, "IMAGE"))
    except: pass
    try:
        # 動画取得
        r = requests.get(GITHUB_API_BASE + "videos")
        if r.status_code == 200:
            files = r.json()
            if isinstance(files, list):
                for f in files:
                    name = f["name"].lower()
                    if name.endswith((".mp4", ".mov")):
                        url = GITHUB_RAW_BASE + "videos/" + f["name"].replace(" ", "_")
                        candidates.append((url, "VIDEO"))
    except: pass

    if not candidates:
        return None, None
    return random.choice(candidates)

def generate_post():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    if random.random() < 0.2:
        # 営業系 (20%)
        p = """京都市内のリラクゼーションサロン「ほのかエンプレイ」のセラピストとして、営業系の投稿を作成してください。

        メニュー: ドライヘッドスパ、ボディケア／もみほぐし、フットケア／脚裏マッサージ
        条件:
        - 必ず改行を入れて読みやすく
        - 絵文字を3〜4個入れる
        - ハッシュタグなし
        - 150文字以内
        - 営業色は控えめ、自然な誘い方
        - 投稿文のみ出力（説明や前置き不要）"""
    else:
        # 日常系 (80%)
        p = """京都市内のリラクゼーションサロン「ほのかエンプレイ」のセラピストとして、日常の何気ない投稿を作成してください。

        例: 京都の天気・季節の話、施術中のちょっとした気づき、お客様の何気ない感想、自分の好きなものなど

        条件:
        - 必ず改行を入れて読みやすく
        - 絵文字を2〜4個入れる
        - ハッシュタグなし
        - 150文字以内
        - 営業色なし、人間味のある投稿
        - 投稿文のみ出力（説明や前置き不要）"""

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": p}]
    )
    text = msg.content[0].text.strip()
    # 鍵括弧を除去
    text = text.replace("「", "").replace("」", "")
    return text

def post_to_threads(text, media_url=None, media_type=None):
    """画像・動画・テキストのいずれかで投稿"""
    if media_type == "IMAGE":
        params = {"media_type": "IMAGE", "image_url": media_url, "text": text, "access_token": ACCESS_TOKEN}
        wait_sec = 30
    elif media_type == "VIDEO":
        params = {"media_type": "VIDEO", "video_url": media_url, "text": text, "access_token": ACCESS_TOKEN}
        wait_sec = 60  # 動画はアップロード処理に時間がかかる
    else:
        params = {"media_type": "TEXT", "text": text, "access_token": ACCESS_TOKEN}
        wait_sec = 5

    r = requests.post(f"https://graph.threads.net/v1.0/{USER_ID}/threads", params=params)

    if r.status_code != 200:
        print(f"❌ コンテナ作成失敗: {r.text}")
        if media_type:
            # メディア失敗 → テキストのみで再試行
            print("📝 テキストのみで再試行")
            return post_to_threads(text, None, None)
        return r

    cid = r.json().get("id")
    print(f"✅ コンテナ作成: {cid}")
    print(f"⏳ {wait_sec}秒待機（メディア処理）...")
    time.sleep(wait_sec)

    return requests.post(
        f"https://graph.threads.net/v1.0/{USER_ID}/threads_publish",
        params={"creation_id": cid, "access_token": ACCESS_TOKEN}
    )

if not ACCESS_TOKEN or not USER_ID:
    print("⚠️ THREADS_ACCESS_TOKEN または THREADS_USER_ID が未設定です")
    exit(1)

text = generate_post()
print(f"📝 投稿文:\n{text}\n")

media_url, media_type = get_media()
if media_url:
    print(f"🎬 MEDIA_CHOSEN: type={media_type} url={media_url}")
else:
    print("📄 メディアなし（テキストのみ投稿）")

r = post_to_threads(text, media_url, media_type)
if r.status_code == 200:
    print(f"✅ SUCCESS: {r.json()}")
else:
    print(f"❌ FAILED: {r.status_code} {r.text}")
