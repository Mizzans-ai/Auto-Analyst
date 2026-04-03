"""
CLI runner — test the agent without Gradio
Usage: python cli.py data.csv "Which category has highest sales?"
"""

import sys
import os
from agent import run_analysis


def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <path_to_csv> [\"optional question\"]")
        sys.exit(1)

    csv_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.getenv("GROQ_API_KEY"):
        api_key = input("Groq API key (free at console.groq.com): ").strip()
        os.environ["GROQ_API_KEY"] = api_key

    print(f"\nAnalysing: {csv_path}")
    if question:
        print(f"Question:  {question}")
    print("─" * 60)

    result = run_analysis(csv_path, question)

    print("\n" + "═" * 60)
    print("AGENT REPORT")
    print("═" * 60)
    print(result["insight"])

    if result["chart_paths"]:
        print(f"\nCharts saved: {', '.join(result['chart_paths'])}")

    if result["error"]:
        print(f"\n⚠ Error after retries:\n{result['error']}")


if __name__ == "__main__":
    main()
