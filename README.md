# Telebot — Telegram Channel Automation Bot

Telebot is a Python-based Telegram bot for managing channel publishing workflows: registering channels, creating reusable post drafts, publishing immediately, sending one post to multiple channels, and scheduling delivery.

- **Project type:** Telegram bot (terminal process)
- **Language:** Python
- **Framework/library:** `python-telegram-bot` (async polling mode)
- **Runs on:** Linux, macOS, Windows (any machine that can run Python)
- **Mode:** API-based (Telegram Bot API)
- **Entry file:** `main.py`

---

## 1) Project Overview

### What this bot does
Telebot helps Telegram channel admins automate recurring publishing tasks with a menu-driven interface.

### Key features
- Add and validate channels where the bot has posting permissions.
- Create draft posts (text + optional media).
- Publish saved posts to selected channels.
- Multipost one message to multiple channels.
- Schedule future posts (UTC-based) with background delivery.
- View and clear event logs.
- Per-user settings (timezone and notifications flag in DB).

### Typical use cases
- Content teams scheduling daily channel updates.
- Solo creators posting the same announcement across multiple channels.
- Admins maintaining a post draft library and publishing on demand.

---

## 2) Project Structure

```text
Telebot/
├── main.py                 # App bootstrap, handler registration, polling loop
├── config.py               # Runtime configuration constants and env reads
├── database.py             # SQLite schema and CRUD helpers
├── scheduler.py            # Background scheduler for delayed publishing
├── keyboards.py            # Inline/reply keyboard builders
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT license
├── README.md               # Project documentation
└── handlers/
    ├── start.py            # /start command + main menu callbacks
    ├── channel.py          # Add/register channel flow
    ├── posts.py            # Create/list/view/delete/publish posts
    ├── multipost.py        # Multi-channel publish conversation
    ├── schedule.py         # Schedule and delete scheduled posts
    ├── logs.py             # Event log view/clear handlers
    └── settings.py         # Settings and timezone selection handlers
```

---

## 3) Requirements

### Software prerequisites
- Python **3.10+** (3.11 recommended)
- `pip`
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Runtime dependencies
From `requirements.txt`:
- `python-telegram-bot==21.3`

### Platform support
- Linux
- macOS
- Windows

---

## 4) Installation Guide (Step-by-Step)

### Step 1 — Clone the repository
```bash
git clone <your-repo-url>.git
cd Telebot
```

### Step 2 — Create and activate a virtual environment

**Linux/macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Configure environment variables
The bot reads `BOT_TOKEN` from environment variables (`config.py`).

**Linux/macOS**
```bash
export BOT_TOKEN="123456789:your_bot_token_here"
```

**Windows (PowerShell)**
```powershell
$env:BOT_TOKEN="123456789:your_bot_token_here"
```

#### Optional `.env` template
If you prefer storing env vars in a file, create `.env` in the project root:

```env
BOT_TOKEN=123456789:your_bot_token_here
```

Then load it in your shell before starting:

**Linux/macOS**
```bash
set -a
source .env
set +a
```

**Windows (PowerShell)**
```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^(.*?)=(.*)$') {
    [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
  }
}
```

### Step 5 — Telegram channel permissions
Add your bot as an admin in each target channel and grant **Post Messages** permission.

---

## 5) Running the Bot

### Start command
```bash
python main.py
```

On startup, the app will:
1. Initialize SQLite schema (`telebot.db`) if missing.
2. Start Telegram polling.
3. Start the background scheduler loop (checks every 30 seconds).

### Operating mode
- **Primary mode:** Online API mode (Telegram Bot API).
- **Offline mode:** Not supported (the bot requires Telegram network access).

### Basic usage flow
1. Open the bot in Telegram and send `/start`.
2. Add at least one channel.
3. Create a post draft.
4. Publish immediately or schedule it.

---

## 6) Configuration Options

Configuration is currently in `config.py`:

- `BOT_TOKEN` (env): Telegram bot token.
- `DATABASE_PATH` (constant): SQLite DB file path (default `telebot.db`).
- `TIMEZONE` (constant): Default timezone label (default `UTC`).

### Environment variables
| Variable | Required | Purpose | Example |
|---|---|---|---|
| `BOT_TOKEN` | Yes | Authenticates your bot with Telegram API | `123456789:ABC...` |

### Settings stored per user in DB
- `timezone`
- `default_channel`
- `notifications` (`1`/`0`)

---

## 7) Troubleshooting

### Error: `InvalidToken` or bot does not start
**Cause:** `BOT_TOKEN` is missing or incorrect.  
**Fix:** Re-export a valid token from BotFather and restart the process.

### Bot cannot post to channel
**Cause:** Bot is not channel admin or lacks posting permission.  
**Fix:** Re-add bot as admin with **Post Messages** permission.

### Scheduled post not delivered
**Possible causes:**
- Scheduled time is not yet due (UTC comparison).
- Channel permissions changed.
- Bot removed from channel.

**Fixes:**
- Verify schedule time is in UTC.
- Check bot admin rights.
- Review Event Log from bot menu for failure details.

### Database locked / file issues
**Cause:** Concurrent access or restricted file permissions.  
**Fix:** Ensure one bot instance is writing to the same SQLite DB and verify write permission in project directory.

---

## 8) Deployment

### Local machine (recommended first)
Run with `python main.py` in an active virtual environment.

### VPS / server
- Install Python + project dependencies.
- Set `BOT_TOKEN` securely in environment.
- Use a process manager (`systemd`, `supervisor`, or Docker restart policy).
- Keep server timezone consistent; scheduling logic uses UTC strings.

### GitHub
GitHub cannot run long-lived polling bots directly. Use:
- GitHub for source control + CI checks.
- A VPS/container platform (Railway, Fly.io, Render, or your own server) for runtime.

---

## 9) Security Notes

- Never hardcode secrets in source files.
- Keep `BOT_TOKEN` in environment variables or `.env` (not committed).
- Add `.env` and local DB files to `.gitignore`.

Suggested `.gitignore` entries:

```gitignore
.venv/
__pycache__/
.env
telebot.db
*.db
```

- Rotate token immediately if leaked.
- Limit bot admin scope to only required channels.

---

## 10) Contribution Guide

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make changes with clear commit messages.
4. Run local validation before pushing.
5. Open a Pull Request describing:
   - What changed
   - Why it changed
   - How it was tested

---

## 11) License

This project is licensed under the **MIT License**. See [`LICENSE`](./LICENSE) for details.
