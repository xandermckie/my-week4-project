# Ratio — LSAT Tutor

Ratio is a web-based LSAT preparation tool powered by Claude (Anthropic's AI). It gives students a private tutoring experience that adapts to their weak areas: an AI tutor explains reasoning concepts on demand, a practice quiz bank tracks which question types trip them up, and a personalized week-by-week study plan is generated from that data. Gamification features — daily streaks, XP, league rankings, daily missions, and friend challenges — keep students accountable between sessions. All user data is encrypted at rest with Fernet symmetric encryption; API keys are never exposed to the browser.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 or later |
| pip | Comes with Python |
| An Anthropic API key | [console.anthropic.com](https://console.anthropic.com) → API Keys → Create key |

> **Getting an API key:** Sign up at [console.anthropic.com](https://console.anthropic.com), add billing, then go to **API Keys** and click **Create Key**. Copy the key — you only see it once.

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/xandermckie/my-week4-project.git
cd my-week4-project

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
```

Open `.env` and fill in all three required values:

```dotenv
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-random-32-character-secret-key

# From console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-...

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=your-base64-fernet-key
```

---

## How to run

```bash
python run.py
```

The server starts at **http://127.0.0.1:5000** in debug mode.

---

## What happens when it runs

1. **Register** at `/register` with an email and password. Agree to the terms of service. Your account is created and you are dropped into the chat.

2. **Tutor chat** (`/chat`) — type any LSAT question, concept, or argument you want explained. Claude responds as a dedicated LSAT coach. Free users get 25 messages per day; Pro users get 50.

3. **Quiz** (`/quiz`) — one question at a time from a 1,000-question bank spanning all LSAT question types (Weaken, Strengthen, Assumption, Flaw, Inference, Main Point, Parallel Reasoning, Principle, Resolve, Reading Comprehension, and more). Each answer earns XP and updates your weak-area tally.

4. **Analysis** (`/analysis`) — a dashboard of your weak areas ranked by error count, plus today's three daily missions with live progress bars.

5. **Study Plan** (`/study-plan`) — enter your exam date and Claude generates a week-by-week plan tailored to your weak areas. Download it as a `.ics` calendar file or have it emailed to you.

6. **Leaderboard** (`/leaderboard`) — see the global top 20 by XP and a friends-only ranking. Your current level, league (Bronze through Diamond), and rank are displayed.

7. **Friends and Challenges** (`/friends`) — add friends by username or email, send 24-hour challenges (XP Race, Question Blitz, Accuracy Duel), and track live scores.

8. **Profile** (`/`) — upload an avatar, set a display name, change your password, view your XP progress bar, and upgrade to Pro.

**Output you can expect:** Claude responses appear as plain text in the chat window. Quiz results show immediately with the correct answer highlighted and a one-paragraph explanation. The study plan renders as formatted markdown on screen and is optionally emailed to you.
