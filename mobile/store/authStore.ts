/**
 * Zustand auth store.
 */

import { create } from "zustand";
import { User, clearAuth, getAuthToken, getUser, saveAuthToken, saveUser } from "@/lib/auth";
import api from "@/lib/api";
import { AuthResponse } from "@/lib/types";

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  hydrate: () => Promise<void>;
  devLogin: (userId: string) => Promise<void>;
  requestLink: (email: string) => Promise<void>;
  verifyToken: (token: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isLoading: true,

  hydrate: async () => {
    const token = await getAuthToken();
    const user = await getUser();
    set({ token, user, isLoading: false });
  },

  devLogin: async (userId: string) => {
    const res = await api.post<AuthResponse>("/auth/dev-login", { user_id: userId });
    await saveAuthToken(res.data.access_token);
    await saveUser(res.data.user);
    set({ token: res.data.access_token, user: res.data.user });
  },

  requestLink: async (email: string) => {
    await api.post("/auth/request-link", { email });
  },

  verifyToken: async (token: string) => {
    const res = await api.post<AuthResponse>("/auth/verify", { token });
    await saveAuthToken(res.data.access_token);
    await saveUser(res.data.user);
    set({ token: res.data.access_token, user: res.data.user });
  },

  logout: async () => {
    await clearAuth();
    set({ token: null, user: null });
  },
}));
