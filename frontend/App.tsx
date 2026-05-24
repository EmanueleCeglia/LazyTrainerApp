import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { Alert, StyleSheet, SafeAreaView, View, TouchableOpacity, Text, Platform, StatusBar as RNStatusBar, ActivityIndicator } from 'react-native';
import { QuestionnaireScreen } from './src/screens/QuestionnaireScreen';
import { WorkoutScreen } from './src/screens/WorkoutScreen';
import { AuthScreen } from './src/screens/AuthScreen';
import { generateWorkout } from './src/api/client';
import { ThemeProvider, useTheme } from './src/styles/ThemeContext';
import { AuthProvider, useAuth } from './src/context/AuthContext';

function MainApp() {
  const { colors, themeName, toggleTheme } = useTheme();
  const { token, username, isLoading: isAuthLoading, logout } = useAuth();
  
  const [planData, setPlanData] = useState<any>(null);
  const [planContext, setPlanContext] = useState<{planId: string, userId: string} | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerate = async (payload: any) => {
    setIsLoading(true);
    try {
      const response = await generateWorkout(payload);
      setPlanData(response.workout_plan);
      // We use the authenticated username
      setPlanContext({ planId: response.plan_id, userId: username || "user" });
    } catch (error: any) {
      Alert.alert("Generation Failed", error.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setPlanData(null);
    setPlanContext(null);
  };

  if (isAuthLoading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background, justifyContent: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  // If not logged in, show the Auth Screen
  if (!token) {
    return <AuthScreen />;
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar style={themeName === 'dark' ? "light" : "dark"} />
      
      {/* Top Bar with Theme and Logout */}
      <View style={styles.topBar}>
        <Text style={{ color: colors.textMuted, flex: 1 }}>Hi, {username}</Text>
        
        <TouchableOpacity style={[styles.themeButton, { borderColor: colors.primary, marginRight: 8 }]} onPress={toggleTheme}>
          <Text style={{ color: colors.primary, fontWeight: 'bold' }}>
            {themeName === 'dark' ? '🌸 Pink' : '🌙 Dark'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={[styles.themeButton, { borderColor: colors.textMuted }]} onPress={logout}>
          <Text style={{ color: colors.textMuted, fontWeight: 'bold' }}>Log Out</Text>
        </TouchableOpacity>
      </View>

      {planData && planContext ? (
        <WorkoutScreen 
          planData={planData} 
          planId={planContext.planId}
          userId={planContext.userId}
          onPlanUpdated={(newData) => setPlanData(newData)}
          onReset={handleReset} 
        />
      ) : (
        <QuestionnaireScreen onComplete={handleGenerate} isLoading={isLoading} />
      )}
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <MainApp />
      </ThemeProvider>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'android' ? (RNStatusBar.currentHeight || 24) + 10 : 10,
    paddingBottom: 10,
  },
  themeButton: {
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  }
});
