# ToneBridge Expo React Native モバイルアプリ

## 📱 概要
ToneBridgeのiOS/Android対応モバイルアプリケーション。Expo Goでの即座のテスト、OTA更新、ネイティブ機能へのアクセスを提供。

## 🎯 主要機能

### コア機能
- ✅ テキスト変換（7種類のトランスフォーメーション）
- ✅ リアルタイム分析
- ✅ 変換履歴管理
- ✅ カスタム辞書
- ✅ オフライン対応（キャッシュ）
- ✅ WebSocket リアルタイム通信
- ✅ プッシュ通知
- ✅ ダークモード対応

### iOS/Android特有機能
- 📷 カメラでテキストスキャン（OCR）
- 🖼️ 画像からテキスト抽出
- 🎤 音声入力
- 📤 共有エクステンション
- 🔐 生体認証（Face ID/Touch ID/指紋）

## 🏗️ プロジェクト構造

```
mobile-app/
├── App.tsx                      # メインエントリポイント
├── app.json                     # Expo設定
├── package.json                 # 依存関係
├── tsconfig.json               # TypeScript設定
├── babel.config.js             # Babel設定
├── metro.config.js             # Metro設定
├── .env                        # 環境変数
├── assets/                     # 静的アセット
│   ├── icon.png               # アプリアイコン (1024x1024)
│   ├── splash.png              # スプラッシュ画面 (1284x2778)
│   ├── adaptive-icon.png      # Android適応アイコン
│   └── fonts/                 # カスタムフォント
├── src/
│   ├── components/            # 再利用可能コンポーネント
│   │   ├── common/
│   │   ├── transform/
│   │   └── ui/
│   ├── screens/              # 画面コンポーネント
│   │   ├── auth/
│   │   ├── home/
│   │   ├── transform/
│   │   ├── history/
│   │   ├── settings/
│   │   └── profile/
│   ├── navigation/           # ナビゲーション設定
│   │   ├── RootNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   └── MainNavigator.tsx
│   ├── services/            # APIサービス
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── storage.ts
│   ├── hooks/              # カスタムフック
│   │   ├── useAuth.ts
│   │   ├── useTransform.ts
│   │   └── useWebSocket.ts
│   ├── contexts/           # React Context
│   │   ├── AuthContext.tsx
│   │   ├── ThemeContext.tsx
│   │   └── WebSocketContext.tsx
│   ├── utils/             # ユーティリティ関数
│   │   ├── validation.ts
│   │   ├── format.ts
│   │   └── constants.ts
│   ├── types/             # TypeScript型定義
│   │   ├── api.types.ts
│   │   ├── navigation.types.ts
│   │   └── models.types.ts
│   ├── config/           # アプリ設定
│   │   ├── toast.ts
│   │   ├── theme.ts
│   │   └── api.config.ts
│   └── store/           # 状態管理（Zustand/Redux）
│       ├── authStore.ts
│       └── transformStore.ts
└── __tests__/          # テストファイル
```

## 🚀 セットアップ

### 1. 開発環境準備

```bash
# Node.js 18以上が必要
node --version

# Expo CLIインストール
npm install -g expo-cli eas-cli

# プロジェクト依存関係インストール
cd mobile-app
npm install

# iOS開発の場合（Macのみ）
cd ios && pod install
```

### 2. 環境変数設定

`.env` ファイルを作成:
```env
EXPO_PUBLIC_API_URL=https://api.tonebridge.io
EXPO_PUBLIC_DEV_API_URL=http://localhost:8082
EXPO_PUBLIC_WS_URL=wss://ws.tonebridge.io
EXPO_PUBLIC_DEV_WS_URL=ws://localhost:3001
```

### 3. 開発サーバー起動

```bash
# Expo Go アプリで開発
npm start

# iOS シミュレーター
npm run ios

# Android エミュレーター
npm run android

# Web ブラウザ
npm run web
```

## 📲 Expo Go でのテスト

### iOS
1. App StoreからExpo Goをダウンロード
2. `npm start`実行後のQRコードをスキャン
3. アプリが自動的に起動

### Android
1. Google PlayからExpo Goをダウンロード
2. QRコードをスキャンまたはURLを入力
3. アプリが自動的に起動

## 🔑 主要な依存関係

### Core
- **expo**: ~49.0.0 - Expoフレームワーク
- **react**: 18.2.0 - React
- **react-native**: 0.72.6 - React Native
- **typescript**: ^5.1.3 - TypeScript

### Navigation
- **@react-navigation/native**: ^6.1.9
- **@react-navigation/bottom-tabs**: ^6.5.11
- **@react-navigation/stack**: ^6.3.20

### UI Components
- **react-native-paper**: ^5.11.4 - Material Design
- **react-native-vector-icons**: ^10.0.3 - アイコン
- **react-native-reanimated**: ~3.3.0 - アニメーション

### State Management
- **@tanstack/react-query**: ^5.17.0 - サーバー状態管理
- **zustand**: ^4.4.7 - クライアント状態管理（追加予定）

### API & WebSocket
- **axios**: ^1.6.5 - HTTP クライアント
- **socket.io-client**: ^4.7.4 - WebSocket

### Storage & Security
- **expo-secure-store**: ~12.3.1 - セキュアストレージ
- **@react-native-async-storage/async-storage**: 1.18.2

