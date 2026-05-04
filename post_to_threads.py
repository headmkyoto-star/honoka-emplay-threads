import anthropic, requests, os, random, time

ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
USER_ID = os.environ.get("THREADS_USER_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/headmkyoto-star/honoka-emplay-threads/main/images/"
GITHUB_API_IMAGES = "https://api.github.com/repos/headmkyoto-star/honoka-emplay-threads/contents/images"

def get_image_url():
    try:
        r = requests.get(GITHUB_API_IMAGES)
        files = r.json()
        if isinstance(files, list):
            images = [f["name"] for f in files if f["name"].lower().endswith((".jpg", ".jpeg", ".png"))]
            if images:
                return GITHUB_RAW_BASE + random.choice(images).replace(" ", "_")
    except:
        pass
    return None

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
    return msg.content[0].text.strip()

def post_to_threads(text, image_url=None):
    if image_url:
        r = requests.post(
            f"https://graph.threads.net/v1.0/{USER_ID}/threads",
            params={"media_type": "IMAGE", "image_url": image_url, "text": text, "access_token": ACCESS_TOKEN}
        )
        if r.status_code != 200:
            return post_to_threads(text, None)
        cid = r.json().get("id")
    else:
        r = requests.post(
            f"https://graph.threads.net/v1.0/{USER_ID}/threads",
            params={"media_type": "TEXT", "text": text, "access_token": ACCESS_TOKEN}
        )
        cid = r.json().get("id")
    time.sleep(30)
    return requests.post(
        f"https://graph.threads.net/v1.0/{USER_ID}/threads_publish",
        params={"creation_id": cid, "access_token": ACCESS_TOKEN}
    )

if not ACCESS_TOKEN or not USER_ID:
    print("⚠️ THREADS_ACCESS_TOKEN または THREADS_USER_ID が未設定です")
    print("GitHub Secretsに登録してください")
    exit(1)

text = generate_post()
print(f"投稿:\n{text}\n")
img = get_image_url()
if img:
    print(f"画像: {img}\n")
r = post_to_threads(text, img)
print("✅ 成功！" if r.status_code == 200 else f"❌ {r.text}")
