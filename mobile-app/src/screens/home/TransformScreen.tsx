import React, { useState } from 'react';
import { View, ScrollView, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import {
  Surface,
  TextInput,
  Button,
  SegmentedButtons,
  Card,
  Title,
  Paragraph,
  Chip,
  ActivityIndicator,
  Divider,
  useTheme,
} from 'react-native-paper';
import { useMutation } from '@tanstack/react-query';
import { transformAPI } from '../../services/api';
import Toast from 'react-native-toast-message';
import { SafeAreaView } from 'react-native-safe-area-context';

type TransformType = 'soften' | 'clarify' | 'structure' | 'summarize' | 'terminology';

interface TransformResult {
  transformed_text: string;
  metadata?: {
    tone_score?: number;
    clarity_score?: number;
    changes_made?: string[];
  };
}

const TransformScreen: React.FC = () => {
  const theme = useTheme();
  const [inputText, setInputText] = useState('');
  const [transformType, setTransformType] = useState<TransformType>('soften');
  const [toneLevel, setToneLevel] = useState(2);
  const [result, setResult] = useState<TransformResult | null>(null);

  const transformMutation = useMutation({
    mutationFn: (data: { text: string; type: TransformType; tone_level?: number }) =>
      transformAPI.transform({
        text: data.text,
        type: data.type,
        options: data.tone_level ? { tone_level: data.tone_level } : undefined,
      }),
    onSuccess: (data) => {
      setResult(data);
      Toast.show({
        type: 'success',
        text1: '変換完了',
        text2: 'テキストが変換されました',
      });
    },
    onError: (error: any) => {
      Toast.show({
        type: 'error',
        text1: '変換エラー',
        text2: error.response?.data?.message || '変換に失敗しました',
      });
    },
  });

  const handleTransform = () => {
    if (!inputText.trim()) {
      Toast.show({
        type: 'error',
        text1: 'エラー',
        text2: 'テキストを入力してください',
      });
      return;
    }

    transformMutation.mutate({
      text: inputText,
      type: transformType,
      tone_level: transformType === 'soften' ? toneLevel : undefined,
    });
  };

  const transformTypes = [
    { value: 'soften', label: '優しく', icon: 'heart' },
    { value: 'clarify', label: '明確に', icon: 'lightbulb' },
    { value: 'structure', label: '構造化', icon: 'format-list-bulleted' },
    { value: 'summarize', label: '要約', icon: 'text-short' },
    { value: 'terminology', label: '用語変換', icon: 'book' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Card style={styles.inputCard}>
            <Card.Content>
              <Title>テキスト変換</Title>
              
              <TextInput
                label="変換したいテキストを入力"
                value={inputText}
                onChangeText={setInputText}
                mode="outlined"
                multiline
                numberOfLines={4}
                style={styles.textInput}
                placeholder="例: この件について至急対応してください..."
              />

              <Title style={styles.sectionTitle}>変換タイプ</Title>
              <SegmentedButtons
                value={transformType}
                onValueChange={(value) => setTransformType(value as TransformType)}
                buttons={transformTypes.slice(0, 3)}
                style={styles.segmentedButtons}
              />
              <SegmentedButtons
                value={transformType}
                onValueChange={(value) => setTransformType(value as TransformType)}
                buttons={transformTypes.slice(3)}
                style={styles.segmentedButtons}
              />

              {transformType === 'soften' && (
                <>
                  <Title style={styles.sectionTitle}>変換強度</Title>
                  <View style={styles.toneContainer}>
                    {[0, 1, 2, 3].map((level) => (
                      <Chip
                        key={level}
                        selected={toneLevel === level}
                        onPress={() => setToneLevel(level)}
                        style={styles.chip}
                      >
                        {level === 0 && '軽め'}
                        {level === 1 && '普通'}
                        {level === 2 && 'しっかり'}
                        {level === 3 && '最大'}
                      </Chip>
                    ))}
                  </View>
                </>
              )}

              <Button
                mode="contained"
                onPress={handleTransform}
                loading={transformMutation.isPending}
                disabled={transformMutation.isPending || !inputText.trim()}
                style={styles.transformButton}
              >
                変換する
              </Button>
            </Card.Content>
          </Card>

          {result && (
            <Card style={styles.resultCard}>
              <Card.Content>
                <Title>変換結果</Title>
                <Divider style={styles.divider} />
                
                <Surface style={styles.resultSurface} elevation={0}>
                  <Paragraph style={styles.resultText}>
                    {result.transformed_text}
                  </Paragraph>
                </Surface>

                {result.metadata && (
                  <>
                    <Divider style={styles.divider} />
                    <View style={styles.metadataContainer}>
                      {result.metadata.tone_score && (
                        <Chip icon="emoticon-happy" style={styles.metadataChip}>
                          トーン: {result.metadata.tone_score}%
                        </Chip>
                      )}
                      {result.metadata.clarity_score && (
                        <Chip icon="eye" style={styles.metadataChip}>
                          明瞭度: {result.metadata.clarity_score}%
                        </Chip>
                      )}
                    </View>
                  </>
                )}

                <View style={styles.actionButtons}>
                  <Button
                    mode="outlined"
                    onPress={() => {
                      // Copy to clipboard
                      Toast.show({
                        type: 'success',
                        text1: 'コピーしました',
                      });
                    }}
                    icon="content-copy"
                  >
                    コピー
                  </Button>
                  <Button
                    mode="outlined"
                    onPress={() => {
                      // Share
                      Toast.show({
                        type: 'info',
                        text1: '共有機能は準備中です',
                      });
                    }}
                    icon="share"
                  >
                    共有
                  </Button>
                </View>
              </Card.Content>
            </Card>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  inputCard: {
    marginBottom: 16,
  },
  textInput: {
    marginTop: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    marginTop: 16,
    marginBottom: 8,
  },
  segmentedButtons: {
    marginBottom: 8,
  },
  toneContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  chip: {
    marginRight: 4,
  },
  transformButton: {
    marginTop: 16,
  },
  resultCard: {
    marginBottom: 16,
  },
  divider: {
    marginVertical: 12,
  },
  resultSurface: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.02)',
  },
  resultText: {
    fontSize: 15,
    lineHeight: 22,
  },
  metadataContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  metadataChip: {
    marginRight: 4,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
});

export default TransformScreen;