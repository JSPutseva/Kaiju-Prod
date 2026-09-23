import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const CurrentUserContext = createContext(null);

export function CurrentUserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("kaiju_token");

    if (!token) {
      setLoading(false);
      return;
    }

    api
      .getCurrentUser()
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        localStorage.removeItem("kaiju_token");
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = (token, currentUser) => {
    localStorage.setItem("kaiju_token", token);
    setUser(currentUser);
  };

  const logout = () => {
    localStorage.removeItem("kaiju_token");
    setUser(null);
  };

  const value = {
    user,
    name: user?.name ?? "",
    roleCode: user?.role ?? null,
    quarterId: user?.quarter_id ?? null,

    setRoleCode: (roleCode) => {
      setUser((current) => (current ? { ...current, role: roleCode } : current));
    },

    login,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  return (
    <CurrentUserContext.Provider value={value}>
      {children}
    </CurrentUserContext.Provider>
  );
}

export function useCurrentUser() {
  const ctx = useContext(CurrentUserContext);
  if (!ctx) {
    throw new Error("useCurrentUser must be used within a CurrentUserProvider");
  }
  return ctx;
}
