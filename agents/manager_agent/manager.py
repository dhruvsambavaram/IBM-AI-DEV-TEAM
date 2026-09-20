"""
manager.py — Manager Agent logic
Pure Python, no LLM calls. Reads a completed task JSON + agent_stats.json,
updates the rolling-window stats store, and produces a structured report.

Usage:
    python agents/manager_agent/manager.py --task <path_to_completed_task.json>
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Agents tracked in stats (excludes "human" and "reflection_agent")
TRACKED_AGENTS = ["pm_agent", "architect_agent", "coding_agent", "testing_agent", "review_agent"]

STATS_PATH = os.path.join(os.path.dirname(__file__), "agent_stats.json")

# Rolling window: only the last WINDOW_SIZE outcomes per agent are evaluated.
# This means an agent that failed early but was fixed by the Reflection Agent
# will recover quickly on the graph, rather than being permanently dragged down
# by historical failures. We track current behavior, not all-time history.
#
# IMPROVEMENT 1: Expanded from 5 → 10 to give more stable signal before
# triggering a reflection — prevents thrashing where a single bad run
# immediately triggers a rewrite.
WINDOW_SIZE = 10

# Canonical threshold rule: flag an agent when its rolling-window success rate
# is below UNDERPERFORM_THRESHOLD and it has at least MIN_RUNS runs in the window.
UNDERPERFORM_THRESHOLD = 0.6
MIN_RUNS = 3

# IMPROVEMENT 7: Emergency trigger — force reflection after this many
# consecutive failures regardless of rolling rate.
CONSECUTIVE_FAILURE_EMERGENCY = 3


# -----------------------------------------------------------------------
# Stats store
# -----------------------------------------------------------------------

def initialize_empty_stats() -> dict:
    """Return a zeroed-out stats dict for all tracked agents."""
    return {
        agent: {
            "recent_outcomes": [],
            "runs": 0,
            "successes": 0,
            "rate": None,
            # IMPROVEMENT 2: Recovery detection fields
            "recovered": False,
            "previous_rate": None,
            # IMPROVEMENT 7: Consecutive failure tracking
            "consecutive_failures": 0,
        }
        for agent in TRACKED_AGENTS
    }


def load_stats(path: str = STATS_PATH) -> dict:
    """
    Load agent_stats.json. If the file doesn't exist or is malformed,
    return an initialized empty stats dict.
    """
    if not os.path.exists(path):
        return initialize_empty_stats()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure all tracked agents are present and have recent_outcomes
        for agent in TRACKED_AGENTS:
            if agent not in data:
                data[agent] = {
                    "recent_outcomes": [],
                    "runs": 0,
                    "successes": 0,
                    "rate": None,
                    "recovered": False,
                    "previous_rate": None,
                    "consecutive_failures": 0,
                }
            elif "recent_outcomes" not in data[agent]:
                # Migrate old format that didn't have recent_outcomes
                data[agent]["recent_outcomes"] = []
        return data
    except (json.JSONDecodeError, KeyError):
        return initialize_empty_stats()


def save_stats(stats: dict, path: str = STATS_PATH) -> None:
    """Write updated stats back to agent_stats.json (with profile fallback if locked)."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except OSError:
        try:
            home_dir = os.path.join(os.path.expanduser("~"), ".ai_dev_team")
            os.makedirs(home_dir, exist_ok=True)
            with open(os.path.join(home_dir, "agent_stats.json"), "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
        except Exception:
            pass


# -----------------------------------------------------------------------
# IMPROVEMENT 3: Failure category classification
# -----------------------------------------------------------------------

def classify_failure(summary: str) -> str:
    """
    Classify a failure output_summary string into a category.

    Categories:
        - "empty_output": agent returned empty string or empty JSON
        - "json_parse_error": agent returned malformed JSON
        - "validation_error": output passed JSON parse but failed schema validation
        - "blocked_by_review": review agent found HIGH severity findings
        - "timeout": agent timed out
        - "rate_limit": 429 from Groq API
        - "unknown": none of the above

    Returns the category string.
    """
    if not summary:
        return "unknown"
    lower = summary.lower()

    if "empty" in lower:
        return "empty_output"
    if "parse" in lower or "json" in lower or "could not parse" in lower:
        return "json_parse_error"
    if "validation" in lower or "failed validation" in lower:
        return "validation_error"
    if "high" in lower and "finding" in lower:
        return "blocked_by_review"
    if "timeout" in lower:
        return "timeout"
    if "429" in lower or "rate limit" in lower or "rate_limit" in lower:
        return "rate_limit"
    return "unknown"


# -----------------------------------------------------------------------
# Core logic
# -----------------------------------------------------------------------

def update_stats(task_obj: dict, stats: dict, window_size: int = WINDOW_SIZE) -> dict:
    """
    Iterate task_obj["history"]. For each entry belonging to a tracked agent
    with a non-null success value:
      1. Append the True/False outcome to that agent's recent_outcomes list.
      2. Cap the list at window_size (drop oldest if over limit).
      3. Recompute runs = len(recent_outcomes), successes = sum(recent_outcomes),
         rate = successes / runs.

    IMPROVEMENT 2: Before updating, store the current rate as previous_rate
    for recovery detection. After updating, check if the agent has recovered.

    IMPROVEMENT 7: Track consecutive_failures — increment on False, reset on True.

    Using a rolling window means the stats reflect an agent's *current* behavior.
    After a Reflection Agent rewrite, improvements show up within WINDOW_SIZE runs
    rather than being diluted by old failures forever.

    Returns the updated stats dict (mutates in place and returns).
    """
    for entry in task_obj.get("history", []):
        agent = entry.get("agent")
        if agent not in TRACKED_AGENTS:
            continue
        success = entry.get("success")
        if success is None:
            continue  # not yet evaluated — skip

        # IMPROVEMENT 2: Store current rate as previous_rate before update
        stats[agent]["previous_rate"] = stats[agent].get("rate")

        # Reset recovered flag before each update
        stats[agent]["recovered"] = False

        # Append new outcome and enforce window cap
        stats[agent]["recent_outcomes"].append(bool(success))
        if len(stats[agent]["recent_outcomes"]) > window_size:
            stats[agent]["recent_outcomes"] = stats[agent]["recent_outcomes"][-window_size:]

        # Recompute derived fields from the window
        outcomes = stats[agent]["recent_outcomes"]
        stats[agent]["runs"] = len(outcomes)
        stats[agent]["successes"] = sum(outcomes)
        stats[agent]["rate"] = stats[agent]["successes"] / stats[agent]["runs"]

        # IMPROVEMENT 7: Track consecutive failures
        consecutive = stats[agent].get("consecutive_failures", 0)
        if bool(success):
            stats[agent]["consecutive_failures"] = 0
        else:
            stats[agent]["consecutive_failures"] = consecutive + 1

        # IMPROVEMENT 2: Recovery detection — if agent was underperforming
        # (previous_rate existed and was below threshold) and now rate >= 0.7
        prev_rate = stats[agent].get("previous_rate")
        curr_rate = stats[agent]["rate"]
        if prev_rate is not None and prev_rate < UNDERPERFORM_THRESHOLD and curr_rate >= 0.7:
            stats[agent]["recovered"] = True
            print(f"[manager] {agent} has recovered — rate climbed from {prev_rate:.2f} to {curr_rate:.2f}")

    return stats


def get_underperformers(
    stats: dict,
    threshold: float = UNDERPERFORM_THRESHOLD,
    min_runs: int = MIN_RUNS,
) -> list:
    """
    Return list of agent names where the rolling-window success rate is below
    the threshold and there are at least min_runs runs in the current window.

    Canonical rule: rate < 0.6 AND runs >= 3.
    """
    result = []
    for agent, data in stats.items():
        if data.get("rate") is None:
            continue
        if data.get("runs", 0) >= min_runs and data["rate"] < threshold:
            result.append(agent)
    return result


def extract_failure_patterns(task_obj: dict, underperformers: list) -> dict:
    """
    For each underperforming agent, scan:
    - task_obj["review_result"]["findings"] for checklist_item values
    - task_obj["history"] for failure entries (success == False) and their output_summary

    IMPROVEMENT 3: Returns a dict of {agent_name: [{"pattern": str, "category": str}, ...]}
    instead of {agent_name: [str, ...]}.
    """
    patterns = {agent: [] for agent in underperformers}

    # Pull from review_result findings (most specific signal)
    review = task_obj.get("review_result")
    if review and isinstance(review.get("findings"), list):
        for finding in review["findings"]:
            item = finding.get("checklist_item", "")
            # Review findings don't have direct agent attribution, but coding_agent
            # produced the code — attribute review findings to it
            if "coding_agent" in patterns and item:
                existing_patterns = [p["pattern"] for p in patterns["coding_agent"]]
                if item not in existing_patterns:
                    patterns["coding_agent"].append({
                        "pattern": item,
                        "category": classify_failure(item),
                    })

    # Pull from history summaries of failed runs
    for entry in task_obj.get("history", []):
        agent = entry.get("agent")
        if agent in patterns and entry.get("success") is False:
            summary = entry.get("output_summary", "")
            if summary:
                pattern_text = f"failed run: {summary}"
                existing_patterns = [p["pattern"] for p in patterns[agent]]
                if pattern_text not in existing_patterns:
                    patterns[agent].append({
                        "pattern": pattern_text,
                        "category": classify_failure(summary),
                    })

    return patterns


def build_reasoning(
    task_obj: dict, underperformers: list, stats: dict, patterns: dict
) -> str:
    """Build a human-readable reasoning string from the underperformer data."""
    if not underperformers:
        return "All agents performing at or above threshold."
    parts = []
    for agent in underperformers:
        data = stats[agent]
        rate_pct = f"{data['rate']:.0%}" if data.get("rate") is not None else "N/A"
        agent_patterns = patterns.get(agent, [])
        # IMPROVEMENT 3: patterns are now dicts — extract the pattern strings
        pattern_str = (
            "; ".join(f"'{p['pattern']}'" for p in agent_patterns)
            if agent_patterns
            else "no specific pattern identified"
        )
        trigger = data.get("_trigger_reason", "low_rate")
        trigger_note = " [EMERGENCY: consecutive failures]" if trigger == "consecutive_failures" else ""
        parts.append(
            f"{agent} succeeded {data['successes']}/{data['runs']} runs in current window "
            f"(rate={rate_pct}){trigger_note}; failure patterns: {pattern_str}"
        )
    return " | ".join(parts)


def generate_report(task_obj: dict, stats: dict) -> dict:
    """
    Assemble and return the Manager Agent output JSON.
    Manager Agent reasoning is 100% deterministic Python -- no LLM calls,
    no coins spent, fully auditable. This is a deliberate design choice: the
    trigger decision itself can never hallucinate or vary between runs.

    IMPROVEMENT 7: Also flags agents with consecutive_failures >= CONSECUTIVE_FAILURE_EMERGENCY
    as underperformers with trigger_reason="consecutive_failures".
    """
    underperformers = get_underperformers(stats)

    # IMPROVEMENT 7: Emergency trigger for consecutive failures
    for agent in TRACKED_AGENTS:
        data = stats.get(agent, {})
        consec = data.get("consecutive_failures", 0)
        if consec >= CONSECUTIVE_FAILURE_EMERGENCY and agent not in underperformers:
            underperformers.append(agent)
            data["_trigger_reason"] = "consecutive_failures"
            print(f"[manager] EMERGENCY: {agent} has failed {consec} times in a row — forcing reflection")

    # Tag trigger_reason on each underperformer for reporting
    for agent in underperformers:
        if "_trigger_reason" not in stats.get(agent, {}):
            stats[agent]["_trigger_reason"] = "low_rate"

    patterns = extract_failure_patterns(task_obj, underperformers)
    reasoning = build_reasoning(task_obj, underperformers, stats, patterns)
    recommended_action = "rewrite_prompt" if underperformers else "none"

    # IMPROVEMENT 3: Aggregate failure categories per underperformer
    failure_categories = {}
    for agent in underperformers:
        agent_patterns = patterns.get(agent, [])
        categories = [p["category"] for p in agent_patterns]
        failure_categories[agent] = list(dict.fromkeys(categories)) if categories else ["unknown"]

    # Build per-agent stats array matching the spec output shape
    agent_stats_array = []
    for agent in TRACKED_AGENTS:
        data = stats[agent]
        outcomes = data.get("recent_outcomes", [])
        failures = outcomes.count(False)
        trigger_reason = data.get("_trigger_reason", "")
        agent_stats_array.append({
            "agent": agent,
            "runs_evaluated": data.get("runs", 0),
            "successes": data.get("successes", 0),
            "failures": failures,
            "success_rate": data.get("rate"),
            "recent_outcomes": outcomes,
            "trigger_reflection": agent in underperformers,
            "trigger_reason": trigger_reason if agent in underperformers else "",
            "consecutive_failures": data.get("consecutive_failures", 0),
            "recovered": data.get("recovered", False),
            "reason": (
                reasoning if agent in underperformers
                else (
                    f"no failures in current window (rate={data['rate']:.0%})"
                    if data.get("rate") is not None and data["rate"] >= UNDERPERFORM_THRESHOLD
                    else "insufficient runs (fewer than 3 in window)"
                    if data.get("runs", 0) < MIN_RUNS
                    else "no data yet"
                )
            ),
        })

    # Clean up internal-only keys
    for agent in TRACKED_AGENTS:
        stats[agent].pop("_trigger_reason", None)

    return {
        "run_id": f"run_{task_obj.get('task_id', 'unknown')}",
        "task_id": task_obj.get("task_id", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_stats": agent_stats_array,
        # Convenience fields kept for backward compat with pipeline + reflection
        "underperformers": underperformers,
        "recommended_action": recommended_action,
        "reasoning": reasoning,
        # IMPROVEMENT 3: Failure categories per underperformer
        "failure_categories": failure_categories,
        # Full snapshot for dashboard
        "stats_snapshot": stats,
    }


# -----------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------

def run(task_path: str, stats_path: str = STATS_PATH) -> dict:
    """
    Full Manager Agent run:
    1. Load task JSON
    2. Load stats
    3. Update rolling-window stats from task history
    4. Save stats
    5. Generate and return report
    """
    with open(task_path, "r", encoding="utf-8") as f:
        task_obj = json.load(f)

    stats = load_stats(stats_path)
    stats = update_stats(task_obj, stats)
    save_stats(stats, stats_path)
    report = generate_report(task_obj, stats)
    return report


def main():
    parser = argparse.ArgumentParser(description="Manager Agent -- analyse pipeline run stats")
    parser.add_argument("--task", required=True, help="Path to completed task JSON file")
    parser.add_argument(
        "--stats",
        default=STATS_PATH,
        help=f"Path to agent_stats.json (default: {STATS_PATH})",
    )
    args = parser.parse_args()

    if not os.path.exists(args.task):
        print(f"ERROR: task file not found: {args.task}", file=sys.stderr)
        sys.exit(1)

    report = run(args.task, args.stats)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
