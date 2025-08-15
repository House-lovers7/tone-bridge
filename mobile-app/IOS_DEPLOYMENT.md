# ToneBridge iOS App Store 公開手順書

## 前提条件

- [ ] Apple Developer Program に登録済み（年間$99）
- [ ] App Store Connect アカウント作成済み
- [ ] Expo/React Nativeアプリの開発完了
- [ ] 必要なアセット（アイコン、スクリーンショット）準備済み
- [ ] プライバシーポリシーとサポートページ準備済み

## 1. Apple Developer での準備

### 1.1 App ID の作成

1. [Apple Developer](https://developer.apple.com) にログイン
2. 「Certificates, Identifiers & Profiles」を選択
3. 「Identifiers」→「+」をクリック
4. 「App IDs」を選択して「Continue」
5. 以下を設定：
   - **Description**: ToneBridge
   - **Bundle ID**: `com.tonebridge.app`（app.jsonと一致させる）
   - **Capabilities**: 必要な機能を選択

### 1.2 必要な Capabilities

アプリで使用する機能に応じて有効化：
- [ ] Push Notifications（プッシュ通知を使用する場合）
- [ ] Sign in with Apple（Apple IDログインを使用する場合）
- [ ] Associated Domains（ディープリンクを使用する場合）

## 2. App Store Connect での準備

### 2.1 新規アプリの作成

1. [App Store Connect](https://appstoreconnect.apple.com) にログイン
2. 「マイApp」→「+」→「新規App」
3. 以下を入力：
   - **プラットフォーム**: iOS
   - **名前**: ToneBridge
   - **プライマリ言語**: 日本語
   - **バンドルID**: 作成したApp IDを選択
   - **SKU**: tonebridge-001（任意の一意な文字列）
   - **ユーザーアクセス**: フルアクセス

### 2.2 アプリ情報の入力

#### 基本情報
- **カテゴリ**: ビジネス / 仕事効率化
- **コンテンツ権利**: 適切なオプションを選択
- **年齢制限指定**: 4+（暴力的なコンテンツなし）

#### 価格とAvailability
- **価格**: 無料 / 有料を選択
- **配信地域**: 日本を含む配信したい地域を選択

## 3. EAS Build の設定

### 3.1 eas.json の更新

```json
{
  "submit": {
    "production": {
      "ios": {
        "appleId": "your-email@example.com",
        "ascAppId": "1234567890",
        "appleTeamId": "TEAM_ID_HERE"
      }
    }
  }
}
```

必要な情報の取得方法：
- **appleId**: Apple IDのメールアドレス
- **ascAppId**: App Store Connectでアプリ作成後に確認
- **appleTeamId**: Apple Developer Membershipページで確認

### 3.2 EAS にログイン

```bash
eas login
```

### 3.3 プロジェクトの設定

```bash
cd mobile-app
eas build:configure
```

## 4. アプリのビルド

### 4.1 app.json の最終確認

```json
{
  "expo": {
    "version": "1.0.0",
    "ios": {
      "bundleIdentifier": "com.tonebridge.app",
      "buildNumber": "1"
    }
  }
}
```

### 4.2 プロダクションビルドの実行

```bash
eas build --platform ios --profile production
```

初回実行時の選択：
- 「Let EAS manage your credentials」を推奨
- Apple IDとパスワードを入力
- 2ファクタ認証コードを入力

### 4.3 ビルド状況の確認

```bash
eas build:list --platform ios
```

または[Expo Dashboard](https://expo.dev)で確認

## 5. App Store Connect へのアップロード

### 5.1 自動提出（推奨）

```bash
eas submit --platform ios --profile production
```

最新のビルドを選択するか、ビルドIDを指定：
```bash
eas submit --platform ios --id=BUILD_ID
```

### 5.2 手動提出（オプション）

1. ビルドをダウンロード
2. Xcode → Open Developer Tool → Application Loader
3. IPAファイルをアップロード

## 6. App Store 提出準備

### 6.1 スクリーンショット

必要なサイズ（最低限）：
- **iPhone 6.7"**: 1290 x 2796px
- **iPhone 6.5"**: 1242 x 2688px または 1284 x 2778px
- **iPhone 5.5"**: 1242 x 2208px
- **iPad 12.9"**: 2048 x 2732px

推奨ツール：
- [Screenshot](https://screenshot.help/)
- [Previewed](https://previewed.app/)

### 6.2 アプリの説明

#### プロモーションテキスト（170文字以内）
```
エンジニアと非エンジニアの間のコミュニケーションを円滑にするAIアシスタント。専門用語を分かりやすく翻訳し、メッセージの温度感を調整します。
```

#### 説明（4000文字以内）
```
ToneBridgeは、技術チームとビジネスチーム間のコミュニケーションギャップを解消する革新的なツールです。

【主な機能】
• テキストトーン変換：技術的な文章を温かみのある表現に自動変換
• 専門用語翻訳：難しい技術用語を分かりやすい言葉に置き換え
• メッセージ構造化：長文や曖昧な文章を整理して要点を抽出
• 優先度判定：メッセージの緊急度を自動判定
• リアルタイム同期：チーム間でのスムーズな情報共有

【こんな方におすすめ】
• エンジニアとのコミュニケーションに悩むマネージャー
• 非技術者への説明に困るエンジニア
• チーム間の連携を改善したいプロジェクトマネージャー

【使い方】
1. テキストを入力またはペースト
2. 変換タイプを選択
3. AIが最適な表現に変換
4. 結果をコピーして使用

プライバシーとセキュリティを重視し、すべての通信は暗号化されています。
```

#### キーワード（100文字以内）
```
コミュニケーション,AI,翻訳,ビジネス,エンジニア,チーム,効率化,テキスト変換,専門用語
```

### 6.3 その他の必須項目

- **サポートURL**: https://tonebridge.io/support
- **プライバシーポリシーURL**: https://tonebridge.io/privacy
- **著作権**: © 2024 ToneBridge Inc.

### 6.4 App Review情報

テストアカウント（必要な場合）：
```
メールアドレス: test@tonebridge.io
パスワード: TestPass123!
```

連絡先情報：
```
名前: [担当者名]
電話番号: [電話番号]
メールアドレス: [メールアドレス]
```

## 7. 審査提出

### 7.1 ビルドの選択

1. App Store Connect → 「マイApp」→ ToneBridge
2. 「iOS App」→ バージョンを選択
3. 「ビルド」セクションで「+」をクリック
4. アップロードしたビルドを選択

### 7.2 提出前の最終チェック

- [ ] すべての必須項目が入力済み
- [ ] スクリーンショットがアップロード済み
- [ ] アプリアイコンが設定済み
- [ ] 年齢制限指定が適切
- [ ] 価格設定が正しい
- [ ] 配信地域が選択済み

### 7.3 審査へ提出

1. 「審査へ提出」をクリック
2. Export Compliance情報を入力
3. 広告識別子（IDFA）の使用について回答
4. 「提出」をクリック

## 8. 審査対応

### 8.1 審査期間

- 通常: 24-48時間
- 初回提出: 最大7日間

### 8.2 よくあるリジェクト理由と対策

#### ガイドライン違反
- **問題**: 不適切なコンテンツ、誤解を招く説明
- **対策**: Apple のガイドラインを詳細に確認

#### 機能不足
- **問題**: 最小限の機能要件を満たしていない
- **対策**: 独自の価値提供を明確にする

#### クラッシュ・バグ
- **問題**: アプリが正常に動作しない
- **対策**: 徹底的なテストを実施

#### メタデータの問題
- **問題**: スクリーンショットと実際のアプリが異なる
- **対策**: 最新のスクリーンショットを使用

### 8.3 リジェクト時の対応

1. Resolution Centerでフィードバックを確認
2. 問題を修正
3. 新しいビルドをアップロード（必要な場合）
4. Resolution Centerで返信
5. 再審査を依頼

## 9. リリース管理

### 9.1 リリース方法の選択

- **手動リリース**: 審査通過後、手動でリリース
- **自動リリース**: 審査通過後、自動的にリリース
- **スケジュールリリース**: 指定日時にリリース

### 9.2 段階的リリース

1日目: 1%、2日目: 2%、3日目: 5%...と段階的にリリース

## 10. アップデート手順

### 10.1 バージョン番号の更新

app.json:
```json
{
  "expo": {
    "version": "1.1.0",  // インクリメント
    "ios": {
      "buildNumber": "2"  // 必ずインクリメント
    }
  }
}
```

### 10.2 新しいビルドとアップロード

```bash
eas build --platform ios --profile production
eas submit --platform ios --profile production
```

### 10.3 App Store Connectで更新

1. 新しいバージョンを作成
2. 更新内容を記載
3. 新しいビルドを選択
4. 審査へ提出

## トラブルシューティング

### 証明書の問題

```bash
# 証明書の確認
eas credentials

# 証明書のリセット
eas credentials --platform ios
```

### ビルドエラー

```bash
# ログの確認
eas build:view --platform ios

# キャッシュクリア
eas build --clear-cache --platform ios
```

### 提出エラー

- Apple IDの2ファクタ認証を確認
- App固有パスワードの生成と使用
- Team IDが正しいか確認

## 参考リンク

- [Expo EAS Documentation](https://docs.expo.dev/eas/)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)

## サポート

問題が発生した場合：
1. [Expo Forums](https://forums.expo.dev/)
2. [Stack Overflow](https://stackoverflow.com/questions/tagged/expo)
3. [Apple Developer Forums](https://developer.apple.com/forums/)