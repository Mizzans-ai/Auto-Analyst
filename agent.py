"""
Autonomous Data Analyst Agent
Uses LangGraph + LangChain + Pandas + Matplotlib + Groq
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, Annotated
import operator

import pandas as pd
import numpy as np

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END


# ── LLM setup ──────────────────────────────────────────────────────────────────

def get_llm():
    # ✅ FIXED: API key set directly as value
    api_key = "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"
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=api_key,
    )


# ── Agent State ────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    csv_path: str
    df_info: str
    messages: Annotated[list, operator.add]
    generated_code: str
    execution_output: str
    execution_error: str
    chart_paths: list
    insight: str
    iterations: int
    max_iterations: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def df_to_info_string(df: pd.DataFrame) -> str:
    buf = []
    buf.append(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    buf.append("\nColumn dtypes:")
    for col, dtype in df.dtypes.items():
        buf.append(f"  {col}: {dtype}")
    buf.append("\nFirst 5 rows (as CSV):")
    buf.append(df.head(5).to_csv(index=False))
    buf.append("\nBasic stats:")
    try:
        buf.append(df.describe().to_string())
    except:
        buf.append("No numeric columns.")
    null_counts = df.isnull().sum()
    if null_counts.any():
        buf.append("\nNull counts:")
        buf.append(null_counts[null_counts > 0].to_string())
    return "\n".join(buf)


def extract_python_code(text: str) -> str:
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


# ── Node 1: Schema Reader ─────────────────────────────────────────────────────

def schema_reader_node(state: AgentState) -> dict:
    print("\n[1/5] SchemaReader — loading CSV...")
    df = pd.read_csv(state["csv_path"])
    info = df_to_info_string(df)
    print(f"      {df.shape[0]} rows x {df.shape[1]} cols | columns: {list(df.columns)}")
    return {
        "df_info": info,
        "messages": [SystemMessage(content=(
            "You are an expert data analyst. Write clean Python using pandas and matplotlib. "
            "Always add 'import matplotlib; matplotlib.use(\"Agg\")' at the top. "
            "Save charts as chart_1.png, chart_2.png etc. Never use plt.show(). "
            "Always call plt.close() after savefig. Print all key insights."
        ))],
        "chart_paths": [],
        "iterations": 0,
    }


# ── Node 2: Code Generator ─────────────────────────────────────────────────────

CODE_PROMPT = """
You have a CSV file at this exact path: {csv_path}

Dataset info:
{df_info}

User request: {user_request}

Write a complete, runnable Python script that:
1. Starts with:
   import matplotlib
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt
   import pandas as pd
   import numpy as np

2. Loads the CSV: df = pd.read_csv(r'{csv_path}')
3. Performs the requested analysis
4. Saves charts: plt.savefig('chart_1.png', dpi=150, bbox_inches='tight')
5. Calls plt.close() after every savefig
6. Prints findings clearly

RULES:
- Only use: pandas, matplotlib, numpy
- NEVER use plt.show()
- Handle NaN values with .dropna() or .fillna(0)
- Use only column names that exist in the dataset above

