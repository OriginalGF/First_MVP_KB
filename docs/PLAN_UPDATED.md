# Project plan

This plan breaks the MVP into milestone-based implementation steps. Each milestone includes a concrete checklist, test expectations, and a definition of done so the work can move forward in a controlled way.

## Part 1: Planning, documentation, and frontend guidance

Goal: Lock in the implementation approach before building anything else.

Checklist:
- [ ] Review the existing frontend code in frontend/, including the current Kanban demo, styling, and tests.
- [ ] Review the repository structure for backend/, scripts/, and docs/.
- [ ] Expand this plan into detailed milestone tasks with implementation notes.
- [ ] Create frontend/AGENTS.md with architecture guidance, coding conventions, test expectations, and workflow notes.
- [ ] Present the plan to the user and wait for approval before starting implementation.

Test expectations:
- No runtime tests are required for this milestone.
- The deliverables should be reviewable in docs/PLAN.md and frontend/AGENTS.md.

Acceptance checklist:
- [ ] The plan clearly lists all major milestones from scaffolding through AI chat.
- [ ] The frontend guidance file explains the current structure, conventions, and testing approach.
- [ ] The user has reviewed the plan and approved moving forward.

## Part 2: Lightweight scaffolding

Goal: Establish a local, lightweight development environment with Docker, a FastAPI backend, and scripts to run the app.

Checklist:
- [ ] Create a lightweight Docker setup for local development.
- [ ] Add a FastAPI app in backend/ with a simple health endpoint.
- [ ] Add start and stop scripts for the supported platforms in scripts/.
- [ ] Confirm the app serves a basic hello world page and a simple API response locally.
- [ ] Keep the setup intentionally simple and local-first.

Test expectations:
- [ ] Start the container or local process successfully.
- [ ] GET / returns a basic success response.
- [ ] GET /api/health or equivalent returns a successful JSON response.

Acceptance checklist:
- [ ] The app can be started locally with the provided scripts.
- [ ] The backend responds successfully from a browser or curl.
- [ ] The setup is lightweight and does not introduce unnecessary complexity.

## Part 3: Frontend integration and static serving

Goal: Make the existing Kanban demo available through the app shell and serve it from the combined stack.

Checklist:
- [ ] Ensure the Next.js frontend can be built and served by the app.
- [ ] Wire the app so the home route shows the existing Kanban board at /.
- [ ] Preserve the current visual design and core Kanban interactions.
- [ ] Add unit tests for the core board behaviors and component rendering.
- [ ] Add integration coverage for the page rendering the board.

Test expectations:
- [ ] Unit tests cover column rendering, card creation, card deletion, and column rename behavior.
- [ ] Integration tests confirm the page loads the Kanban board successfully.
- [ ] Build completes without frontend errors.

Acceptance checklist:
- [ ] The home page shows the Kanban board.
- [ ] Existing drag-and-drop and card creation flows still work.
- [ ] The frontend builds successfully.

## Part 4: Dummy authentication experience

Goal: Add a simple sign-in experience with hardcoded credentials before exposing the board.

Checklist:
- [ ] Add a simple login screen at / that requires the dummy credentials user / password.
- [ ] Show the Kanban board only after authentication succeeds.
- [ ] Add a logout action that returns the user to the login view.
- [ ] Keep the flow minimal and focused on the MVP experience.

Test expectations:
- [ ] Unit tests cover successful login, failed login, and logout behavior.
- [ ] Integration tests confirm the board is hidden before login and shown after login.

Acceptance checklist:
- [ ] A user cannot see the board without authentication.
- [ ] A valid login reveals the Kanban board.
- [ ] Logout returns the user to the login experience.

## Part 5: Database modeling and schema proposal

Goal: Define a practical schema for the MVP before implementing persistence.

Checklist:
- [ ] Propose a simple SQLite-friendly schema for users, boards, columns, and cards.
- [ ] Save the proposed schema as JSON in docs/.
- [ ] Document the intended data model and explain how it will support future multi-user expansion.
- [ ] Present the schema for review before implementing persistence.

Test expectations:
- [ ] The schema proposal is stored in a versioned docs file.
- [ ] The structure is consistent with the current frontend board model.

