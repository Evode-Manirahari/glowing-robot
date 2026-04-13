import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { login as apiLogin, register as apiRegister, getMe } from "./api";

interface AuthUser {
  id: string;
  email: string;
  name: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setLoading(false); return; }
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await apiLogin(email, password);
    localStorage.setItem("token", res.access_token);
    setUser({ id: res.user_id, email: res.email, name: res.name });
  }

  async function register(email: string, name: string, password: string) {
    const res = await apiRegister(email, name, password);
    localStorage.setItem("token", res.access_token);
    setUser({ id: res.user_id, email: res.email, name: res.name });
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
