# 🤖 Delulu — Telegram Channel Automation Bot

A clean, modular bot for managing, creating, and scheduling posts across multiple Telegram channels.

---

## Features

| Button | What it does |
|--------|-------------|
| ➕ Add Channel | Validates & registers a channel where the bot is admin |
| 📝 Create Post | Title → content → optional media → save draft or publish instantly |
| 📂 My Posts | Browse drafts, publish to any channel, or delete |
| 📤 Multipost | Send one post to multiple channels in one go |
| ⏰ Schedule Post | Pick a post, a channel, and a UTC datetime — fires automatically |
| 🗑 Delete Scheduled | Remove any pending scheduled post before it fires |
| 📊 Event Log | Timestamped log of all bot actions (last 30), clearable |
| ⚙ Settings | Change timezone, toggle delivery notifications |
| ❌ Exit | Closes the menu |

---

## Setup

### 1. Clone / copy the project

```
delulu-bot/
├── main.py
├── database.py
├── scheduler.py
├── keyboards.py
├── config.py
├── requirements.txt
└── handlers/
    ├── __init__.py
    ├── start.py
    ├── channel.py
    ├── posts.py
    ├── multipost.py
    ├── schedule.py
    ├── logs.py
    └── settings.py
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your bot token

**Option A — environment variable (recommended):**
```bash
export BOT_TOKEN="your_token_here"
python main.py
```

**Option B — edit `config.py` directly:**
```python
BOT_TOKEN = "your_token_here"
```

### 4. Make the bot an admin in your channels

Before adding a channel via the bot, go to your Telegram channel → Administrators → Add Administrator → find your bot → give it **Post Messages** permission.

### 5. Run

```bash
python main.py
```

---

## Scheduling

- All scheduled times are stored and compared in **UTC**.
- The scheduler polls every **30 seconds**.
- You'll receive a Telegram notification when a post is sent or fails.

---

## Database

SQLite (`delulu.db`) is created automatically on first run. Tables:

- `channels` — registered channels per user  
- `posts` — draft/published post content  
- `scheduled_posts` — pending / sent / failed scheduled deliveries  
- `event_log` — audit trail  
- `settings` — per-user preferences  

---

## Deployment tips

- Use **systemd**, **supervisor**, or **Docker** to keep the bot running in the background.
- For production, consider switching the SQLite database to PostgreSQL.
- Keep your `BOT_TOKEN` in an `.env` file and use `python-dotenv` to load it.
