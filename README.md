# 軽量なろうリーダー (Narou Reader)

「小説家になろう」の小説を軽量なインターフェースで読むためのWebアプリケーションです。3DSなどの低機能ブラウザでも快適に利用できるよう設計されています。

A lightweight web application for reading novels from "Shōsetsuka ni Narō" (小説家になろう) with a simple interface optimized for low-powered browsers like the Nintendo 3DS.

## 特徴 (Features)

- 📚 **小説検索**: 作品名や作者名で小説を検索
- 📖 **目次表示**: 章立てとエピソード一覧を見やすく表示
- 📱 **軽量設計**: 3DSなどの低機能ブラウザに最適化
- 🔤 **ルビ対応**: ふりがなを括弧表記に変換して表示
- 🎯 **シンプルUI**: 読書に集中できるミニマルなデザイン
- 🚀 **高速ナビゲーション**: 前の話・次の話への素早い移動

## 技術スタック (Tech Stack)

- **Backend**: Python 3.x + Flask
- **Web Scraping**: requests + BeautifulSoup4
- **Frontend**: HTML + CSS (埋め込みテンプレート)
- **Production Server**: Gunicorn

## インストール (Installation)

### 必要環境 (Requirements)

- Python 3.7以上
- インターネット接続

### セットアップ手順 (Setup)

1. **リポジトリをクローン**
```bash
git clone https://github.com/raayucorp/narou-reader.git
cd narou-reader
```

2. **依存関係をインストール**
```bash
pip install -r requirements.txt
```

3. **アプリケーションを起動**

**開発環境の場合:**
```bash
python app.py
```
アプリケーションは `http://localhost:8000` で起動します。

**本番環境の場合:**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 使い方 (Usage)

### 1. 小説を検索
- トップページで作品名や作者名を入力して検索
- 検索結果から読みたい小説を選択

### 2. 目次を確認
- 小説の詳細ページで章構成とエピソード一覧を確認
- あらすじも表示されます

### 3. 小説を読む
- エピソードをクリックして本文を表示
- ページ下部のナビゲーションで前後の話に移動

### URL構造

```
/                           # トップページ（検索）
/search?q={検索語}&page={ページ}  # 検索結果
/novel/{ncode}              # 目次ページ
/novel/{ncode}/{chapter}    # 本文表示
```

## API仕様 (API Specification)

### 検索エンドポイント
```
GET /search?q={query}&page={page_number}
```

### 目次エンドポイント
```
GET /novel/{ncode}?p={page_number}
```

### 本文表示エンドポイント
```
GET /novel/{ncode}/{chapter}
```

## 設定 (Configuration)

### 重要な設定項目

- `BASE_URL`: 小説家になろうのベースURL
- `USER_AGENT`: スクレイピング時のUser-Agent
- `HEADERS`: HTTPリクエストヘッダー

### カスタマイズ

CSSスタイルは `BASE_TEMPLATE` 内で定義されており、必要に応じて外観をカスタマイズできます。

## 法的事項・免責事項 (Legal Notice)

⚠️ **重要**: このアプリケーションは「小説家になろう」のコンテンツをスクレイピングして表示します。

- **個人利用の範囲**でのみご利用ください
- **商用利用は禁止**です
- サーバーへの負荷軽減のため、リクエスト間に1秒の待機時間を設けています
- 「小説家になろう」の利用規約を遵守してください
- 作者および「小説家になろう」の権利を尊重してください

### 著作権

- 表示される小説の内容は各作者に著作権があります
- 本アプリケーションのソースコードの著作権は開発者にあります

## 開発・貢献 (Development & Contributing)

### 開発環境のセットアップ

```bash
# 開発用サーバーを起動（デバッグモード）
python app.py
```

### 貢献方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発ガイドライン

- Pythonコードは[PEP 8](https://pep8.org/)に従ってください
- 新機能には適切なコメントを追加してください
- サーバー負荷を考慮した実装を心がけてください

## トラブルシューティング (Troubleshooting)

### よくある問題

**Q: 「検索結果の取得に失敗しました」と表示される**
A: インターネット接続を確認し、しばらく時間をおいてから再試行してください。

**Q: 本文が正しく表示されない**
A: 「小説家になろう」のサイト構造が変更された可能性があります。最新版への更新を確認してください。

**Q: 3DSで表示が崩れる**
A: CSSは3DS向けに最適化されていますが、一部の表示に制限がある場合があります。

## ライセンス (License)

このプロジェクトはMITライセンス相当の条件で公開されています。詳細は開発者にお問い合わせください。

## 更新履歴 (Changelog)

- **v1.0.0**: 初期リリース
  - 小説検索機能
  - 目次表示機能
  - 本文読み込み機能
  - 3DS対応軽量デザイン

## 作者 (Author)

開発・メンテナンス: [raayucorp](https://github.com/raayucorp)

## 関連リンク (Related Links)

- [小説家になろう](https://syosetu.com/) - 対象サイト
- [Flask Documentation](https://flask.palletsprojects.com/) - 使用フレームワーク

---

*このプロジェクトは個人的な学習・利用目的で作成されており、「小説家になろう」の公式プロジェクトではありません。*