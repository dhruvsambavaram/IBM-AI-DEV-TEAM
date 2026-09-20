# Fix: Remove Hard 900-Token Cap in iam_auth.py

## Top-Level Overview

The function `call_bob_chat()` in `orchestration/iam_auth.py` hard-caps every LLM call to
900 output tokens regardless of what the caller requests. This silently truncates agents
that legitimately need large outputs — the Coding Agent calls with `max_tokens=8192` and the
pipeline's LLM function calls with `max_tokens=3000`, but both are cut to 900. A unified
diff for even a small file change typically exceeds 900 tokens, making this the primary root
cause of truncated diffs and `_extract_code_diff_fallback` being triggered.

The correct fix is to replace the blanket 900 cap with a model-level ceiling (32 768, the
Groq model output limit) that is also overridable via a `GROQ_MAX_OUTPUT_TOKENS` env var.
Groq free-tier OTPM (output-tokens-per-minute) rate limits are enforced by the API as
retriable 429 errors — they must not be absorbed by pre-truncating every call.

---

## Sub-Tasks

### Sub-Task 1 — Replace the 900 cap with a configurable model-level ceiling

**Intent**
Remove `min(max_tokens, 900)` and replace it with `min(max_tokens, _MAX_OUTPUT_TOKENS)`
where `_MAX_OUTPUT_TOKENS` defaults to 32 768 but can be overridden via the
`GROQ_MAX_OUTPUT_TOKENS` environment variable. Update the docstring to explain the new
behaviour accurately.

**Expected Outcomes**
- `call_bob_chat(..., max_tokens=8192)` now sends `max_tokens=8192` to the Groq API.
- `call_bob_chat(..., max_tokens=3000)` now sends `max_tokens=3000`.
- `call_bob_chat(..., max_tokens=50000)` is still capped at 32 768 (model limit).
- Setting `GROQ_MAX_OUTPUT_TOKENS=4096` in the environment lowers the ceiling for
  constrained deployments without touching code.
- The function docstring no longer mentions the 900 free-tier heuristic.

**Todo List**
1. Add module-level constant `_MAX_OUTPUT_TOKENS` above `call_bob_chat`, reading from
   `GROQ_MAX_OUTPUT_TOKENS` env var with default `32768`.
2. Replace line 68 (`max_tokens = min(max_tokens, 900)`) with
   `max_tokens = min(max_tokens, _MAX_OUTPUT_TOKENS)`.
3. Update the `max_tokens` parameter description in the docstring to document the new
   ceiling and the env-var override.
4. Remove the stale inline comment `# Stay within Groq free-tier OTPM limit`.

**Relevant Context**
- File: `orchestration/iam_auth.py`, line 68
- Callers and their requested limits:
  - `agents/coding_agent/coding_agent.py:423` — `max_tokens=8192`
  - `orchestration/pipeline.py:424` — `max_tokens=3000`
  - `orchestration/pipeline.py:462` — `max_tokens=2000`
  - `agents/reflection_agent/reflection.py:217` — `max_tokens=3000`
  - `agents/review_agent/review_agent.py:137` — `max_tokens=2500`
  - `agents/architect_agent/architect_agent.py:100` — `max_tokens=1500`
  - `agents/pm_agent/pm_agent.py:56` — `max_tokens=1200`
  - `agents/scaffold_agent/scaffold_agent.py:45` — `max_tokens=1500`
- Test file: `orchestration/test_iam_auth.py` — mocks `Groq` entirely; no assertion checks
  the value of `max_tokens` passed to the API, so no test changes are needed.

**Status** — `[ ] pending`

---

## No Other Files Need Changing

Every caller already passes a sensible `max_tokens` value that matches its actual need.
The fix is entirely contained in `orchestration/iam_auth.py`. No agent code, no pipeline
code, no tests need to change.
