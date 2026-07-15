# Frontend agent guide

This file describes the current frontend implementation so future work can stay aligned with the existing architecture and conventions.

## Purpose

The frontend is a Next.js app that renders a polished Kanban board demo. It is currently a client-side experience with local state and no backend persistence.

## Current structure

- app/ contains the Next.js app router entry points.
  - app/layout.tsx sets up the app shell and global fonts.
  - app/page.tsx renders the home page.
  - app/globals.css defines the shared theme variables and base styling.
- components/ contains the UI building blocks for the board.
  - KanbanBoard.tsx owns the board state and orchestrates drag-and-drop actions.
  - KanbanColumn.tsx renders each column and its cards.
  - KanbanCard.tsx renders an individual card with drag support.
  - KanbanCardPreview.tsx renders the card preview shown while dragging.
  - NewCardForm.tsx handles creating new cards.
- lib/ contains shared board state helpers.
  - kanban.ts declares the board data shape, default seed data, drag logic, and ID generation.
- src/test/ contains the test setup for Vitest and Testing Library.
  - KanbanBoard.test.tsx covers the current board interactions.
  - setup.ts defines the test environment.

## Key implementation notes

- The current app uses React 19 and Next.js 16.
- The board uses dnd-kit for drag-and-drop interactions.
- The design system is already defined with CSS variables in globals.css.
- The app is intentionally simple and should remain that way for the MVP.
- The board state is currently local-only and lives inside KanbanBoard.tsx.
- The current UI is visually rich but should stay lightweight and focused on the Kanban workflow.

## Coding conventions

- Keep changes small and focused.
- Prefer simple, readable React components over abstraction unless it clearly improves maintainability.
- Preserve the current visual language and color system from globals.css.
- Do not add extra features that are not part of the MVP plan.
- Follow the existing naming style with PascalCase for components and camelCase for utilities.
- Keep the app simple and avoid unnecessary defensive programming.

## Testing expectations

- Write or update tests when changing behavior.
- Prefer testing real user flows through the UI rather than implementation details.
- Keep unit and integration tests lightweight and easy to read.
- For board behavior, test interactions such as renaming columns, adding cards, deleting cards, and drag-and-drop movement where feasible.
- For future authentication and backend integration work, add tests around login flow, loading states, and successful persistence.
- When implementing AI features, test both the happy path and malformed or incomplete responses.

## Implementation guidance for future milestones

- When introducing authentication, keep the experience minimal and hardcoded for the MVP.
- When wiring to the backend, keep the frontend API layer simple and do not over-engineer state management.
- When adding AI chat, preserve the existing board experience and make the sidebar feel like part of the same product.
- Always verify the frontend build and test suite after meaningful changes.
- Keep the board data shape consistent between the frontend and backend when persistence is introduced.

## Working style

- Favor incremental changes over large rewrites.
- Preserve existing behavior unless the current milestone explicitly changes it.
- When a change affects the board data model, keep the shape consistent between the frontend and backend.
- Keep the implementation aligned with the current project plan and avoid scope creep.
