"""
Gradio UI — Autonomous Data Analyst Agent
Run: python app.py
"""

import os
import glob
from pathlib import Path
import gradio as gr
from agent import run_analysis
from PIL import Image


# ── Core function ─────────────────────────────────────────────────────────────

def analyse(csv_file, user_request: str, progress=gr.Progress()):
    if not csv_file:
        return (
            "### ❌ No file uploaded\nPlease upload a CSV file to get started.",
            [],
            "",
            gr.update(visible=False),
        )

    try:
        csv_path = csv_file.name
    except AttributeError:
        csv_path = str(csv_file)

    csv_dir = str(Path(csv_path).parent.resolve())

    # Clean old charts in csv_dir
    for f in glob.glob(os.path.join(csv_dir, "chart_*.png")):
        try:
            os.remove(f)
        except:
            pass

    progress(0.1, desc="📂 Reading your CSV...")

    try:
        progress(0.3, desc="🧠 Agent writing analysis code...")
        result = run_analysis(
            csv_path=csv_path,
            user_request=user_request.strip() if user_request else "Perform a comprehensive exploratory data analysis with charts",
        )
    except Exception:
        import traceback
        err = traceback.format_exc()
        return (
            f"### ❌ Agent crashed\n```\n{err}\n```",
            [],
            err,
            gr.update(visible=True),
        )

    progress(0.9, desc="✍️ Writing insights...")

    # Insight
    insight_md = result.get("insight", "") or "_No insight generated._"
    if result.get("error"):
        insight_md += f"\n\n---\n> ⚠️ **Execution error after retries:**\n```\n{result['error']}\n```"

    # Charts — look in csv_dir where they were saved
    charts = []
    for path in result.get("chart_paths", []):
        if os.path.exists(path):
            try:
                img = Image.open(path).copy()
                charts.append(img)
            except:
                pass

    # Also scan csv_dir in case paths differ
    if not charts:
        for p in sorted(Path(csv_dir).glob("chart_*.png")):
            try:
                img = Image.open(str(p)).copy()
                charts.append(img)
            except:
                pass

    raw_output = result.get("output") or "(no printed output captured)"

    progress(1.0, desc="✅ Done!")

    return (
        insight_md,
        charts,
        raw_output,
        gr.update(visible=True),
    )


# ── Custom CSS ────────────────────────────────────────────────────────────────

css = """
/* ── Page background ── */
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Header banner ── */
.header-box {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 24px;
    color: white;
}
.header-box h1 {
    font-size: 28px !important;
    font-weight: 700 !important;
    margin: 0 0 8px 0 !important;
    color: white !important;
}
.header-box p {
    font-size: 15px !important;
    color: #c7d2fe !important;
    margin: 0 !important;
    line-height: 1.6 !important;
}
.stack-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #e0e7ff;
    margin: 12px 4px 0 0;
}

/* ── Left panel card ── */
.input-panel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    height: fit-content;
}

/* ── Right panel card ── */
.output-panel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* ── Section labels ── */
.section-label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #6b7280 !important;
    margin-bottom: 8px !important;
}

/* ── File upload ── */
.file-upload-area {
    border: 2px dashed #c7d2fe !important;
    border-radius: 12px !important;
    background: #f5f3ff !important;
    transition: all 0.2s !important;
}
.file-upload-area:hover {
    border-color: #6366f1 !important;
    background: #ede9fe !important;
}

/* ── Analyse button ── */
.analyse-btn {
    background: linear-gradient(135deg, #4338ca, #6366f1) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 14px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.35) !important;
}
.analyse-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(99,102,241,0.45) !important;
}

/* ── Insight markdown area ── */
.insight-box .prose {
    font-size: 15px !important;
    line-height: 1.75 !important;
    color: #1f2937 !important;
}

/* ── Gallery ── */
.gallery-wrap {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Raw output accordion ── */
.raw-output {
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    background: #f9fafb !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}

/* ── Pipeline steps ── */
.pipeline-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 16px;
    font-size: 13px;
    color: #6b7280;
    flex-wrap: wrap;
}
.pipeline-step {
    background: #ede9fe;
    color: #5b21b6;
    border-radius: 6px;
    padding: 3px 10px;
    font-weight: 500;
    font-size: 12px;
}
.pipeline-arrow {
    color: #d1d5db;
    font-size: 14px;
}

/* ── Status indicator ── */
.status-bar {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    color: #166534;
    margin-top: 12px;
}

/* dark mode friendly */
@media (prefers-color-scheme: dark) {
    .input-panel, .output-panel {
        background: #1f2937 !important;
        border-color: #374151 !important;
    }
}
"""

# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(
    title="Auto  Analyst",
    css=css,
    theme=gr.themes.Base(
        primary_hue="indigo",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ),
) as demo:

    # ── Header ──
    gr.HTML("""
    <div class="header-box">
        <h1>🤖 Auto Analyst</h1>
        <p>Upload any CSV and ask a question — the agent writes Python code, executes it,
        auto-fixes errors, generates charts, and explains insights in plain English.</p>
        <span class="stack-badge">LangGraph</span>
        <span class="stack-badge">LangChain</span>
        <span class="stack-badge">Pandas</span>
        <span class="stack-badge">Matplotlib</span>
        <span class="stack-badge">LLaMA 3 · Groq</span>
    </div>
    """)

    # ── Main layout ──
    with gr.Row(equal_height=False):

        # ── Left: Inputs ──
        with gr.Column(scale=1, min_width=320, elem_classes="input-panel"):

            gr.HTML('<p class="section-label">📁 Upload your data</p>')
            csv_input = gr.File(
                label="",
                file_types=[".csv"],
                elem_classes="file-upload-area",
            )

            gr.HTML('<p class="section-label" style="margin-top:20px">💬 Your question</p>')
            request_input = gr.Textbox(
                label="",
                placeholder=(
                    "e.g. Which product has highest revenue?\n"
                    "Show sales trends over time.\n"
                    "Which region performs best?"
                ),
                lines=4,
            )

            gr.HTML('<p style="font-size:12px;color:#9ca3af;margin:8px 0 16px">Leave blank for full exploratory analysis</p>')

            run_btn = gr.Button(
                "🔍  Analyse Now",
                variant="primary",
                elem_classes="analyse-btn",
                size="lg",
            )

            gr.HTML("""
            <div class="pipeline-bar">
                <span class="pipeline-step">Schema</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-step">Code Gen</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-step">Execute</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-step">Auto-debug</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-step">Insight</span>
            </div>
            """)

        # ── Right: Outputs ──
        with gr.Column(scale=2, elem_classes="output-panel"):

            gr.HTML('<p class="section-label">📊 Agent report</p>')
            insight_output = gr.Markdown(
                value="*Upload a CSV and click **Analyse Now** to get started.*",
                elem_classes="insight-box",
            )

            results_group = gr.Group(visible=False)
            with results_group:
                gr.HTML('<p class="section-label" style="margin-top:24px">📈 Generated charts</p>')
                chart_output = gr.Gallery(
                    label="",
                    columns=2,
                    height=420,
                    object_fit="contain",
                    elem_classes="gallery-wrap",
                    show_label=False,
                )

                with gr.Accordion("🖥️  Raw code output", open=False):
                    raw_output = gr.Textbox(
                        label="",
                        lines=8,
                        elem_classes="raw-output",
                        show_label=False,
                    )

    # ── Wire up ──
    run_btn.click(
        fn=analyse,
        inputs=[csv_input, request_input],
        outputs=[insight_output, chart_output, raw_output, results_group],
        show_progress=True,
    )


if __name__ == "__main__":
    demo.launch(share=False)