Acceptance checklist:
- [ ] The schema covers the Kanban data needed for the MVP.
- [ ] The approach is documented clearly for review.
- [ ] The user has approved the schema direction before persistence work starts.

## Part 6: Backend API for Kanban persistence

Goal: Add backend routes that read and update board data for a logged-in user.

Checklist:
- [ ] Create database initialization logic so SQLite is created automatically if missing.
- [ ] Add API routes to read board data for a given user.
- [ ] Add API routes to create, update, and delete cards and update column state.
- [ ] Keep the API slim and focused on the MVP board use case.
- [ ] Add backend unit tests around persistence and error handling.

Test expectations:
- [ ] Backend tests cover creating the database, reading a board, updating columns, and saving card changes.
- [ ] Tests verify that the API returns appropriate success and error responses.

Acceptance checklist:
- [ ] The backend can persist board state for a user.
- [ ] The database is created automatically when needed.
- [ ] Core board operations work through the API.

## Part 7: Frontend connected to the backend

Goal: Replace the local-only board state with real persisted data from the backend.

Checklist:
- [ ] Update the frontend to load board data from the backend after login.
- [ ] Send board changes back to the backend after card moves, edits, and additions.
- [ ] Handle loading and save states in a simple way.
- [ ] Preserve the current UI experience while using backend-backed data.
- [ ] Add thorough frontend tests covering the new data flow.

Test expectations:
- [ ] Frontend tests cover initial loading, successful save, and basic failure handling.
- [ ] Integration tests confirm the board reflects backend data and updates after user actions.

Acceptance checklist:
- [ ] The board loads its current state from the backend.
- [ ] User actions update the persisted board.
- [ ] The UI remains responsive and usable.

## Part 8: AI connectivity

Goal: Connect the backend to OpenRouter and verify that AI calls succeed.

Checklist:
- [ ] Configure the backend to use the OpenRouter API key from the environment.
- [ ] Add a simple backend endpoint or internal call for a basic AI test prompt.
- [ ] Verify the backend can successfully call the configured model.
- [ ] Keep the initial integration minimal and test-driven.

Test expectations:
- [ ] A simple prompt such as 2 + 2 returns a valid AI response.
- [ ] Failure cases are surfaced clearly in logs and responses.

Acceptance checklist:
- [ ] The backend can call the AI provider successfully.
- [ ] The integration works with the declared model and environment configuration.

## Part 9: Structured AI board actions

Goal: Send board context and user intent to the model and let it return both a reply and optional board updates.

Checklist:
- [ ] Send the current board JSON plus the user's question and conversation context to the AI.
- [ ] Require the AI response to use a structured output format with a message and optional board updates.
- [ ] Apply safe, explicit board updates only when the response includes valid changes.
- [ ] Add backend tests covering structured responses and invalid payload handling.
- [ ] Add frontend tests for the AI-driven update flow where relevant.

Test expectations:
- [ ] Backend tests verify a valid structured response updates the board correctly.
- [ ] Tests verify invalid or incomplete AI output does not corrupt board state.

Acceptance checklist:
- [ ] The AI can respond to the user with helpful text.
- [ ] The AI can optionally propose board changes in a controlled and validated format.
- [ ] The system rejects malformed updates safely.

## Part 10: AI chat sidebar and live refresh

Goal: Add a polished AI chat experience that can update the board and reflect those changes immediately.

Checklist:
- [ ] Add a sidebar chat experience in the UI with a clear message history area and input.
- [ ] Send the current board state and conversation history to the backend when the user submits a prompt.
- [ ] Show the AI response in the chat UI.
- [ ] If the AI returns valid board updates, apply them to the board and refresh the UI automatically.
- [ ] Keep the experience visually consistent with the existing board styling.

Test expectations:
- [ ] Frontend tests cover rendering the chat sidebar, sending a message, and showing the AI response.
- [ ] Integration tests confirm that a valid AI board update is reflected in the board UI.

Acceptance checklist:
- [ ] The user can chat with the AI from the app.
- [ ] The AI can respond conversationally and optionally update the board.
- [ ] Board refreshes happen automatically when valid updates are received.
