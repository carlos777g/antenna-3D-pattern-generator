# AGENTS.md

## Run Commands

- **Client**: `cd client && npm run dev` (Vite dev server on port 5173)
- **Server**: `cd server && node index.js` (Express on port 3000)
- **Both needed**: For full functionality, run both in separate terminals

## Architecture

- `client/` - React 19 + Vite + Three.js frontend; entrypoint `client/src/main.jsx`
- `server/` - Express backend; entrypoint `server/index.js`

## Project Notes

- Server uses pnpm (specified in `packageManager`), client uses npm
- No tests configured (server test script is a placeholder)
- Client uses Tailwind CSS v4 with `@tailwindcss/vite` plugin
- Path alias `@` resolves to `client/src/`

## Linting

- Client: `cd client && npm run lint` (ESLint 9)