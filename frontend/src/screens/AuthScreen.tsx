import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, KeyboardAvoidingView, Platform, Alert, TouchableOpacity } from 'react-native';
import { useTheme } from '../styles/ThemeContext';
import { Button } from '../components/Button';
import { loginUser, registerUser } from '../api/client';
import { useAuth } from '../context/AuthContext';

export function AuthScreen() {
  const { colors } = useTheme();
  const { login } = useAuth();
  
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (!username || !password) {
      Alert.alert("Missing Fields", "Please enter both username and password.");
      return;
    }

    setIsLoading(true);
    try {
      if (isLogin) {
        const data = await loginUser(username, password);
        await login(data.access_token, data.username);
      } else {
        const data = await registerUser({ username, password });
        await login(data.access_token, data.username);
      }
    } catch (error: any) {
      Alert.alert("Authentication Failed", error.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.formContainer}>
        <Text style={[styles.header, { color: colors.text }]}>
          {isLogin ? "Welcome Back" : "Create Account"}
        </Text>
        <Text style={[styles.subHeader, { color: colors.textMuted }]}>
          {isLogin ? "Log in to view your plans." : "Start your journey today."}
        </Text>

        <TextInput 
          style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} 
          value={username} 
          onChangeText={setUsername} 
          placeholder="Username" 
          placeholderTextColor={colors.textMuted}
          autoCapitalize="none"
        />

        <TextInput 
          style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} 
          value={password} 
          onChangeText={setPassword} 
          placeholder="Password" 
          secureTextEntry
          placeholderTextColor={colors.textMuted}
        />

        <Button 
          title={isLogin ? "Log In" : "Sign Up"} 
          onPress={handleSubmit} 
          loading={isLoading} 
        />

        <TouchableOpacity onPress={() => setIsLogin(!isLogin)} style={styles.toggleBtn}>
          <Text style={[styles.toggleText, { color: colors.primary }]}>
            {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Log In"}
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
  },
  formContainer: {
    padding: 24,
  },
  header: {
    fontSize: 32,
    fontWeight: '900',
    marginBottom: 8,
  },
  subHeader: {
    fontSize: 16,
    marginBottom: 32,
  },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    marginBottom: 16,
  },
  toggleBtn: {
    marginTop: 24,
    alignItems: 'center',
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '600',
  }
});
