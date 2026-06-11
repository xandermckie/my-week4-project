# Ratio — LSAT Tutor

Ratio is a web-based LSAT preparation tool powered by Claude (Anthropic's AI). It gives students a private tutoring experience that adapts to their weak areas: an AI tutor explains reasoning concepts on demand, a 100-question practice bank tracks which question types trip them up, and a personalized week-by-week study plan is generated from that data. Gamification features — daily streaks, XP, league rankings (Bronze through Diamond), daily missions, global leaderboards, and 24-hour friend challenges — keep students accountable between sessions. A free tier gives generous daily limits; upgrading to Pro removes all caps and unlocks the full social feature set. All user data is encrypted at rest with Fernet symmetric encryption; API keys are never exposed to the browser.

---

## Prerequisites

| Requirement | Version / notes |
|---|---|
| Python | **3.11 or later** |
| pip | Comes bundled with Python |
| An Anthropic API key | See below |

### Getting an Anthropic API key

1. Sign up at [console.anthropic.com](https://console.anthropic.com).
2. Add a payment method under **Billing**.
3. Go to **API Keys** → **Create Key**.
4. Copy the key — you see it only once. It starts with `sk-ant-`.

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/xandermckie/my-week4-project.git
cd my-week4-project

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
```

Open `.env` and fill in the three required values:

```dotenv
# Generate with:
#   python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-random-32-character-hex-string

# From console.anthropic.com → API Keys
ANTHROPIC_API_KEY=sk-ant-...

# Generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=your-base64-fernet-key
```

### Optional — email notifications

To enable welcome emails, streak warnings, weekly digests, and study plan delivery, add these to `.env`:

```dotenv
MAIL_ENABLED=true
MAIL_USERNAME=your-gmail-address@gmail.com
MAIL_PASSWORD=your-gmail-app-password   # not your login password — use an App Password
APP_URL=http://127.0.0.1:5000           # used in email links
```

> **Gmail App Passwords:** Go to your Google Account → Security → 2-Step Verification → App Passwords. Generate one for "Mail / Windows Computer". Use that 16-character code as `MAIL_PASSWORD`.

---

## How to run

```bash
python run.py
```

The development server starts at **http://127.0.0.1:5000** in debug mode with live reloading.

---

## What it does when it runs

### Input you give

| Where | What to type |
|---|---|
| `/register` | Email address and password (min 8 characters). Agree to terms. |
| `/chat` | Any LSAT question, argument, or concept — plain English. e.g. *"Explain the difference between a necessary assumption and a sufficient assumption"* |
| `/quiz` | Click a radio button A–D, submit, read the explanation. |
| `/study-plan` | Enter your target exam date (e.g. `2026-09-13`). |
| `/upgrade` | A mock 16-digit card number, MM/YY expiry, and CVV — no real charge. |

### Output you get

| Feature | Output |
|---|---|
| **Tutor Chat** | Claude responds as a dedicated LSAT coach, explaining the reasoning behind any concept, dissecting arguments, and giving practice tips. Free users get 25 messages/day; Pro gets 200. |
| **Quiz** | One question at a time from the 100-question bank covering Weaken, Strengthen, Assumption, Flaw, Inference, Main Point, Parallel Reasoning, Principle, Resolve, and Reading Comprehension. After submitting, the correct answer is highlighted, your wrong choice is marked in red, and a paragraph explains the reasoning. Each answer earns XP (+15 correct, +3 wrong). |
| **Analysis dashboard** | A ranked list of your weak question types by error count, plus today's three daily missions with live progress bars and XP rewards. |
| **Study Plan** | A week-by-week Markdown plan tailored to your weak areas and exam date, optionally emailed to you. |
| **Leaderboard** | Global top 20 by XP and a friends-only ranking, with your league badge (Bronze → Diamond) and current level. |
| **Friends & Challenges** | Add study partners by email, send 24-hour XP Race / Question Blitz / Accuracy Duel challenges, and track live delta scores. |
| **Profile** | XP progress bar, streak count, best streak, total questions answered, league badge, and upgrade status. |
| **Emails** | Welcome on sign-up, study plan delivery, weekly digest every Monday, streak warning if you haven't studied by evening, and Pro upgrade confirmation — all styled HTML emails. |

### Previewing email templates (no mail server needed)

```bash
python scripts/test_emails.py
# HTML previews saved to scripts/email_previews/ — open any in your browser

# To send live test emails (requires MAIL_ENABLED=true in .env):
python scripts/test_emails.py --send your@email.com
```

---

## Project structure

```
app/
├── auth/           Registration, login, logout
├── billing/        Free / Pro tier, mock payment, upgrade confirmation email
├── chat/           AI tutor chat via Claude
├── analysis/       Weak-area dashboard and daily missions
├── quiz/           Practice questions loaded from static/questions.json
├── study_plan/     AI-generated study plan (Claude Sonnet)
├── social/         XP engine, missions, leaderboard, friends, challenges
├── profile/        Avatar, display name, password change
├── storage/        Fernet-encrypted JSON user store
├── templates/
│   └── email/      HTML email templates (welcome, digest, streak, upgrade)
├── static/
│   ├── css/main.css        Glassmorphism UI
│   └── questions.json      100-question LSAT bank
└── email_service.py        Flask-Mail senders for all email types
scripts/
└── test_emails.py  Render or live-send email template previews
```
