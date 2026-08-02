import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api.js";

/** Per-session chat state backed by the REST agent endpoint. */
export function useAgentChat(sessionId, { historyLoader } = {}) {
  const [running, setRunning] = useState(false);
  const [messages, setMessages] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [usage, setUsage] = useState({ input: 0, output: 0 });
  const [prompt, setPrompt] = useState(null);

  useEffect(() => {
    if (!sessionId) return undefined;
    let closed = false;

    setMessages([]);
    setTasks([]);
    setUsage({ input: 0, output: 0 });
    setPrompt(null);

    if (historyLoader) {
      Promise.resolve(historyLoader(sessionId))
        .then((seed) => {
          if (!closed && Array.isArray(seed) && seed.length) setMessages(seed);
        })
        .catch(() => {});
    }

    return () => {
      closed = true;
    };
  }, [sessionId, historyLoader]);

  const startRun = useCallback(async ({
    query,
    session_id,
    user_id,
    agent_name,
    files = [],
  }) => {
    setMessages((previous) => [
      ...previous,
      { role: "user", content: query, attachments: files.map((file) => file.name).filter(Boolean) },
    ]);
    setRunning(true);

    try {
      const result = await api.runAgent({
        query: { text: query, files },
        session_id,
        user_id,
        agent_name,
      });
      const response = typeof result === "string" ? result : result?.response || "";
      setMessages((previous) => [
        ...previous,
        { role: "assistant", blocks: [{ type: "text", text: response || "The agent returned no response." }] },
      ]);
    } catch (error) {
      const message = error?.message || "The agent request failed.";
      setMessages((previous) => [
        ...previous,
        { role: "assistant", blocks: [{ type: "text", text: `⚠️ ${message}` }] },
      ]);
    } finally {
      setRunning(false);
    }
  }, []);

  const respond = useCallback((_requestId, _value) => {
    setPrompt(null);
  }, []);

  const cancel = useCallback(() => {}, []);

  const clear = useCallback(() => {
    setMessages([]);
    setTasks([]);
    setUsage({ input: 0, output: 0 });
    setPrompt(null);
  }, []);

  return { running, messages, tasks, usage, prompt, startRun, respond, cancel, clear };
}

export default useAgentChat;
