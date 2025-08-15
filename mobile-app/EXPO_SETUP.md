# ToneBridge Mobile App - Expo セットアップ・動作確認手順

## 前提条件

- Node.js 16.x以上がインストール済み
- npm または yarnがインストール済み
- Expo Goアプリがスマートフォンにインストール済み（開発用）
- macOS（iOSシミュレータを使用する場合）
- Xcodeがインストール済み（iOSシミュレータを使用する場合）

## 1. 初期セットアップ

### 1.1 依存関係のインストール

```bash
cd mobile-app
npm install
```

### 1.2 Expo CLIのグローバルインストール（オプション）

```bash
npm install -g expo-cli
```

### 1.3 EAS CLIのインストール（ビルド・デプロイ用）

```bash
npm install -g eas-cli
```

## 2. 環境変数の設定

### 2.1 開発用環境変数ファイルの作成

```bash
cp .env.example .env
```

### 2.2 環境変数の編集

`.env`ファイルを開き、以下の値を設定：

```env
# API設定
EXPO_PUBLIC_API_URL=http://localhost:8082
EXPO_PUBLIC_WS_URL=ws://localhost:3001

# 開発設定
EXPO_PUBLIC_ENV=development
```

## 3. 開発サーバーの起動

### 3.1 バックエンドサービスの起動

別のターミナルで、ToneBridgeのバックエンドを起動：

```bash
# プロジェクトルートから
make up
# または
cd infrastructure && docker-compose up -d
```

### 3.2 Expoの開発サーバー起動

```bash
cd mobile-app
npm start
# または
expo start
```

## 4. アプリの動作確認

### 4.1 実機での確認（推奨）

1. Expo開発サーバーが起動したら、QRコードが表示されます
2. **iOS**: Expo Goアプリでカメラを使ってQRコードをスキャン
3. **Android**: Expo Goアプリ内のQRコードスキャナーを使用
4. アプリが自動的に読み込まれ、起動します

### 4.2 iOSシミュレータでの確認（macOSのみ）

```bash
# Expo開発サーバー起動後
i  # iOSシミュレータで開く
```

### 4.3 Androidエミュレータでの確認

```bash
# Android Studioでエミュレータを起動後
a  # Androidエミュレータで開く
```

### 4.4 Webブラウザでの確認

```bash
# Expo開発サーバー起動後
w  # Webブラウザで開く
```

## 5. 基本機能の動作テスト

### 5.1 接続テスト

1. アプリが起動することを確認
2. スプラッシュ画面が表示されることを確認
3. ログイン画面またはホーム画面が表示されることを確認

### 5.2 APIサーバー接続テスト

1. 開発者メニューを開く（実機を振る、またはCmd+D/Ctrl+M）
2. ネットワークログを確認
3. APIエンドポイント（http://localhost:8082）への接続を確認

### 5.3 基本的な機能テスト

- [ ] ログイン/サインアップ機能
- [ ] テキスト変換機能
- [ ] 変換履歴の表示
- [ ] 設定画面の表示
- [ ] WebSocket接続（リアルタイム機能）

## 6. トラブルシューティング

### 6.1 「Metro bundler」エラー

```bash
# Metro キャッシュをクリア
npx expo start -c
```

### 6.2 依存関係の問題

```bash
# node_modulesを削除して再インストール
rm -rf node_modules
npm install
```

### 6.3 iOSシミュレータが起動しない

```bash
# Xcodeを開いて、シミュレータを手動で起動
open -a Simulator
```

### 6.4 ネットワーク接続エラー

開発環境の場合、以下を確認：
- バックエンドサービスが起動しているか
- ファイアウォール設定
- `localhost`の代わりに、PCのIPアドレスを使用

```javascript
// 例: api.tsで
const API_URL = Platform.select({
  ios: 'http://192.168.1.100:8082', // あなたのPCのIPアドレス
  android: 'http://10.0.2.2:8082',   // Androidエミュレータ用
  default: 'http://localhost:8082'
});
```

### 6.5 Expo Goアプリでプロジェクトが開けない

- Expo GoアプリとExpo SDKのバージョン互換性を確認
- 同じWi-Fiネットワークに接続されているか確認
- ファイアウォール設定を確認

## 7. ホットリロード設定

### 7.1 Fast Refreshの有効化

開発者メニューから「Enable Fast Refresh」を選択

### 7.2 コード変更の確認

1. `src/screens/home/TransformScreen.tsx`を編集
2. 保存後、アプリが自動的にリロードされることを確認

## 8. デバッグツール

### 8.1 React Developer Tools

```bash
# 別のターミナルで
npx react-devtools
```

### 8.2 Flipper（オプション）

```bash
# Flipperをインストール後、アプリに接続
npx expo install expo-dev-client
```

## 9. パフォーマンス確認

### 9.1 開発者メニューから確認

- Show Perf Monitor: パフォーマンスモニターを表示
- Enable FPS Monitor: FPSモニターを表示

### 9.2 メモリ使用量の確認

Chrome DevToolsまたはSafari Web Inspectorを使用

## 10. ビルド準備の確認

### 10.1 アセットの確認

```bash
# アセットが正しく配置されているか確認
ls -la assets/
```

必要なファイル：
- icon.png (1024x1024)
- splash.png (1242x2436)
- adaptive-icon.png (1024x1024)
- favicon.png (48x48)

### 10.2 app.json設定の検証

```bash
# Expo設定の検証
expo doctor
```

## 次のステップ

動作確認が完了したら、[IOS_DEPLOYMENT.md](./IOS_DEPLOYMENT.md)を参照してiOS App Storeへの公開準備を進めてください。

## 参考リンク

- [Expo Documentation](https://docs.expo.dev/)
- [Expo Go](https://expo.dev/client)
- [React Native Documentation](https://reactnative.dev/)
- [ToneBridge API Documentation](../docs/API_REFERENCE.md)