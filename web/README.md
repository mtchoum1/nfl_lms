# nfl-lms-web

Minimal **Vite + TypeScript** frontend for the NFL Last Man Standing app. Firebase client SDK is initialized in [`src/firebase.ts`](src/firebase.ts) (Analytics enabled).

User sign-up and Realtime Database profiles are handled by the **Python API** (`POST /api/v1/users` on the backend); this app holds Firebase web config for future client-side auth and UI.

## Setup

From this directory:

```bash
npm install
cp .env.example .env
```

Fill in `.env` with values from the [Firebase console](https://console.firebase.google.com/) → Project settings → Your apps → Web app config:

| Variable | Firebase config field |
|----------|----------------------|
| `VITE_FIREBASE_API_KEY` | apiKey |
| `VITE_FIREBASE_AUTH_DOMAIN` | authDomain |
| `VITE_FIREBASE_PROJECT_ID` | projectId |
| `VITE_FIREBASE_STORAGE_BUCKET` | storageBucket |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | messagingSenderId |
| `VITE_FIREBASE_APP_ID` | appId |
| `VITE_FIREBASE_MEASUREMENT_ID` | measurementId (optional) |

Only variables prefixed with `VITE_` are exposed to the browser. Do **not** put server credentials (service account JSON, `GOOGLE_APPLICATION_CREDENTIALS`) in this file — those belong in the repo root [`.env`](../.env.example) for the API.

## Development

```bash
npm run dev
```

Default Vite dev server: [http://localhost:5173](http://localhost:5173)

Point the API at your local backend and allow CORS if needed (repo root `.env` or shell):

```bash
# example: API on 8000, frontend on 5173
export CORS_ORIGINS=http://localhost:5173
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Typecheck + production build to `dist/` |
| `npm run preview` | Serve the production build locally |

## Related

- Backend API and Firebase Admin setup: [../README.md](../README.md)
