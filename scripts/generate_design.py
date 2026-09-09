"""design.png を生成するワイヤーフレームスクリプト。
生成物はdesign.mdの仕様書と対になるモックアップ画像。実行時のみ使用し、アプリ本体には含めない。
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 900
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_PATH, size)

# --- カラーパレット（Tailwind slate / indigo / emerald 系を想定） ---
BG = (241, 245, 249)       # slate-100
CARD = (255, 255, 255)     # white
BORDER = (203, 213, 225)   # slate-300
TEXT = (15, 23, 42)        # slate-900
SUBTEXT = (100, 116, 139)  # slate-500
INDIGO = (79, 70, 229)     # indigo-600
INDIGO_LIGHT = (224, 231, 255)  # indigo-100
EMERALD = (5, 150, 105)    # emerald-600
EMERALD_LIGHT = (209, 250, 229)  # emerald-100
AMBER = (217, 119, 6)      # amber-600
AMBER_LIGHT = (254, 243, 199)
RED = (220, 38, 38)
RED_LIGHT = (254, 226, 226)
TRACK = (226, 232, 240)    # slate-200

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def rounded(box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def text(xy, s, size=16, color=TEXT, bold=False, anchor=None):
    d.text(xy, s, font=font(size, bold), fill=color, anchor=anchor)

def pill(xy, s, fg, bg, size=13, pad_x=10, pad_y=5):
    x, y = xy
    f = font(size, bold=True)
    bbox = d.textbbox((0, 0), s, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    box = (x, y, x + tw + pad_x * 2, y + th + pad_y * 2)
    rounded(box, radius=(th + pad_y * 2) // 2, fill=bg)
    d.text((x + pad_x, y + pad_y - bbox[1]), s, font=f, fill=fg)
    return box[2] - box[0]

MARGIN = 24

# ============================================================
# ヘッダーバー
# ============================================================
header_h = 76
rounded((MARGIN, MARGIN, W - MARGIN, MARGIN + header_h), 16, fill=CARD, outline=BORDER, width=1)
text((MARGIN + 24, MARGIN + 16), "WebSend", size=26, bold=True, color=TEXT)
text((MARGIN + 24, MARGIN + 50), "LAN内P2Pファイル・テキスト共有ボード ── サーバーには何も残しません", size=13, color=SUBTEXT)

# 右側: 自分のURL/IP表示 + 接続ステータス
addr_text = "http://192.168.1.42:8000"
f = font(14, bold=True)
bbox = d.textbbox((0, 0), addr_text, font=f)
tw = bbox[2] - bbox[0]
ax = W - MARGIN - 24 - tw - 130
text((ax, MARGIN + 22), addr_text, size=14, bold=True, color=INDIGO)
pill((ax + tw + 14, MARGIN + 18), "● シグナリング接続中", fg=EMERALD, bg=EMERALD_LIGHT, size=13)

y = MARGIN + header_h + 20

# ============================================================
# ルーム参加パネル
# ============================================================
room_h = 100
rounded((MARGIN, y, W - MARGIN, y + room_h), 16, fill=CARD, outline=BORDER, width=1)
text((MARGIN + 24, y + 14), "ルーム", size=15, bold=True, color=TEXT)
text((MARGIN + 24, y + 38), "同じルームコードを入力した端末同士が一覧に表示されます", size=12, color=SUBTEXT)

# 入力欄（ニックネーム / ルームコード）
def input_box(x, y, w, h, label, value, placeholder_color=TEXT):
    text((x, y - 20), label, size=11, color=SUBTEXT, bold=True)
    rounded((x, y, x + w, y + h), 8, fill=(248, 250, 252), outline=BORDER, width=1)
    text((x + 12, y + h // 2), value, size=14, color=placeholder_color, anchor="lm")

input_box(MARGIN + 24, y + 68, 260, 34, "あなたの名前", "ゲスト の Pixel 8")
input_box(MARGIN + 24 + 260 + 20, y + 68, 200, 34, "ルームコード", "HACK-2026")

# 参加ボタン
btn_x = MARGIN + 24 + 260 + 20 + 200 + 20
rounded((btn_x, y + 68, btn_x + 140, y + 68 + 34), 8, fill=INDIGO)
text((btn_x + 70, y + 68 + 17), "ルームに参加", size=14, bold=True, color=(255, 255, 255), anchor="mm")

y += room_h + 20

# ============================================================
# 左カラム: 参加者(ピア)一覧  /  右カラム: 共有パネル
# ============================================================
col_gap = 20
left_w = 380
right_x = MARGIN + left_w + col_gap
right_w = (W - MARGIN) - right_x
bottom_reserve = 210  # ログパネル分を下に確保
col_bottom = H - MARGIN - bottom_reserve

# ---- 左: 接続中の端末一覧 ----
rounded((MARGIN, y, MARGIN + left_w, col_bottom), 16, fill=CARD, outline=BORDER, width=1)
text((MARGIN + 20, y + 16), "同じルームの端末", size=15, bold=True, color=TEXT)
pill((MARGIN + left_w - 20 - 46, y + 14), "3", fg=INDIGO, bg=INDIGO_LIGHT, size=13, pad_x=8)

peers = [
    ("pc", "Kenji の ThinkPad", "接続済み", EMERALD, EMERALD_LIGHT, "切断"),
    ("phone", "佐藤 の iPhone", "接続中…", AMBER, AMBER_LIGHT, "キャンセル"),
    ("pc", "Haiku OS PC (WebPositive)", "未接続", SUBTEXT, TRACK, "接続"),
]
py = y + 56
row_h = 74
for kind, name, status, sc, sbg, action in peers:
    rounded((MARGIN + 16, py, MARGIN + left_w - 16, py + row_h - 10), 12, fill=(248, 250, 252), outline=BORDER, width=1)
    # デバイス種別アイコン（絵文字非依存の簡易描画）
    icon_x, icon_y = MARGIN + 30, py + 16
    if kind == "pc":
        d.rounded_rectangle((icon_x, icon_y, icon_x + 20, icon_y + 14), 2, outline=SUBTEXT, width=2)
        d.line((icon_x + 6, icon_y + 17, icon_x + 14, icon_y + 17), fill=SUBTEXT, width=2)
    else:
        d.rounded_rectangle((icon_x + 4, icon_y, icon_x + 16, icon_y + 20), 3, outline=SUBTEXT, width=2)
        d.line((icon_x + 8, icon_y + 16, icon_x + 12, icon_y + 16), fill=SUBTEXT, width=2)
    text((MARGIN + 60, py + 14), name, size=14, bold=True, color=TEXT)
    pill((MARGIN + 32, py + 36), status, fg=sc, bg=sbg, size=11, pad_x=8, pad_y=4)
    # アクションボタン
    bw = 90
    bx = MARGIN + left_w - 16 - 16 - bw
    is_primary = action == "接続"
    rounded((bx, py + 12, bx + bw, py + 40), 8,
            fill=INDIGO if is_primary else (255, 255, 255),
            outline=None if is_primary else BORDER, width=1)
    text((bx + bw // 2, py + 26), action, size=12, bold=True,
         color=(255, 255, 255) if is_primary else SUBTEXT, anchor="mm")
    py += row_h

text((MARGIN + 20, col_bottom - 34), "※ ルームに入るだけでは接続されません。個別に「接続」を押してP2P接続を開始します", size=11, color=SUBTEXT)

# ---- 右: 共有パネル（テキスト & ファイル） ----
rounded((right_x, y, W - MARGIN, col_bottom), 16, fill=CARD, outline=BORDER, width=1)
text((right_x + 20, y + 16), "共有する（接続済みの端末全員に送信）", size=15, bold=True, color=TEXT)

# テキスト共有
ty = y + 54
text((right_x + 20, ty), "テキスト", size=12, bold=True, color=SUBTEXT)
ta_h = 70
rounded((right_x + 20, ty + 20, W - MARGIN - 130, ty + 20 + ta_h), 10, fill=(248, 250, 252), outline=BORDER, width=1)
text((right_x + 34, ty + 34), "URLやメモをここに貼り付け…", size=13, color=SUBTEXT)
send_btn_x = W - MARGIN - 110
rounded((send_btn_x, ty + 20, W - MARGIN - 20, ty + 20 + ta_h), 10, fill=INDIGO)
text(((send_btn_x + W - MARGIN - 20) // 2, ty + 20 + ta_h // 2), "送信", size=15, bold=True, color=(255, 255, 255), anchor="mm")

# ファイル共有（ドロップゾーン）
fy = ty + 20 + ta_h + 24
text((right_x + 20, fy), "ファイル", size=12, bold=True, color=SUBTEXT)
dz_h = 90
rounded((right_x + 20, fy + 20, W - MARGIN - 20, fy + 20 + dz_h), 10, fill=INDIGO_LIGHT, outline=INDIGO, width=2)
cx = (right_x + 20 + W - MARGIN - 20) // 2
d.line((cx, fy + 20 + dz_h // 2 - 22, cx, fy + 20 + dz_h // 2 - 8), fill=INDIGO, width=3)
d.polygon([(cx - 7, fy + 20 + dz_h // 2 - 16), (cx + 7, fy + 20 + dz_h // 2 - 16), (cx, fy + 20 + dz_h // 2 - 26)], fill=INDIGO)
text((cx, fy + 20 + dz_h // 2 - 2), "ここにファイルをドラッグ＆ドロップ", size=14, bold=True, color=INDIGO, anchor="mm")
text((cx, fy + 20 + dz_h // 2 + 22), "またはクリックして選択（複数選択可）", size=12, color=INDIGO, anchor="mm")

# 送信中ファイルの進捗
py2 = fy + 20 + dz_h + 20
files = [
    ("slides.pdf", "4.2 MB", 0.72, INDIGO, "送信中… 72%"),
    ("photo_001.jpg", "2.8 MB", 1.0, EMERALD, "完了 ✓ 2.8 MB/2.8 MB"),
]
for fname, fsize, prog, color, label in files:
    text((right_x + 20, py2), f"{fname}", size=13, bold=True, color=TEXT)
    text((W - MARGIN - 20, py2), fsize, size=12, color=SUBTEXT, anchor="ra")
    bar_y = py2 + 22
    bar_box = (right_x + 20, bar_y, W - MARGIN - 20, bar_y + 10)
    rounded(bar_box, 5, fill=TRACK)
    bar_w = int((bar_box[2] - bar_box[0]) * prog)
    if bar_w > 0:
        rounded((bar_box[0], bar_box[1], bar_box[0] + bar_w, bar_box[3]), 5, fill=color)
    text((right_x + 20, bar_y + 16), label, size=11, color=SUBTEXT)
    py2 += 56

y = col_bottom + 20

# ============================================================
# 送受信ログ
# ============================================================
log_h = H - MARGIN - y
rounded((MARGIN, y, W - MARGIN, y + log_h), 16, fill=(15, 23, 42), outline=BORDER, width=1)
text((MARGIN + 20, y + 14), "送受信ログ", size=14, bold=True, color=(226, 232, 240))
pill((MARGIN + 20 + 110, y + 12), "自動スクロール", fg=(226,232,240), bg=(51,65,85), size=10, pad_x=8, pad_y=4)

log_lines = [
    ("12:03:41", "[SIGNALING]", (96, 165, 250), "ルーム HACK-2026 に参加しました（自分含め3端末）"),
    ("12:03:55", "[P2P]", (74, 222, 128), "Kenji の ThinkPad と DataChannel が確立しました"),
    ("12:04:10", "[TEXT]", (250, 204, 21), "Kenji の ThinkPad からテキストを受信: \"会場WiFiのパスワードは...\""),
    ("12:04:33", "[FILE]", (167, 139, 250), "slides.pdf の送信を開始（4.2 MB, 42チャンク）"),
    ("12:04:58", "[FILE]", (74, 222, 128), "photo_001.jpg の受信が完了しました (2.8 MB)"),
    ("12:05:02", "[P2P]", (248, 113, 113), "佐藤 の iPhone との接続がタイムアウトしました。再試行してください"),
]
ly = y + 46
for ts, tag, tagcolor, msg in log_lines:
    text((MARGIN + 20, ly), ts, size=12, color=(100, 116, 139))
    text((MARGIN + 110, ly), tag, size=12, bold=True, color=tagcolor)
    text((MARGIN + 210, ly), msg, size=12, color=(226, 232, 240))
    ly += 24

img.save("design.png")
print("saved design.png", img.size)
