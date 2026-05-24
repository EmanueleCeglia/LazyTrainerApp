import React, { createContext, useState, useEffect, useContext } from 'react';
import * as SecureStore from 'expo-secure-store';

interface AuthContextData {
  token: string | null;
  username: string | null;
  isLoading: boolean;
  login: (token: string, username: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored token on app load
    const loadToken = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync('userToken');
        const storedUsername = await SecureStore.getItemAsync('username');
        if (storedToken && storedUsername) {
          setToken(storedToken);
          setUsername(storedUsername);
        }
      } catch (e) {
        console.error("Failed to load token", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadToken();
  }, []);

  const login = async (newToken: string, newUsername: string) => {
    try {
      await SecureStore.setItemAsync('userToken', newToken);
      await SecureStore.setItemAsync('username', newUsername);
      setToken(newToken);
      setUsername(newUsername);
    } catch (e) {
      console.error("Failed to save token", e);
    }
  };

  const logout = async () => {
    try {
      await SecureStore.deleteItemAsync('userToken');
      await SecureStore.deleteItemAsync('username');
      setToken(null);
      setUsername(null);
    } catch (e) {
      console.error("Failed to delete token", e);
    }
  };

  return (
    <AuthContext.Provider value={{ token, username, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