Return ONLY a ```python code block.
"""

def code_generator_node(state: AgentState) -> dict:
    print("\n[2/5] CodeGenerator — writing analysis code...")
    llm = get_llm()

    user_request = "Perform a comprehensive exploratory data analysis"
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_request = msg.content
            break

    prompt = CODE_PROMPT.format(
        csv_path=state["csv_path"],
        df_info=state["df_info"],
        user_request=user_request,
    )

    response = llm.invoke(state["messages"] + [HumanMessage(content=prompt)])
    code = extract_python_code(response.content)
    print(f"      Generated {len(code.splitlines())} lines of code")

    return {
        "generated_code": code,
        "messages": [AIMessage(content=response.content)],
    }


# ── Node 3: Code Executor ─────────────────────────────────────────────────────

def code_executor_node(state: AgentState) -> dict:
    print("\n[3/5] Executor — running generated code...")

    csv_dir = str(Path(state["csv_path"]).parent.resolve())

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=csv_dir
    ) as f:
        f.write(state["generated_code"])
        script_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=csv_dir,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            print(f"      ❌ Error: {stderr[:200]}")
            return {
                "execution_output": stdout,
                "execution_error": stderr,
                "iterations": state["iterations"] + 1,
            }

        charts = sorted([str(p) for p in Path(csv_dir).glob("chart_*.png")])
        print(f"      ✅ Success | Charts: {charts}")

        return {
            "execution_output": stdout,
            "execution_error": "",
            "chart_paths": charts,
            "iterations": state["iterations"] + 1,
        }

    except subprocess.TimeoutExpired:
        return {
            "execution_output": "",
            "execution_error": "Code timed out after 60 seconds.",
            "iterations": state["iterations"] + 1,
        }
    finally:
        Path(script_path).unlink(missing_ok=True)


# ── Node 4: Debugger ──────────────────────────────────────────────────────────

def debugger_node(state: AgentState) -> dict:
    print(f"\n[4/5] Debugger — fixing error (attempt {state['iterations']})...")
    llm = get_llm()

    prompt = f"""
Fix this Python code that failed with the error below.

ERROR:
{state['execution_error']}

CODE:
```python
{state['generated_code']}
```

Common fixes:
- Add: import matplotlib; matplotlib.use('Agg') at the very top
- Use r'...' raw string for file paths
- Drop NaN before plotting
- Use only column names that exist in the data

Return ONLY a fixed ```python code block.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    fixed_code = extract_python_code(response.content)
    print("      Fixed code ready")

    return {
        "generated_code": fixed_code,
        "messages": [AIMessage(content=response.content)],
    }


# ── Node 5: Insight Generator ─────────────────────────────────────────────────

def insight_generator_node(state: AgentState) -> dict:
    print("\n[5/5] InsightGenerator — writing report...")
    llm = get_llm()

    prompt = f"""
A Python data analysis produced this output:

{state['execution_output'] or '(no output captured)'}

Dataset structure:
{state['df_info']}

Write a clear analyst report:
1. Key findings (bullet points with specific numbers)
2. Interesting patterns or anomalies
3. Recommended next steps

Write for a non-technical business audience.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    print("      ✅ Report complete!")
    return {"insight": response.content}


# ── Routing ───────────────────────────────────────────────────────────────────

def should_debug(state: AgentState) -> str:
    # ✅ FIXED: routing keys match graph node names exactly
    if state["execution_error"] and state["iterations"] < state["max_iterations"]:
        return "debug"
    return "insight"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("schema",  schema_reader_node)
    g.add_node("code",    code_generator_node)
    g.add_node("exec",    code_executor_node)
    g.add_node("debug",   debugger_node)
    g.add_node("insight", insight_generator_node)

    g.set_entry_point("schema")
    g.add_edge("schema", "code")
    g.add_edge("code",   "exec")

    # ✅ FIXED: routing return values match node names ("debug" and "insight")
    g.add_conditional_edges("exec", should_debug, {
        "debug":   "debug",
        "insight": "insight",
    })

    g.add_edge("debug",   "exec")
    g.add_edge("insight", END)

    return g.compile()


# ── Public API ────────────────────────────────────────────────────────────────

def run_analysis(csv_path: str, user_request: str = "") -> dict:
    app = build_graph()

    state: AgentState = {
        "csv_path":        csv_path,
        "df_info":         "",
        "messages":        [HumanMessage(content=user_request)] if user_request else [],
        "generated_code":  "",
        "execution_output":"",
        "execution_error": "",
        "chart_paths":     [],
        "insight":         "",
        "iterations":      0,
        "max_iterations":  3,
    }

    final = app.invoke(state)

    return {
        "insight":     final.get("insight", ""),
        "chart_paths": final.get("chart_paths", []),
        "output":      final.get("execution_output", ""),
        "error":       final.get("execution_error", ""),
    }