module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      'react-native-reanimated/plugin',
      [
        'module-resolver',
        {
          root: ['./'],
          extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
          alias: {
            '@': './src',
            '@components': './src/components',
            '@screens': './src/screens',
            '@services': './src/services',
            '@hooks': './src/hooks',
            '@utils': './src/utils',
            '@types': './src/types',
            '@constants': './src/constants',
            '@navigation': './src/navigation',
            '@store': './src/store',
            '@contexts': './src/contexts',
            '@config': './src/config',
          },
        },
      ],
    ],
  };
};