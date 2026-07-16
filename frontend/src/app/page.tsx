"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const DEMO_USERNAME = "user";
const DEMO_PASSWORD = "password";
const DEMO_PASSWORD_STORAGE_KEY = "pm-demo-password";

type LoginFormState = {
  username: string;
  password: string;
};

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activePassword, setActivePassword] = useState(DEMO_PASSWORD);
  const [formState, setFormState] = useState<LoginFormState>({
    username: "",
    password: "",
  });
  const [changePasswordState, setChangePasswordState] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [changePasswordError, setChangePasswordError] = useState<string | null>(null);
  const [changePasswordSuccess, setChangePasswordSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const storedPassword = window.localStorage.getItem(DEMO_PASSWORD_STORAGE_KEY);
    if (storedPassword) {
      setActivePassword(storedPassword);
    }
  }, []);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (
      formState.username === DEMO_USERNAME &&
      formState.password === activePassword
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
        <div className="flex flex-wrap items-start justify-end gap-3 px-6 pt-6">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              setChangePasswordError(null);
              setChangePasswordSuccess(null);

              if (changePasswordState.currentPassword !== activePassword) {
                setChangePasswordError("Current password is incorrect");
                return;
              }

              if (changePasswordState.newPassword.length < 4) {
                setChangePasswordError("New password must be at least 4 characters");
                return;
              }

              if (changePasswordState.newPassword !== changePasswordState.confirmPassword) {
                setChangePasswordError("New password and confirmation do not match");
                return;
              }

              setActivePassword(changePasswordState.newPassword);
              if (typeof window !== "undefined") {
                window.localStorage.setItem(
                  DEMO_PASSWORD_STORAGE_KEY,
                  changePasswordState.newPassword
                );
              }
              setChangePasswordState({
                currentPassword: "",
                newPassword: "",
                confirmPassword: "",
              });
              setChangePasswordSuccess("Password updated");
            }}
            className="flex flex-wrap items-end gap-2 rounded-2xl border border-[var(--stroke)] bg-white px-3 py-3"
          >
            <label className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Current
              <input
                aria-label="Current password"
                type="password"
                value={changePasswordState.currentPassword}
                onChange={(event) =>
                  setChangePasswordState((prev) => ({
                    ...prev,
                    currentPassword: event.target.value,
                  }))
                }
                className="mt-1 w-28 rounded-lg border border-[var(--stroke)] px-2 py-1 text-sm"
              />
            </label>
            <label className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              New
              <input
                aria-label="New password"
                type="password"
                value={changePasswordState.newPassword}
                onChange={(event) =>
                  setChangePasswordState((prev) => ({
                    ...prev,
                    newPassword: event.target.value,
                  }))
                }
                className="mt-1 w-28 rounded-lg border border-[var(--stroke)] px-2 py-1 text-sm"
              />
            </label>
            <label className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Confirm
              <input
                aria-label="Confirm new password"
                type="password"
                value={changePasswordState.confirmPassword}
                onChange={(event) =>
                  setChangePasswordState((prev) => ({
                    ...prev,
                    confirmPassword: event.target.value,
                  }))
                }
                className="mt-1 w-28 rounded-lg border border-[var(--stroke)] px-2 py-1 text-sm"
              />
            </label>
            <button
              type="submit"
              className="rounded-full bg-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white"
            >
              Change password
            </button>
            {changePasswordError ? (
              <p className="w-full text-xs font-medium text-red-600">{changePasswordError}</p>
            ) : null}
            {changePasswordSuccess ? (
              <p className="w-full text-xs font-medium text-green-700">{changePasswordSuccess}</p>
            ) : null}
          </form>
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
