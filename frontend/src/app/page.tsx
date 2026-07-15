"use client";

import { useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const DEMO_USERNAME = "user";
const DEMO_PASSWORD = "password";

type LoginFormState = {
  username: string;
  password: string;
};

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [formState, setFormState] = useState<LoginFormState>({
    username: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (
      formState.username === DEMO_USERNAME &&
      formState.password === DEMO_PASSWORD
    ) {
      setError(null);
      setIsAuthenticated(true);
      return;
    }

    setError("Invalid username or password");
  };

  if (isAuthenticated) {
    return (
      <div>
        <div className="flex justify-end px-6 pt-6">
          <button
            type="button"
            onClick={() => {
              setIsAuthenticated(false);
              setFormState({ username: "", password: "" });
              setError(null);
            }}
            className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-sm font-semibold uppercase tracking-wide text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)]"
          >
            Sign out
          </button>
        </div>
        <KanbanBoard />
      </div>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6 py-12">
      <div className="w-full max-w-md rounded-[32px] border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)] backdrop-blur">
        <h2 className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          Sign in
        </h2>
        <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
          Welcome back
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
          Use the demo credentials to access the kanban workspace.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <label className="block text-sm font-medium text-[var(--navy-dark)]">
            <span className="mb-2 block">Username</span>
            <input
              aria-label="Username"
              value={formState.username}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, username: event.target.value }))
              }
              className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 outline-none transition focus:border-[var(--primary-blue)]"
            />
          </label>

          <label className="block text-sm font-medium text-[var(--navy-dark)]">
            <span className="mb-2 block">Password</span>
            <input
              aria-label="Password"
              type="password"
              value={formState.password}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, password: event.target.value }))
              }
              className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 outline-none transition focus:border-[var(--primary-blue)]"
            />
          </label>

          {error ? (
            <p className="text-sm font-medium text-red-600">{error}</p>
          ) : null}

          <button
            type="submit"
            className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
          >
            Sign in
          </button>
        </form>
      </div>
    </main>
  );
}
