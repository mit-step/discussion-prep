import { createContext, useContext, useState, type ReactNode } from "react";
import { api, clearStoredUserId, setStoredUserId } from "../api/client";

interface User {
  user_id: string;
  name: string;
  email: string;
}

interface UserContextValue {
  user: User | null;
  login: (name: string, email: string) => Promise<void>;
  logout: () => void;
}

const UserContext = createContext<UserContextValue | undefined>(undefined);

const USER_KEY = "discussion-prep:user";

function loadStoredUser(): User | null {
  const stored = localStorage.getItem(USER_KEY);
  if (!stored) return null;
  try {
    return JSON.parse(stored) as User;
  } catch {
    return null;
  }
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(loadStoredUser);

  async function login(name: string, email: string) {
    const result = await api.login(name, email);
    setStoredUserId(result.user_id);
    localStorage.setItem(USER_KEY, JSON.stringify(result));
    setUser(result);
  }

  function logout() {
    clearStoredUserId();
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }

  return <UserContext.Provider value={{ user, login, logout }}>{children}</UserContext.Provider>;
}

export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within a UserProvider");
  return ctx;
}
