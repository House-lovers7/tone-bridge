# ToneBridge App Assets

このディレクトリには、アプリのアイコンやスプラッシュ画面などのアセットファイルを配置します。

## 必要なファイル

### 1. アプリアイコン
- **ファイル名**: `icon.png`
- **サイズ**: 1024x1024px
- **形式**: PNG（透過なし）
- **説明**: App Storeおよびデバイス上で表示されるアプリアイコン

### 2. スプラッシュ画面
- **ファイル名**: `splash.png`
- **サイズ**: 1242x2436px（iPhone向け）
- **形式**: PNG
- **説明**: アプリ起動時に表示されるスプラッシュ画面

### 3. アダプティブアイコン（Android用）
- **ファイル名**: `adaptive-icon.png`
- **サイズ**: 1024x1024px
- **形式**: PNG（透過可）
- **説明**: Androidのアダプティブアイコン用の前景画像

### 4. ファビコン（Web用）
- **ファイル名**: `favicon.png`
- **サイズ**: 48x48px
- **形式**: PNG
- **説明**: Webブラウザで表示されるファビコン

## アセット生成のヒント

1. **高解像度から開始**: 常に最大サイズ（1024x1024px）から作成し、必要に応じてダウンスケール
2. **ブランドカラー**: ToneBridgeのブランドカラーを使用
3. **シンプルなデザイン**: 小さいサイズでも認識しやすいシンプルなデザインを採用
4. **背景色**: スプラッシュ画面の背景色は `app.json` の設定と一致させる

## アセット生成ツール

- [Expo Icon Builder](https://buildicon.netlify.app/)
- [App Icon Generator](https://appicon.co/)
- [Figma](https://www.figma.com/) - デザイン作成用

## 注意事項

- アイコンに透過部分を含めない（iOS要件）
- Apple Human Interface Guidelinesに準拠
- Google Material Design Guidelinesに準拠