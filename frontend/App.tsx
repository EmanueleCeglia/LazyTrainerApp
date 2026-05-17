import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { Alert, StyleSheet, SafeAreaView, View, TouchableOpacity, Text, Platform, StatusBar as RNStatusBar } from 'react-native';
import { QuestionnaireScreen } from './src/screens/QuestionnaireScreen';
import { WorkoutScreen } from './src/screens/WorkoutScreen';
import { generateWorkout } from './src/api/client';
import { ThemeProvider, useTheme } from './src/styles/ThemeContext';

function MainApp() {
  const { colors, themeName, toggleTheme } = useTheme();
  const [planData, setPlanData] = useState<any>(null);
  const [planContext, setPlanContext] = useState<{planId: string, userId: string} | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerate = async (payload: any) => {
    setIsLoading(true);
    try {
      const response = await generateWorkout(payload);
      setPlanData(response.workout_plan);
      setPlanContext({ planId: response.plan_id, userId: payload.user_id });
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

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar style={themeName === 'dark' ? "light" : "dark"} />
      
      {/* Theme Toggle Button positioned at top right */}
      <View style={styles.topBar}>
        <TouchableOpacity style={[styles.themeButton, { borderColor: colors.primary }]} onPress={toggleTheme}>
          <Text style={{ color: colors.primary, fontWeight: 'bold' }}>
            {themeName === 'dark' ? '🌸 Pink Mode' : '🌙 Dark Mode'}
          </Text>
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
    <ThemeProvider>
      <MainApp />
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topBar: {
    alignItems: 'flex-end',
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
