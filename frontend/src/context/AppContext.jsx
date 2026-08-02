import { createContext, useContext, useState } from "react";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null); // { username, email, user_id }
  const [selectedAgent, setSelectedAgent] = useState("Generic");
  const [sessions, setSessions] = useState([]); // loaded from the API
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const login = (u) => setUser(u); // u = { username, email, user_id }
  const logout = () => setUser(null);

  const value = {
    user,
    login,
    logout,
    selectedAgent,
    setSelectedAgent,
    sessions,
    setSessions,
    currentSessionId,
    setCurrentSessionId,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
