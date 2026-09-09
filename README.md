# WebSend

同じWi-Fi（LAN）につながっているスマホ・PC・Haiku OSのブラウザ同士で、インターネットを介さずにファイルとテキストを送受信できる、1日限定ハッカソン向けの共有ボードです。

- サーバーはWebRTCの接続情報を仲介するだけで、ファイルやテキストの実データはブラウザ間で直接（P2P）やり取りされます。
- サーバー側にデータベースやファイル保存は一切ありません。ルームの状態はメモリ上だけに存在し、再起動すれば消えます。
- ビルド不要の1ファイルHTML（Vanilla JS + Tailwind CDN）なので、フロントエンドのインストール作業も不要です。

## 動作環境 / 対応ブラウザ

- Python 3.10以上
- モダンブラウザ（Chrome、Firefox、Edge、Safari等）でWi-Fi経由でアクセス
- **Haiku OSの標準ブラウザ「WebPositive」はWebRTC（`RTCPeerConnection`）が未実装のため使用できません。Haiku OSでは代わりにFirefoxを使ってください**（実機でP2P接続・テキスト送信・ファイル送信の動作を確認済みです）。

## セットアップ

```bash
python3 -m pip install --user fastapi uvicorn websockets
```

低スペックなARM機（Raspberry Pi等）では `uvicorn[standard]` は避けてください。オプション拡張の`uvloop`がソースからのビルドになり、非力な機体では現実的な時間で終わりません。上記のとおり拡張なしの`uvicorn`で十分です。

## 起動方法

```bash
cd WebSend
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
```

起動すると以下の2つが立ち上がります。

- HTTP/WebSocketサーバー: `0.0.0.0:8000`（画面の配信とシグナリング）
- STUNサーバー: `0.0.0.0:3478` (UDP)（LAN内で完結する自前STUN。インターネットのSTUNは使いません）

## LAN内の他端末からアクセス

サーバーを起動したPCのLAN内IPアドレスを確認し、同じWi-FiにつながっているスマホやPCのブラウザから `http://<サーバーのIPアドレス>:8000` を開いてください。

```bash
# サーバーPCのIPアドレスを調べる例（Linux/macOS）
hostname -I
```

## 使い方

1. 全員が同じ「ルームコード」を入力して「ルームに参加」を押す（自分の名前は自動で入るが変更可能）。
2. 「同じルームの端末」一覧に相手が表示されたら、送受信したい相手の「接続」を押してP2P接続を開始する（自動では繋がらない — 個別に接続が必要）。
3. 「接続済み」になったら、「共有する」パネルからテキストを送信、またはファイルをドラッグ＆ドロップ／クリックで選択して送信する。
4. 受信したテキストは「テキストのやり取り」欄にカード表示され、受信したファイルは自動でブラウザのダウンロードとして保存される。
5. 画面下の「送受信ログ」で、シグナリング・P2P接続・送受信の様子を確認できる。devtoolsが使いにくい環境向けに「全文をテキスト表示（コピー用）」ボタンもある。

## アーキテクチャ

- **バックエンド (`server.py`)**: FastAPI + WebSocketで、ルームへのjoin/leaveの通知と、SDP・ICE candidateの中継のみを行う。ファイル・テキストの実データは一切通過しない。
- **STUNサーバー (`stun_server.py`)**: RFC 5389のBinding Requestのみに対応した最小実装。Chrome系ブラウザがWebRTCのhost candidateをmDNS匿名ホスト名にする挙動への対策として、LAN内で完結する実IPアドレス解決の手段を提供する。
- **フロントエンド (`static/index.html`)**: 1ファイルのVanilla JS。`RTCPeerConnection` + `RTCDataChannel`でブラウザ間の直接通信を行い、ファイルは16KBチャンクに分割し`bufferedAmount`を見ながら送信する。

## プロジェクト構成

```
WebSend/
├── server.py           # シグナリングサーバー（FastAPI）
├── stun_server.py       # LAN内完結の最小STUNサーバー
├── static/
│   └── index.html       # フロントエンド（1ファイル）
├── scripts/
│   └── generate_design.py  # design.png生成スクリプト（Pillow）
├── design.png            # UIモックアップ画像
├── design.md              # UI仕様書
└── CLAUDE.md               # 開発方針・技術的な学びの記録
```

## トラブルシューティング

- **同じルームなのに接続できない/失敗する**: まずルーターの「APアイソレーション（クライアント分離）」設定を確認してください。同じWi-Fiでも端末同士の直接通信をブロックする設定がある場合、P2P接続はできません。
- **特定のブラウザだけ失敗する**: 送受信ログの「全文をテキスト表示（コピー用）」でログを確認してください。起動時に出る「RTCPeerConnection: false」は、そのブラウザがWebRTCに対応していないことを意味します（Haiku OSのWebPositiveで確認済み。Firefox等の別ブラウザを使ってください）。
- **ファイアウォールがある環境**: STUNサーバーのUDP 3478と、WebRTCのDataChannelが使う動的なUDPポートがブロックされていないか確認してください。

## 開発ドキュメントについて

技術スタックの選定理由や実装中に得た知見（Haiku OS対応やSTUNサーバー導入の経緯など）は`CLAUDE.md`に、UI仕様は`design.md`にまとめてあります。
