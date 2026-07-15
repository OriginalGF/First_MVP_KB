import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "./page";

describe("Home page", () => {
  it("shows a login form before the board is available", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /kanban studio/i })).not.toBeInTheDocument();
  });

  it("allows a user to sign in with the demo credentials", async () => {
    const user = userEvent.setup();
    render(<Home />);

    await user.type(screen.getByLabelText(/username/i), "user");
    await user.type(screen.getByLabelText(/password/i), "password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("shows an error for invalid credentials", async () => {
    const user = userEvent.setup();
    render(<Home />);

    await user.type(screen.getByLabelText(/username/i), "wrong");
    await user.type(screen.getByLabelText(/password/i), "value");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
  });

  it("allows a user to sign out again", async () => {
    const user = userEvent.setup();
    render(<Home />);

    await user.type(screen.getByLabelText(/username/i), "user");
    await user.type(screen.getByLabelText(/password/i), "password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await user.click(screen.getByRole("button", { name: /sign out/i }));

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /kanban studio/i })).not.toBeInTheDocument();
  });
});
