# WebSend

LAN内（同一Wi-Fi）に閉じたP2Pファイル・テキスト共有ボード。インターネット不要、サーバーにデータを一切残さない。1日限定ハッカソン会場での利用を想定。

## 目的 / 制約

- 同じLAN上のスマホ・PC・**Haiku OS**から、インストール不要・ビルド不要でアクセスできること。
  - **既知の制約: Haiku OS標準ブラウザのWebPositiveは`RTCPeerConnection`自体が未実装（実機で確認: `typeof RTCPeerConnection === 'undefined'`）。ポリフィル不可能なプラットフォーム制約のため、Haiku OSでは代わりにFirefoxを使うこと（実機でP2P接続・テキスト送信・ファイル送信とも動作確認済み）。** ハッカソン会場でHaiku端末を使う場合は事前にFirefoxを用意してもらう。
- サーバーはWebRTCの「シグナリング（接続情報の仲介）」のみを行い、ファイル・テキストの実データはサーバーを経由しない。
- サーバー側にデータベースやファイル保存を一切行わない（完全ステートレス、メモリ上の接続情報のみ）。
- 外部CDNには一切依存しない（ハッカソン会場はインターネットが無い前提）。Tailwindはインターネット経由のCDN `<script src="https://cdn.tailwindcss.com">` ではなく、`static/vendor/tailwind.js` にベンダリングしたPlay CDNスクリプトをサーバーから配信する（`server.py`で`/static`をマウント）。ビルドツール（npm/webpack等）は使わない。

## 技術スタック

### バックエンド: Python (FastAPI + WebSocket)

- 役割はWebRTCシグナリングの仲介のみ：
  - 同一LAN上のクライアント同士が「部屋（ルーム）」に入り、SDP/ICE candidateをWebSocket経由で交換する。
  - ファイル本体・テキスト本体はサーバーを一切通過しない（RTCDataChannelで直接P2P転送）。
- 保存領域なし：DBなし、ディスク書き込みなし。ルーム状態はプロセスメモリ上の辞書のみで、再起動で消える。
- 依存はできるだけ薄く：`fastapi`, `uvicorn`, `websockets`程度。
- **`uvicorn`は拡張なし（`uvicorn[standard]`にしない）。** Raspberry Pi 3B+ (armv7 / Buster)実機で検証した際、`[standard]`が引き込む`uvloop`がプリビルドwheelを持たずソースからのCビルドになり、非力なARM機では現実的な時間で終わらなかった（数分待っても未完了）。`uvicorn`単体 + `websockets`ならwheelインストールで数十秒。ハッカソン会場の低スペック機でのセットアップ時間を優先し、パフォーマンス最適化拡張は使わない。

### フロントエンド: ビルド不要の単一HTMLファイル

- `index.html` 1ファイルに HTML + Vanilla JS を同梱。Tailwind CSSはローカルにベンダリングした`static/vendor/tailwind.js`を`<script src="/static/vendor/tailwind.js">`で読み込む（インターネット不要）。
- フレームワーク（React/Vue等）不使用、npm/bundler不使用 — Haiku OS標準ブラウザ（WebPositive）は最新JS機能やビルドツールの実行環境を持たないため。
- Vanilla JSはES2017程度の互換性を目安にする（WebPositiveの実装状況に合わせて動作確認しながら調整）。

### P2P通信: WebRTC

- `RTCPeerConnection` + `RTCDataChannel` を使い、シグナリングサーバーを介さず端末間で直接データ（ファイル／テキスト）をやり取りする。
- **シグナリングサーバーに自前のSTUNサーバー（UDP 3478、`stun_server.py`）を同居させている。** インターネットのSTUN（stun.l.google.com等）は使わない。
  - 背景: Chrome系ブラウザはプライバシー保護のためWebRTCのhost candidateをmDNS匿名ホスト名（`xxxxxxxx-....local`）にする。自前STUNのBinding Responseで「観測した送信元IP:port」を返すことで、mDNSに隠されない実IPアドレスのcandidate（srflx）も得られるようにしている。LAN内で完結するのでインターネット非接続でも動作する。
  - **実機検証済み**: Windows↔Linux間のPCでこのSTUN込みの構成でP2P接続・テキスト送信・ファイル送信が正常動作することを確認。
- 大きいファイルはDataChannel上で16KBチャンクに分割して送信し、`dc.bufferedAmount`を見てbackpressure制御する。
- offer/answer/ICE candidateをシグナリングで送る際は、プレーンオブジェクトに詰め替えてからJSON化している。`RTCSessionDescription`/`RTCIceCandidate`のプロパティはブラウザ実装によってprototypeのgetterになっている場合があり、そのまま`JSON.stringify()`すると`{}`になってしまう懸念があるため（cross-browser対策）。
- 送受信ログに「全文をテキスト表示（コピー用）」ボタンがある。devtoolsが使えない/使いにくい環境（Haiku等）から、ブラウザ情報・SDP要約・エラー内容などの診断情報をコピペで報告してもらうためのもの。

## 実行方法

- `uvicorn`等で `0.0.0.0:8000` にバインドし、LAN内の他端末からホストPCのIPアドレス（例: `http://192.168.x.x:8000`）でアクセスできるようにする。
- HTTPでの配信を前提とする（LAN内・自己署名証明書なしでWebRTCを使うため、`localhost`以外はHTTPS必須というブラウザ制約に注意 — 動作確認時に必要なら自己署名証明書 or Chromeの`--unsafely-treat-insecure-origin-as-secure`相当の回避策を検討）。

## 開発の進め方

1. **デザイン先行**: 画面デザインを`design.png`（Pillowで生成した完成予想図）と`design.md`（UI要素仕様）として先にまとめる。
2. **小さい単位で実装し、都度動作確認する**:
   - ① WebSocketシグナリング（ルーム参加、SDP/ICE candidateの中継）
   - ② P2P接続確立（RTCPeerConnection、DataChannel open確認）
   - ③ ファイル・テキスト送受信（チャンク分割、進捗表示、受信側での再構成）
   - 1機能実装 → その場で実際に動かして確認 → 結果報告 → 次の機能へ、を徹底する。

## コーディング方針

- コメントは最小限（自明でないWHYのみ）。
- 抽象化やエラーハンドリングは今回のスコープ（LAN内・信頼できる参加者間の一時的な共有）に見合った分だけ。
- サーバー側にログ以外の永続化コードを書かない。
