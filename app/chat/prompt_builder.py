"""Builds the system and user messages sent to Claude for each chat turn."""

import re

SYSTEM_PROMPT = """You are an expert LSAT tutor. When a student submits a question, response, or study note, always reply with a structured coaching breakdown using EXACTLY this format:

**Question Type:** [Logical Reasoning / Analytical Reasoning / Reading Comprehension / Other]
**Core Skill Being Tested:** [one sentence]
**Step-by-Step Reasoning Strategy:**
1. [first step]
2. [second step]
3. [additional steps as needed]
**Common Trap:** [one sentence describing the most common mistake on this question type]
**Memory Cue:** [a short, memorable phrase or pattern the student can use to recognize this question type quickly]

Be concise, direct, and encouraging. Avoid jargon that isn't standard LSAT terminology. If the student's answer is included, evaluate whether it is correct and explain why before giving the breakdown.

IMPORTANT: You may ONLY respond to messages about LSAT preparation, logical reasoning, reading comprehension, analytical reasoning, or follow-up clarifications about a previous response (e.g. "explain that more simply", "I don't understand step 2", "break that down further", "can you simplify that?"). If the message is clearly off-topic and unrelated to LSAT study, respond ONLY with: "I can only help with LSAT preparation. Please paste an LSAT question or describe a concept you are studying." Do not answer off-topic questions under any circumstances."""

_INJECTION_PATTERNS = re.compile(
    r"(ignore previous instructions?|disregard your instructions?|new instructions?:|"
    r"</?system>|you are now a)",
    re.IGNORECASE,
)
_FAKE_DELIMITERS = re.compile(r"[#=\-]{3,}")


def _sanitize_input(text: str) -> str:
    """Strip null bytes, fake section delimiters, and known prompt-injection phrases."""
    text = text.replace("\x00", "")
    text = _FAKE_DELIMITERS.sub(" ", text)
    text = _INJECTION_PATTERNS.sub("[redacted]", text)
    return text


def build_messages(
    user_input: str,
    turns: list[dict],
    summary: str,
    weak_areas: dict,
) -> list[dict]:
    """Assemble the messages list to send to Claude.

    Injects the session summary and weak-area context into the system prompt
    so every response is personalized to the student's history.

    Args:
        user_input: The student's latest message.
        turns: Recent (uncompressed) session turns as [{"role": ..., "content": ...}].
        summary: Compressed summary of older session turns.
        weak_areas: Dict mapping question type to error count, e.g. {"Weaken": 4}.

    Returns:
        A list of message dicts ready for anthropic.messages.create().
    """
    system = SYSTEM_PROMPT

    if weak_areas:
        ranked = sorted(weak_areas.items(), key=lambda x: x[1], reverse=True)
        area_lines = "\n".join(f"- {qtype} ({count} errors)" for qtype, count in ranked)
        system += f"\n\n**Student's Current Weak Areas (prioritize coaching on these):**\n{area_lines}"

    messages = []

    if summary:
        messages.append({
            "role": "user",
            "content": f"[Session summary from earlier in our study session: {summary}]",
        })
        messages.append({
            "role": "assistant",
            "content": "Understood — I have context from our earlier work together.",
        })

    messages.extend(turns)
    messages.append({"role": "user", "content": _sanitize_input(user_input)})

    return messages, system
