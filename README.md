# Autonomous Data Analyst Agent

An agentic AI that takes any CSV, writes Python analysis code, executes it,
auto-debugs errors, generates charts, and explains findings in plain English.

## Agent graph

```
Schema Reader → Code Generator → Code Executor ──(error)──→ Debugger ─┐
                                        │                               │
                                        └──(success)──→ Insight Gen → END
                                                (also loops back from Debugger)
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get a FREE Groq API key (no credit card needed)
#    → https://console.groq.com
#    Set it as an env var:
export GROQ_API_KEY=gsk_your_key_here

# 3a. Run the Gradio web UI
python app.py
# Open http://localhost:7860

# 3b. Or use the CLI
python cli.py sample_data.csv "Which category generates the most revenue?"
```

## Using Ollama instead of Groq (100% local/offline)

```bash
# Install Ollama: https://ollama.com
ollama pull mistral   # or llama3.2, qwen2.5, deepseek-r1

# In agent.py, replace get_llm() with:
from langchain_ollama import ChatOllama
def get_llm():
    return ChatOllama(model="mistral", temperature=0)
```

## Project structure

```
data_analyst_agent/
├── agent.py          # LangGraph agent (all nodes + graph)
├── app.py            # Gradio web UI
├── cli.py            # CLI runner for quick testing
├── requirements.txt
├── sample_data.csv   # Sample sales data to test with
└── README.md
```

## What each LangGraph node does

| Node | What it does |
|---|---|
| `schema_reader` | Loads CSV, builds schema + sample string for the LLM |
| `code_generator` | Asks LLM to write pandas + matplotlib analysis code |
| `code_executor` | Runs code in a subprocess, captures stdout + charts |
| `debugger` | If code errors, asks LLM to fix it (up to 3 retries) |
| `insight_generator` | Turns printed output into a plain-English report |

## CV talking points for this project

- "Built a multi-node LangGraph agent with automatic error recovery"
- "Implemented a code-generation → execution → self-debug loop"
- "Used structured state passing between agent nodes"
- "LLM-generated analysis code runs safely in subprocess isolation"
