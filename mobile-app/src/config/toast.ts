import React from 'react';
import { BaseToast, ErrorToast, InfoToast } from 'react-native-toast-message';
import { View, Text } from 'react-native';

export const toastConfig = {
  success: (props: any) => (
    <BaseToast
      {...props}
      style={{
        borderLeftColor: '#4CAF50',
        backgroundColor: '#ffffff',
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
      }}
      contentContainerStyle={{ paddingHorizontal: 15 }}
      text1Style={{
        fontSize: 15,
        fontWeight: '600',
        color: '#212121',
      }}
      text2Style={{
        fontSize: 13,
        color: '#757575',
      }}
    />
  ),
  
  error: (props: any) => (
    <ErrorToast
      {...props}
      style={{
        borderLeftColor: '#F44336',
        backgroundColor: '#ffffff',
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
      }}
      text1Style={{
        fontSize: 15,
        fontWeight: '600',
        color: '#212121',
      }}
      text2Style={{
        fontSize: 13,
        color: '#757575',
      }}
    />
  ),
  
  info: (props: any) => (
    <InfoToast
      {...props}
      style={{
        borderLeftColor: '#2196F3',
        backgroundColor: '#ffffff',
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
      }}
      text1Style={{
        fontSize: 15,
        fontWeight: '600',
        color: '#212121',
      }}
      text2Style={{
        fontSize: 13,
        color: '#757575',
      }}
    />
  ),
  
  custom: (props: any) => (
    <View style={{
      height: 60,
      width: '90%',
      backgroundColor: '#ffffff',
      borderRadius: 8,
      padding: 12,
      flexDirection: 'row',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
      elevation: 5,
    }}>
      <Text style={{ flex: 1, fontSize: 14, color: '#212121' }}>
        {props.text1}
      </Text>
    </View>
  ),
};