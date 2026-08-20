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
    const assistantId = `stream-${Date.now()}-${Math.random()}`;

    try {
      const payload = {
        query: { text: query, files },
        session_id,
        user_id,
        agent_name,
      };
      let receivedText = false;
      await api.streamAgent(payload, (event) => {
        if (event.type === "chunk" && event.message) {
          receivedText = true;
          setMessages((previous) => {
            const existing = previous.find((item) => item.id === assistantId);
            if (!existing) {
              return [
                ...previous,
                {
                  id: assistantId,
                  role: "assistant",
                  streaming: true,
                  blocks: [{ type: "text", text: event.message }],
                },
              ];
            }

            const blocks = existing.blocks || [{ type: "text", text: "" }];
            const textBlock = blocks.find((block) => block.type === "text") || blocks[0];
            return previous.map((item) => item.id !== assistantId ? item : {
              ...item,
              blocks: blocks.map((block) =>
                block === textBlock ? { ...block, text: `${block.text || ""}${event.message}` } : block
              ),
            });
          });
        }

        if (event.type === "completed") {
          setMessages((previous) => previous.map((item) =>
            item.id === assistantId ? { ...item, streaming: false } : item
          ));
        }
      });

      if (!receivedText) {
        setMessages((previous) => [
          ...previous,
          { role: "assistant", blocks: [{ type: "text", text: "The agent returned no response." }] },
        ]);
      }
    } catch (error) {
      const message = error?.message || "The agent request failed.";
      setMessages((previous) => {
        const hasAssistant = previous.some((item) => item.id === assistantId);
        if (!hasAssistant) {
          return [...previous, { role: "assistant", blocks: [{ type: "text", text: `⚠️ ${message}` }] }];
        }
        return previous.map((item) =>
          item.id === assistantId
            ? { ...item, streaming: false, blocks: [{ type: "text", text: `⚠️ ${message}` }] }
            : item
        );
      });
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
