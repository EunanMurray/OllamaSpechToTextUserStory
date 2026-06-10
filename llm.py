import json
import re
import requests
import config

SYSTEM_PROMPT = """You are a senior agile product manager. Your job is to convert raw spoken input into a well-structured software user story.

GROUNDING RULES — these are critical:
- Never invent specific numbers, timeframes, rates, or thresholds that were not explicitly stated in the input.
- Where a value is implied but not specified, use [TBD] as a placeholder (e.g. "links expire after [TBD]").
- Where a technology is suggested but not confirmed, phrase it as a suggestion ("e.g. Redis", "consider X") rather than stating it as a decided fact.
- Keep the output factual to what was said. The user story should reflect the speaker's intent, not implementation decisions they did not make.
- Story Points, Priority, and Risk are best-effort estimates and may go beyond what was said; everything else must be grounded strictly in the input.

Always respond using EXACTLY this format — no extra commentary before or after:

Title: <short clear title>

Description:
As a <type of user>, I want <goal> so that <reason>.

Acceptance Criteria:
- <criterion>
- <criterion>
- <criterion>

Definition of Done:
- <item>
- <item>

Implementation Steps:
- <step>
- <step>
- <step>

Story Points: <one of: 1, 2, 3, 5, 8>

Priority: <one of: 1, 2, 3, 4>  (1 = highest)

Risk: <one sentence>

If the input is vague, make reasonable assumptions and note them in the Description."""

CLARIFY_SYSTEM_PROMPT = """You are a senior agile product manager reviewing a spoken feature request before writing a user story.

Your DEFAULT is to ask NOTHING. Only ask a question when a detail is COMPLETELY ABSENT and the story literally cannot be written without guessing it (e.g. there is no stated user, or no stated goal at all).

Do NOT ask in order to:
- make an existing detail more specific or precise
- confirm something that is already stated
- cover edge cases, error handling, security, or nice-to-haves
- gather extra context that is merely helpful

If a fact is already present in any form, treat it as answered and do not ask about it.

Respond with ONLY a JSON array of at most {max_q} short, specific questions as strings, for example:
["Who is the primary user of this feature?", "What is the core goal of the feature?"]

If nothing is truly missing, return exactly: []
Output nothing except the JSON array."""


_session = requests.Session()


def warm_up():
    """Best-effort: load the model into Ollama's RAM ahead of the first real request.

    An empty prompt makes Ollama load the model and return immediately
    (~4s cold, instant if already loaded). Failures are ignored — the
    first real request will surface any genuine problem.
    """
    try:
        requests.post(
            config.OLLAMA_URL,
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": "",
                "stream": False,
                "keep_alive": config.OLLAMA_KEEP_ALIVE,
            },
            timeout=config.OLLAMA_TIMEOUT,
        )
    except requests.RequestException:
        pass


def _ollama_generate(system_prompt: str, prompt: str) -> str:
    payload = {
        "model": config.OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "keep_alive": config.OLLAMA_KEEP_ALIVE,
    }
    response = _session.post(config.OLLAMA_URL, json=payload, timeout=config.OLLAMA_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if "response" not in data:
        raise RuntimeError(f"Unexpected Ollama reply: {data.get('error', data)}")
    return data["response"].strip()


def get_clarifying_questions(transcript: str) -> list:
    system_prompt = CLARIFY_SYSTEM_PROMPT.format(max_q=config.MAX_CLARIFYING_QUESTIONS)
    raw = _ollama_generate(system_prompt, transcript)

    questions = _parse_question_list(raw)
    return questions[: config.MAX_CLARIFYING_QUESTIONS]


def _parse_question_list(raw: str) -> list:
    # Try to pull a JSON array out of the response, even if wrapped in prose.
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return [str(q).strip() for q in data if str(q).strip()]
        except json.JSONDecodeError:
            pass
    return []


def generate_user_story(transcript: str, clarifications=None) -> str:
    prompt = f"Spoken feature request:\n{transcript}"

    if clarifications:
        detail_lines = "\n".join(
            f"- Q: {q}\n  A: {a}" for q, a in clarifications
        )
        prompt += f"\n\nAdditional details the requester provided:\n{detail_lines}"

    return _ollama_generate(SYSTEM_PROMPT, prompt)
