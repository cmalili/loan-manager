# Frontend

Next.js frontend for the internal Loan Manager system.

## Structure

- `src/app/` contains App Router pages.
- `src/components/` contains shared UI and auth shell components.
- `src/lib/` contains API client, types, and formatting helpers.
- `src/styles/` contains global application styling.
- `public/` contains static assets.
- `tests/` is reserved for frontend tests.

## Local Setup

```bash
npm install
cp .env.local.example .env.local
```

Set `NEXT_PUBLIC_API_BASE_URL` to the backend API base URL. For local backend
defaults, use:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Run the app:

```bash
npm run dev
```

Verify the app:

```bash
npm run lint
npm run typecheck
npm run build
```
