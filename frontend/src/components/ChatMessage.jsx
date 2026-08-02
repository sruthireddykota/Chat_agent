import { Bot, User as UserIcon, Clock, Wrench } from "lucide-react";
import ToolCallCard from "./ToolCallCard.jsx";
import PlanPrompt from "./PlanPrompt.jsx";
import ReasoningBlock from "./ReasoningBlock.jsx";

function TurnFooter({ usage, blocks }) {
  const tools = (blocks ?? []).filter((b) => b.type === "tool");
  const duration = tools.reduce((a, t) => a + (t.durationMs ?? 0), 0);
  const total = (usage?.input ?? 0) + (usage?.output ?? 0);
  if (!usage && !tools.length) return null;
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 pl-11 text-[11px] text-slate-400">
      {usage && (
        <span>
          {usage.input.toLocaleString()} in · {usage.output.toLocaleString()} out
          · {total.toLocaleString()} tokens
        </span>
      )}
      {tools.length > 0 && (
        <span className="inline-flex items-center gap-1">
          <Wrench size={11} /> {tools.length} tool{tools.length === 1 ? "" : "s"}
        </span>
      )}
      {duration > 0 && (
        <span className="inline-flex items-center gap-1">
          <Clock size={11} /> {duration} ms
        </span>
      )}
    </div>
  );
}

export default function ChatMessage({ message, onAnswer }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex flex-row-reverse gap-3">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-200 text-slate-600">
          <UserIcon size={16} />
        </div>
        <div className="max-w-[80%] rounded-2xl bg-brand-600 px-4 py-2.5 text-sm leading-relaxed text-white animate-fade-in-up">
          {message.image && (
            <img
              src={message.image}
              alt="attachment"
              className="mb-2 max-h-48 rounded-lg"
            />
          )}
          <div className="whitespace-pre-wrap">{message.content}</div>
          {message.attachments?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {message.attachments.map((name) => (
                <span key={name} className="rounded-md bg-white/15 px-2 py-1 text-xs">
                  📎 {name}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex gap-3">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-600 text-white">
          <Bot size={16} />
        </div>
        <div className="min-w-0 max-w-[85%] flex-1 animate-fade-in-up">
          {message.blocks ? (
            message.blocks.map((b, i) => {
              if (b.type === "reasoning")
                return <ReasoningBlock key={i} text={b.text} />;
              if (b.type === "tool") return <ToolCallCard key={i} block={b} />;
              if (b.type === "plan")
                return (
                  <PlanPrompt
                    key={i}
                    plan={b.plan}
                    resolved={b.resolved}
                    answer={b.answer}
                    onAnswer={onAnswer}
                  />
                );
              return (
                <div
                  key={i}
                  className="my-1 whitespace-pre-wrap rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm leading-relaxed text-slate-800"
                >
                  {b.text}
                </div>
              );
            })
          ) : (
            <div className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm leading-relaxed text-slate-800">
              {message.content}
            </div>
          )}
        </div>
      </div>
      <TurnFooter usage={message.usage} blocks={message.blocks} />
    </div>
  );
}
