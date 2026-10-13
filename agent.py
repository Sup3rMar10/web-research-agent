"""A tiny web research agent: give it a topic, it searches the live web and saves a cited Markdown report.

Usage: python agent.py "state of open-source LLM inference engines"
"""
import re
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-5-5"
MAX_STEPS = 12  # safety cap on model turns per run
REPORTS = Path("reports")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

SYSTEM = (
    "You are a web research analyst. Search the web for current, reputable sources, cross-check key claims, "
    "then call save_report exactly once with a concise Markdown report: a short summary, key findings as "
    "bullets, and a Sources section listing every URL you relied on. Never state facts you did not find."
)

TOOLS = [
    # Server-side tool: Anthropic runs the searches, so there is no function to implement.
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 6},
    # Client-side tool: runs here, on this machine.
    {
        "name": "save_report",
        "description": "Save the finished Markdown report to disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Short name without extension, e.g. llm-inference"},
                "markdown": {"type": "string", "description": "The full report"},
            },
            "required": ["filename", "markdown"],
        },
    },
]


def save_report(filename: str, markdown: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", filename.lower()).strip("-") or "report"
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"{slug}.md"
    path.write_text(markdown, encoding="utf-8")
    return f"Saved {path}"


def research(topic: str) -> str:
    """The agent loop: Claude searches and reasons, and the script handles pauses and the save tool."""
    messages = [{"role": "user", "content": f"Research this topic and save a report: {topic}"}]
    for _ in range(MAX_STEPS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=TOOLS,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:  # show what the agent is searching for
            if block.type == "server_tool_use" and block.name == "web_search":
                print(f"  [search] {block.input.get('query')}")

        if response.stop_reason == "pause_turn":  # server-side tool loop hit its limit: just continue
            continue
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text") or f"Stopped: {response.stop_reason}"

        results = []
        for block in response.content:
            if block.type == "tool_use":  # only our own tool arrives here; web_search ran server-side
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": save_report(**block.input)}
                )
        messages.append({"role": "user", "content": results})
    return "Stopped: step limit reached."


if __name__ == "__main__":
    print(research(" ".join(sys.argv[1:]) or "recent advances in small language models"))
