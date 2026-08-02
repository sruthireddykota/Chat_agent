// (src/services/api.js) or the chat state hook (src/hooks/useAgentChat.js).

// Agent selector options. There is no backend endpoint for this list, so it
// stays as front-end config; `id` is sent as `agent_name` on a run.
export const AGENTS = [
  { id: "Generic", label: "Generic", desc: "General-purpose conversational assistant." },
  { id: "Coder", label: "Coder", desc: "Writes code and builds files in a live workspace." },
  { id: "Researcher", label: "Researcher", desc: "Searches and synthesizes information from sources." },
  { id: "RAG", label: "RAG", desc: "Answers grounded in your knowledge base." },
];

// Model context window used to draw the usage bar in the activity panel.
export const CONTEXT_WINDOW = 200000;
