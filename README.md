# AKAZA CORE — JS HOSTING BOT

A futuristic, private single-admin Telegram control bot for managing your own JavaScript scripts.

## Visual / reply theme
- AKAZA CORE control-deck style with neon-inspired labels and structured Telegram HTML formatting.
- Persistent command keyboard for Upload, Files, Launch, Stop, Restart, Status and Logs.
- Telegram does not allow bots to change the user's app font. This package uses bold, italic, monospace code blocks, spacing and symbols to create the futuristic look inside messages.

## Deploy
1. Keep your source-code repository private.
2. Choose a host that supports a persistent Node.js background worker and persistent storage.
3. This package intentionally does not include a live `.env` file. Set `TELEGRAM_BOT_TOKEN` and `ADMIN_ID` in your hosting dashboard, or copy `.env.example` to `.env` for local testing.
4. Build command: `npm install`
5. For Docker deployment, select Docker runtime; the included `Dockerfile` builds and starts the bot automatically. For non-Docker Node.js deployment, use start command: `npm start`.
6. If your host uses dashboard variables, add these there instead (they override local `.env`):
   - `TELEGRAM_BOT_TOKEN` = a fresh token from BotFather
   - `ADMIN_ID` = your numeric Telegram user ID
7. Deploy, then send `/start` to your bot.

## Use
1. Send `/start`.
2. Tap **🚀 Upload Script** and send a `.js` document (maximum 1 MB).
3. Tap **▶️ Launch** when only one script is stored.
4. If multiple scripts exist, use `/run filename.js`.
5. Use **📡 System Status**, **📜 Live Logs**, **⏹ Stop** and **♻️ Restart** to manage it.

## Important security notes
- This is a private single-admin runner, not a secure multi-user hosting service or an OS sandbox.
- Uploaded JavaScript executes with the hosting account's operating-system permissions. Only upload code you wrote and trust. Never let strangers upload scripts.
- The bot token and hosting environment secrets are not passed to the child script, but the runner itself requires the Telegram token.
- Never publish your bot token or commit it to GitHub. If a token was exposed, revoke it through BotFather and create a new one.
- Your host must support background workers and persistent storage. Free plans may sleep, restart or stop; 24/7 uptime is not guaranteed.

## Requirements
- Node.js 18 or newer
- npm


**Token safety:** The token was shared in chat while preparing this package. For safety, revoke it with BotFather and generate a new token before deploying; then replace the value in `.env` or your host environment variables. Do not upload `.env` to a public repository.
