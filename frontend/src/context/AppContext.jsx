import { createContext, useContext, useState } from "react";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = JSON.parse(window.localStorage.getItem("chat_agent_user") || "null");
      const savedToken = window.localStorage.getItem("chat_agent_access_token");
      // Do not restore pre-JWT sessions. They would render the app as logged
      // in while every API request is rejected by Kong with 401.
      if (!savedUser?.access_token || savedUser.access_token !== savedToken) {
        window.localStorage.removeItem("chat_agent_user");
        window.localStorage.removeItem("chat_agent_access_token");
        return null;
      }
      return savedUser;
    } catch {
      window.localStorage.removeItem("chat_agent_user");
      window.localStorage.removeItem("chat_agent_access_token");
      return null;
    }
  }); // { username, email, user_id, role, access_token }
  const [selectedAgent, setSelectedAgent] = useState("Generic");
  const [sessions, setSessions] = useState([]); // loaded from the API
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const login = (u) => {
    window.localStorage.setItem("chat_agent_user", JSON.stringify(u));
    window.localStorage.setItem("chat_agent_access_token", u.access_token);
    setUser(u);
  };
  const logout = () => {
    window.localStorage.removeItem("chat_agent_user");
    window.localStorage.removeItem("chat_agent_access_token");
    setUser(null);
  };

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