### Forms & Validation
- **react-hook-form**: ^7.48.2 - フォーム管理
- **yup**: ^1.3.3 - バリデーション（追加予定）

## 📦 ビルド & デプロイ

### EAS Build (推奨)

```bash
# EAS CLIログイン
eas login

# プロジェクト初期化
eas build:configure

# 開発ビルド
eas build --profile development --platform ios
eas build --profile development --platform android

# プレビュービルド（内部テスト用）
eas build --profile preview --platform all

# 本番ビルド
eas build --profile production --platform all
```

### eas.json 設定

```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "buildNumber": "auto"
      },
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "ios": {
        "buildNumber": "auto"
      },
      "android": {
        "buildType": "app-bundle",
        "versionCode": "auto"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your@email.com",
        "ascAppId": "your-app-id"
      },
      "android": {
        "track": "production",
        "releaseStatus": "completed"
      }
    }
  }
}
```

## 🎨 UIコンポーネント例

### TransformInput Component
```tsx
import React from 'react';
import { TextInput, Button, Surface } from 'react-native-paper';

export const TransformInput: React.FC = () => {
  const [text, setText] = useState('');
  const [transformType, setTransformType] = useState('soften');
  
  const handleTransform = async () => {
    const result = await transformAPI.transform({
      text,
      type: transformType,
      options: { tone_level: 2 }
    });
    // Handle result
  };

  return (
    <Surface style={styles.container}>
      <TextInput
        label="入力テキスト"
        value={text}
        onChangeText={setText}
        multiline
        numberOfLines={4}
      />
      <Button mode="contained" onPress={handleTransform}>
        変換
      </Button>
    </Surface>
  );
};
```

## 🔒 セキュリティ

### トークン管理
```typescript
// Secure Store使用
import * as SecureStore from 'expo-secure-store';

// トークン保存
await SecureStore.setItemAsync('access_token', token);

// トークン取得
const token = await SecureStore.getItemAsync('access_token');

// トークン削除
await SecureStore.deleteItemAsync('access_token');
```

### 生体認証
```typescript
import * as LocalAuthentication from 'expo-local-authentication';

const authenticate = async () => {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  
  if (hasHardware && isEnrolled) {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'ToneBridgeにログイン',
      fallbackLabel: 'パスコードを使用',
    });
    
    if (result.success) {
      // 認証成功
    }
  }
};
```

## 📊 パフォーマンス最適化

### 1. メモ化
```typescript
import { memo, useMemo, useCallback } from 'react';

const MemoizedComponent = memo(({ data }) => {
  const processedData = useMemo(() => 
    expensiveProcess(data), [data]
  );
  
  const handlePress = useCallback(() => {
    // Handle press
  }, []);
  
  return <View>{/* ... */}</View>;
});
```

### 2. リスト最適化
```typescript
import { FlatList } from 'react-native';

<FlatList
  data={items}
  keyExtractor={(item) => item.id}
  renderItem={renderItem}
  initialNumToRender={10}
  maxToRenderPerBatch={10}
  windowSize={10}
  removeClippedSubviews={true}
  getItemLayout={(data, index) => ({
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
/>
```

### 3. 画像最適化
```typescript
import { Image } from 'expo-image';

<Image
  source={{ uri: imageUrl }}
  style={styles.image}
  contentFit="cover"
  placeholder={blurhash}
  transition={200}
  cachePolicy="memory-disk"
/>
```

## 🧪 テスト

### ユニットテスト
```bash
npm test
```

### E2Eテスト（Detox）
```bash
# iOS
detox test --configuration ios.sim.debug

# Android
detox test --configuration android.emu.debug
```

## 📱 App Store / Google Play 提出

### iOS App Store
1. Apple Developer Program登録（$99/年）
2. App Store Connect でアプリ作成
3. `eas submit -p ios`
4. TestFlight でベータテスト
5. App Store審査提出

### Google Play Store
1. Google Play Developer登録（$25 一回）
2. Google Play Console でアプリ作成
3. `eas submit -p android`
4. 内部テスト → クローズドテスト → オープンテスト
5. 本番リリース

## 🐛 トラブルシューティング

### よくある問題

#### Metro バンドラーエラー
```bash
# キャッシュクリア
npx expo start -c

# node_modules再インストール
rm -rf node_modules
npm install
```

#### iOS ビルドエラー
```bash
cd ios
pod deintegrate
pod install
```

#### Android ビルドエラー
```bash
cd android
./gradlew clean
cd ..
npx react-native run-android
```

## 🔄 OTA アップデート

```bash
# アップデート公開
eas update --branch production --message "Bug fixes"

# チャンネル設定
eas update:configure
```

## 📈 分析 & モニタリング

### Sentry 統合
```typescript
import * as Sentry from 'sentry-expo';

Sentry.init({
  dsn: 'YOUR_SENTRY_DSN',
  enableInExpoDevelopment: false,
  debug: __DEV__,
});
```

### Analytics
```typescript
import * as Analytics from 'expo-analytics-amplitude';

Analytics.initializeAsync('YOUR_API_KEY');
Analytics.logEventAsync('transform_completed', {
  type: 'soften',
  length: text.length,
});
```

## 📚 参考資料

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [React Navigation](https://reactnavigation.org/)
- [React Native Paper](https://callstack.github.io/react-native-paper/)

---

*Last Updated: 2025-01-15*
*Version: 1.0.0*
*Status: Development*