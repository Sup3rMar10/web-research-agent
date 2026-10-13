# Web Research Agent

A minimal AI agent that researches a topic on the live web and saves a cited Markdown report. It's one Python file and one dependency.

```
$ python agent.py "state of open-source LLM inference engines"
  [search] open source LLM inference engines comparison
  [search] vLLM vs llama.cpp throughput benchmarks
  ...
Saved reports/llm-inference-engines.md
```

## How it works

The agent combines two kinds of tools in one loop:

| Tool | Type | Role |
|---|---|---|
| `web_search` | **Server-side**, run by Anthropic | Finds current sources. There's nothing to implement locally |
| `save_report` | **Client-side**, run by this script | Writes the final report to `reports/` |

The loop is hand-written and handles three cases:

1. `pause_turn`: the server-side search loop hit its limit, so the script re-sends the turn to continue it.
2. `tool_use`: Claude called `save_report`, so the script runs it and returns the result.
3. Anything else: Claude is done, and the script prints the final message.

The system prompt asks for a summary, key findings and a Sources list. It also tells the agent not to state facts it didn't find.

## Run

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python agent.py "your topic"
```

Reports are written to `./reports/` (git-ignored).

## Design notes

- Searches are capped at 6 per run (`max_uses`) and the loop at 12 turns, so cost and runtime are bounded.
- The report filename is sanitized to `[a-z0-9-]` and always written inside `reports/`, so the model can't write elsewhere on disk.
- Built on the Anthropic Python SDK with `claude-opus-5-5` and adaptive thinking.
- Web search must be enabled for your organization in the Anthropic Console.
