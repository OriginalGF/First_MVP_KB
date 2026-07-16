"use client";

import { useEffect, useRef, useState } from "react";

export type AiMessage = {
  role: "assistant" | "user";
  content: string;
};

type AiAssistantPanelProps = {
  board: {
    columns: Array<{ id: string; title: string; cardIds: string[] }>;
    cards: Record<string, { id: string; title: string; details: string }>;
  };
  onBoardUpdated: (nextBoard: {
    columns: Array<{ id: string; title: string; cardIds: string[] }>;
    cards: Record<string, { id: string; title: string; details: string }>;
  }) => void;
};

export const AiAssistantPanel = ({ board, onBoardUpdated }: AiAssistantPanelProps) => {
  const [messages, setMessages] = useState<AiMessage[]>([
    {
      role: "assistant",
      content: "Ask me to rename a column, add a card, or move work around the board.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messageListRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft.trim() || isSending) {
      return;
    }

    const nextDraft = draft.trim();
    setDraft("");
    setMessages((prev) => [...prev, { role: "user", content: nextDraft }]);
    setIsSending(true);

    try {
      const response = await fetch("http://127.0.0.1:8011/api/ai/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: nextDraft, board }),
      });

      if (!response.ok) {
        throw new Error("AI request failed");
      }

      const payload = (await response.json()) as {
        message: string;
        board?: typeof board;
      };

      setMessages((prev) => [...prev, { role: "assistant", content: payload.message }]);
      if (payload.board) {
        onBoardUpdated(payload.board);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "The assistant could not respond right now." },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section className="rounded-[32px] border border-[var(--stroke)] bg-white/90 p-6 shadow-[var(--shadow)] backdrop-blur">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            AI assistant
          </p>
          <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Ask for board updates
          </h2>
        </div>
        <div className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--primary-blue)]">
          Live
        </div>
      </div>

      <div
        ref={messageListRef}
        className="mb-4 flex max-h-64 flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-4"
      >
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 ${
              message.role === "assistant"
                ? "bg-white text-[var(--navy-dark)]"
                : "ml-auto bg-[var(--primary-blue)] text-white"
            }`}
          >
            {message.content}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Try: rename the backlog column to Ready"
          className="min-h-[96px] rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none transition focus:border-[var(--primary-blue)]"
        />
        <p className="text-xs text-[var(--gray-text)]">
          Examples: rename a column, add a card, or move a card to review.
        </p>
        <button
          type="submit"
          disabled={isSending}
          className="rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isSending ? "Thinking..." : "Send to AI"}
        </button>
      </form>
    </section>
  );
};
