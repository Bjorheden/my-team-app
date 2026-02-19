# MyTeams Mobile

React Native app built with Expo (SDK 51) and TypeScript, using Expo Router for file-based navigation.

## Setup

```bash
cd mobile
cp .env.example .env
npm install
npx expo start
```

## Networking notes

| Target | `EXPO_PUBLIC_API_URL` |
|---|---|
| iOS Simulator (Mac) | `http://localhost:8000/v1` |
| Android Emulator | `http://10.0.2.2:8000/v1` |
| Physical device (same LAN) | `http://<machine-ip>:8000/v1` |
| Expo Go on device | use LAN IP |

## Screens

| Route | Description |
|---|---|
| `/(auth)/login` | Login / Magic-link entry, dev login button |
| `/(tabs)/` | Dashboard: followed teams, next/last match, standings |
| `/(tabs)/search` | Search teams, follow/unfollow |
| `/team/[id]` | Team fixtures list |
| `/fixture/[id]` | Fixture detail + event timeline |

## Dev login

In development mode (`APP_ENV=development`), tap **🛠 Dev Login** on the login screen to log in instantly without email. This calls `POST /v1/auth/dev-login` which must be enabled on the backend.

## Type check

```bash
npx tsc --noEmit
```

## Lint

```bash
npx expo lint
```

## Tests

```bash
npx jest
```
