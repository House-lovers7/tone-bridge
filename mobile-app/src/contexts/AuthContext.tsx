import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../services/api';
import Toast from 'react-native-toast-message';

interface User {
  id: string;
  email: string;
  name: string;
  organization?: string;
  role: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

interface RegisterData {
  email: string;
  password: string;
  name: string;
  organization?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        const profile = await authAPI.getProfile();
        setUser(profile);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      await SecureStore.deleteItemAsync('access_token');
      await SecureStore.deleteItemAsync('refresh_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const { user } = await authAPI.login(email, password);
      setUser(user);
      
      Toast.show({
        type: 'success',
        text1: 'ログイン成功',
        text2: `おかえりなさい、${user.name}さん`,
      });
    } catch (error: any) {
      Toast.show({
        type: 'error',
        text1: 'ログインエラー',
        text2: error.response?.data?.message || 'ログインに失敗しました',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setIsLoading(true);
      const { user } = await authAPI.register(data);
      setUser(user);
      
      Toast.show({
        type: 'success',
        text1: '登録成功',
        text2: 'ToneBridgeへようこそ！',
      });
    } catch (error: any) {
      Toast.show({
        type: 'error',
        text1: '登録エラー',
        text2: error.response?.data?.message || '登録に失敗しました',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      await authAPI.logout();
      setUser(null);
      
      Toast.show({
        type: 'info',
        text1: 'ログアウト',
        text2: 'またのご利用をお待ちしています',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    try {
      setIsLoading(true);
      const updatedUser = await authAPI.updateProfile(data);
      setUser(updatedUser);
      
      Toast.show({
        type: 'success',
        text1: 'プロフィール更新',
        text2: '変更が保存されました',
      });
    } catch (error: any) {
      Toast.show({
        type: 'error',
        text1: '更新エラー',
        text2: error.response?.data?.message || '更新に失敗しました',
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};