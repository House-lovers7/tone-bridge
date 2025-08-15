import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider as PaperProvider, MD3LightTheme, MD3DarkTheme, adaptNavigationTheme } from 'react-native-paper';
import Toast from 'react-native-toast-message';
import * as SplashScreen from 'expo-splash-screen';
import * as Font from 'expo-font';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { AuthProvider } from './src/contexts/AuthContext';
import { ThemeProvider, useTheme } from './src/contexts/ThemeContext';
import RootNavigator from './src/navigation/RootNavigator';
import { toastConfig } from './src/config/toast';

// Keep the splash screen visible while we fetch resources
SplashScreen.preventAutoHideAsync();

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const { isDarkMode } = useTheme();
  
  const theme = isDarkMode ? MD3DarkTheme : MD3LightTheme;
  const { LightTheme, DarkTheme } = adaptNavigationTheme({
    reactNavigationLight: MD3LightTheme,
    reactNavigationDark: MD3DarkTheme,
  });

  const navigationTheme = isDarkMode ? DarkTheme : LightTheme;

  return (
    <PaperProvider theme={theme}>
      <NavigationContainer theme={navigationTheme}>
        <StatusBar style={isDarkMode ? 'light' : 'dark'} />
        <RootNavigator />
        <Toast config={toastConfig} />
      </NavigationContainer>
    </PaperProvider>
  );
}

export default function App() {
  const [appIsReady, setAppIsReady] = useState(false);

  useEffect(() => {
    async function prepare() {
      try {
        // Pre-load fonts
        await Font.loadAsync({
          'Roboto-Regular': require('./assets/fonts/Roboto-Regular.ttf'),
          'Roboto-Medium': require('./assets/fonts/Roboto-Medium.ttf'),
          'Roboto-Bold': require('./assets/fonts/Roboto-Bold.ttf'),
        });

        // Artificially delay for two seconds to simulate a slow loading
        // experience. Remove this if you want to remove the delay.
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (e) {
        console.warn(e);
      } finally {
        // Tell the application to render
        setAppIsReady(true);
        await SplashScreen.hideAsync();
      }
    }

    prepare();
  }, []);

  if (!appIsReady) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <AuthProvider>
              <AppContent />
            </AuthProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}