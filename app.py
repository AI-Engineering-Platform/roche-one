import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import difflib  # for HTML diff
import re       # for section heading detection

import gradio as gr
import matplotlib.pyplot as plt

from config import (
    INPUT_DATA_JSON,
    CSR_TEMPLATE_PATH,
    CSR_SAMPLE_REPORT_PATH,
    GENERATED_CSR_PATH,
    CONFIDENCE_THRESHOLD,
    MAX_ITERATIONS,
)
from utils.logging_utils import setup_logger
from utils.file_utils import read_docx_text

from agents.knowledge_agent import KnowledgeAgent
from agents.document_composer_agent import DocumentComposerAgent
from agents.reviewer_agent import ReviewerAgent
from agents.compliance_agent import ComplianceAgent
from agents.reviser_agent import ReviserAgent

logger = setup_logger("CSR-Gradio-App")


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def _copy_uploaded_file(uploaded, target_path: str) -> str:
    """Copy a Gradio UploadedFile to the configured path."""
    if uploaded is None:
        raise ValueError(f"Missing required file for {target_path}")

    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(uploaded.name, target)
    return str(target)


def save_clinical_json(uploaded_file) -> str:
    """Handle upload of clinical JSON for Tab 1."""
    if uploaded_file is None:
        return "⚠️ No file uploaded."

    try:
        dest = _copy_uploaded_file(uploaded_file, INPUT_DATA_JSON)
        msg = f"✅ Clinical JSON saved to: {dest}"
        logger.info(msg)
        return msg
    except Exception as e:
        logger.exception("Error saving clinical JSON")
        return f"❌ Error saving clinical JSON: {e}"


def _plot_score_history(score_history: List[Dict[str, float]]):
    """Return a matplotlib figure for Gradio showing score evolution."""
    if not score_history:
        return None

    iterations = [s["iteration"] for s in score_history]
    review_scores = [s["review"] for s in score_history]
    compliance_scores = [s["compliance"] for s in score_history]
    combined_scores = [s["combined"] for s in score_history]

    fig, ax = plt.subplots()
    ax.plot(iterations, review_scores, marker="o", label="Reviewer")
    ax.plot(iterations, compliance_scores, marker="o", label="Compliance")
    ax.plot(iterations, combined_scores, marker="o", label="Combined")

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Score (0–100)")
    ax.set_title("Score History")
    ax.legend()
    ax.grid(True)

    return fig


def list_output_documents() -> Tuple[List[str], List[str], List[str]]:
    """
    Scan data/output for docx files and categorize.
    Returns filenames only (not full paths) for display.
    """
    base_dir = Path("data/output")
    if not base_dir.exists():
        return [], [], []

    csr_files = []
    review_files = []
    compliance_files = []

    for p in base_dir.rglob("*.docx"):
        name = p.name.lower()
        filename = p.name  # Just the filename, not the full path
        if "_review_v" in name or "review" in name:
            review_files.append(filename)
        elif "_compliance_v" in name or "compliance" in name:
            compliance_files.append(filename)
        else:
            csr_files.append(filename)

    return sorted(csr_files), sorted(review_files), sorted(compliance_files)


def get_full_path(filename: str) -> Optional[str]:
    """
    Given a filename, find the full path in data/output.
    """
    if not filename:
        return None
    base_dir = Path("data/output")
    for p in base_dir.rglob(filename):
        return str(p)
    return None


def export_document(filename: str):
    """
    Export/download a document given its filename.
    Returns the full path for Gradio File component.
    """
    if not filename:
        return None
    full_path = get_full_path(filename)
    if full_path and Path(full_path).exists():
        return full_path
    return None


def refresh_document_lists():
    """
    Refresh all document dropdowns with latest files from data/output.
    Returns updated choices for all dropdowns.
    """
    csr_files, review_files, compliance_files = list_output_documents()
    all_files = sorted(set(csr_files + review_files + compliance_files))
    
    return (
        gr.update(choices=csr_files, value=csr_files[0] if csr_files else None),
        gr.update(choices=review_files, value=review_files[0] if review_files else None),
        gr.update(choices=compliance_files, value=compliance_files[0] if compliance_files else None),
        gr.update(choices=all_files, value=all_files[0] if all_files else None),
        gr.update(choices=all_files, value=all_files[1] if len(all_files) > 1 else (all_files[0] if all_files else None)),
    )


def update_comparison_dropdown(doc_type: str):
    """
    Update the comparison document dropdown based on selected document type.
    """
    csr_files, review_files, compliance_files = list_output_documents()
    
    if doc_type == "CSR Versions":
        choices = csr_files
    elif doc_type == "Review Reports":
        choices = review_files
    elif doc_type == "Compliance Reports":
        choices = compliance_files
    else:
        choices = []
    
    return gr.update(choices=choices, value=choices[0] if choices else None)


# -------------------------------------------------------------------
# Document comparison helpers
# -------------------------------------------------------------------

SECTION_HEADING_PATTERN = re.compile(
    r"^\s*\d+(\.\d+)*\s+.+"  # e.g. "4. Study Population", "2.1 Inclusion Criteria"
)

# capture leading section number for ordering (e.g. "3.1.2")
SECTION_NUMBER_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)*)")


def normalize_section_title(title: str) -> str:
    """
    Normalize a section heading so that comparison is based on the
    header name only, ignoring numbering and special characters.

    Example:
      "4.1.2 Study Population!!"  ->  "study population"
    """
    # Remove leading numbering like "4.", "4.1", "4.1.2", etc.
    title = re.sub(r'^\s*\d+(\.\d+)*\s*', '', title)

    # Keep only alphanumerics and spaces; drop other special characters
    title = re.sub(r'[^A-Za-z0-9\s]+', '', title)

    # Collapse whitespace and lowercase
    return re.sub(r'\s+', ' ', title).strip().lower()


def split_into_sections(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Split text into sections based on numbered headings.

    Returns a dict keyed by a normalized section name (header text only,
    no numbering or special characters):

      {
        normalized_section_key: {
          "title": original_title_line,
          "lines": [ ... section body lines ... ]
        },
        "__UNSECTIONED__": {
          "title": "__UNSECTIONED__",
          "lines": [ ... lines before first heading ... ]
        }
      }

    Comparison will use the normalized key, so differences in numbering or
    special characters in the heading line are ignored.
    """
    lines = text.splitlines()
    sections: Dict[str, Dict[str, Any]] = {}

    current_key = "__UNSECTIONED__"
    sections[current_key] = {"title": "__UNSECTIONED__", "lines": []}

    for line in lines:
        stripped = line.strip()
        if SECTION_HEADING_PATTERN.match(stripped):
            # Create normalized key based on header *name*, not numbering/special chars
            norm_key = normalize_section_title(stripped) or "__UNNAMED_SECTION__"

            current_key = norm_key
            if current_key not in sections:
                sections[current_key] = {
                    "title": stripped,   # keep original for display
                    "lines": [],
                }
            else:
                # If we already have this section key but no title yet, set it
                if not sections[current_key].get("title"):
                    sections[current_key]["title"] = stripped
        else:
            sections[current_key]["lines"].append(line)

    # Clean up empty unsectioned
    if sections.get("__UNSECTIONED__") and not sections["__UNSECTIONED__"]["lines"]:
        sections.pop("__UNSECTIONED__", None)

    return sections


def make_html_diff_table(
    lines_a: List[str],
    lines_b: List[str],
    fromdesc: str,
    todesc: str,
    context: bool = True,
    numlines: int = 2,
) -> str:
    """Create a single HtmlDiff table for two lists of lines."""
    differ = difflib.HtmlDiff(wrapcolumn=80)
    return differ.make_table(
        lines_a,
        lines_b,
        fromdesc=fromdesc,
        todesc=todesc,
        context=context,
        numlines=numlines,
    )


def build_diff_legend() -> str:
    """Return HTML legend explaining color codes in a clear, CSR-friendly way."""
    return """
    <div style="margin-bottom: 10px; font-family: sans-serif; font-size: 14px;">
      <strong>Color Legend:</strong>

      <div style="margin-top:6px;">
        <span style="background-color:#fab1a0; padding:2px 6px;">
          Red – Removed from Document A
        </span>
        <span style="margin-left:10px;">
          (Content that was present in Document A but is missing in Document B)
        </span>
      </div>

      <div style="margin-top:6px;">
        <span style="background-color:#c8f7c5; padding:2px 6px;">
          Green – Added in Document B
        </span>
        <span style="margin-left:10px;">
          (New content introduced in Document B that was not in Document A)
        </span>
      </div>

      <div style="margin-top:6px;">
        <span style="background-color:#ffeaa7; padding:2px 6px;">
          Yellow – Modified Text
        </span>
        <span style="margin-left:10px;">
          (Text that exists in both documents but has been changed, e.g., wording or values)
        </span>
      </div>
    </div>
    """


def build_diff_style() -> str:
    """Return shared CSS for diff tables."""
    return """
    <style>
    table.diff {font-family: monospace; border: medium solid #ccc; border-collapse: collapse;}
    .diff_header {background-color: #f0f0f0; font-weight: bold;}
    .diff_next {background-color: #e0e0ff;}
    .diff_add {background-color: #c8f7c5;}   /* added: light green */
    .diff_chg {background-color: #ffeaa7;}   /* changed: light yellow */
    .diff_sub {background-color: #fab1a0;}   /* removed: light red/orange */
    td, th {padding: 2px 4px; vertical-align: top;}
    </style>
    """


def compare_documents(filename_a: str, filename_b: str, mode: str) -> str:
    """
    Compare two DOCX documents and return an HTML diff.
    Now accepts filenames and resolves full paths internally.
    """
    if not filename_a or not filename_b:
        return "<p style='color:red;'>Please select both documents to compare.</p>"

    # Resolve full paths from filenames
    path_a = get_full_path(filename_a)
    path_b = get_full_path(filename_b)
    
    if not path_a or not path_b:
        return "<p style='color:red;'>Could not find one or both documents.</p>"

    try:
        text_a = read_docx_text(path_a)
        text_b = read_docx_text(path_b)

        style = build_diff_style()
        legend = build_diff_legend()

        if mode == "Section-wise by numbered headings":
            sections_a = split_into_sections(text_a)
            sections_b = split_into_sections(text_b)

            # union of normalized section keys
            all_keys = set(sections_a.keys()) | set(sections_b.keys())
            html_parts: List[str] = [style, legend]

            if not all_keys:
                html_parts.append(
                    "<p>No numbered headings detected; falling back to full document comparison.</p>"
                )
                # fallback to line-by-line
                lines_a = text_a.splitlines()
                lines_b = text_b.splitlines()
                table = make_html_diff_table(
                    lines_a, lines_b, "Document A", "Document B", context=True, numlines=2
                )
                html_parts.append(table)
                return "".join(html_parts)

            def sort_key(key: str):
                """
                Sort sections primarily by numeric heading (e.g. 3.1 < 3.2 < 10),
                and fallback to title/key alphabetically if no number is found.
                """
                sec = sections_a.get(key) or sections_b.get(key) or {}
                title = sec.get("title") or key

                m = SECTION_NUMBER_PATTERN.match(title)
                if m:
                    # "3.1.2" -> [3, 1, 2]
                    nums = [int(p) for p in m.group(1).split(".")]
                    return (0, nums, title.lower())
                else:
                    # non-numbered sections go after numbered ones, sorted by name
                    return (1, [9999], title.lower())

            # now sorted in proper numeric order: 3.1 before 3.2, etc.
            sorted_keys = sorted(all_keys, key=sort_key)

            for key in sorted_keys:
                sec_a = sections_a.get(key, {})
                sec_b = sections_b.get(key, {})

                # Prefer the title from A, otherwise from B, otherwise use the key
                display_title = (
                    sec_a.get("title")
                    or sec_b.get("title")
                    or key
                )

                lines_a = sec_a.get("lines", [])
                lines_b = sec_b.get("lines", [])

                # If both sides are completely empty, skip to avoid blank sections
                if not lines_a and not lines_b:
                    continue

                html_parts.append(
                    f"<h3 style='font-family:sans-serif;'>{display_title}</h3>"
                )
                table = make_html_diff_table(
                    lines_a,
                    lines_b,
                    fromdesc=f"{display_title} (A)",
                    todesc=f"{display_title} (B)",
                    context=True,
                    numlines=1,
                )
                html_parts.append(table)

            return "".join(html_parts)

        else:
            # Line-by-line full document comparison
            lines_a = text_a.splitlines()
            lines_b = text_b.splitlines()
            table = make_html_diff_table(
                lines_a, lines_b, "Document A", "Document B", context=True, numlines=2
            )
            return style + legend + table

    except Exception as e:
        logger.exception("Error comparing documents")
        return f"<p style='color:red;'>Error reading documents: {e}</p>"


# -------------------------------------------------------------------
# Streaming pipeline for real-time updates (+ Langfuse info)
# -------------------------------------------------------------------

def run_full_pipeline_stream():
    """
    Run the full multi-agent pipeline as a generator.
    Yields UI updates so Live Execution Monitor shows real-time status.
    Uses configuration from config.py.
    """

    # Use values from config.py
    target_confidence = float(CONFIDENCE_THRESHOLD)
    max_iterations = int(float(MAX_ITERATIONS)) if isinstance(MAX_ITERATIONS, str) else int(MAX_ITERATIONS)

    log_lines: List[str] = []
    score_history: List[Dict[str, float]] = []
    current_status = "Starting..."
    current_iteration = 0
    reviewer_score = 0.0
    compliance_score = 0.0
    combined_score = 0.0
    latest_csr_path: Optional[str] = None

    def log(msg: str):
        logger.info(msg)
        log_lines.append(msg)

    start_time = time.time()
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # This text will show up in the Langfuse metrics box
    langfuse_info = (
        f"Run ID: {run_id}\n"
        "Use this run ID to correlate with your Langfuse trace / session.\n"
        "If you have Langfuse tracing enabled in your agents, you can link this run to the trace in the Langfuse UI."
    )

    def make_yield(status: str, progress: float, final_summary: str = ""):
        """Helper to yield the 10 UI outputs consistently."""
        log_display = "\n".join(log_lines[-20:])
        iteration_display = str(current_iteration)
        reviewer_display = f"{reviewer_score:.1f}"
        compliance_display = f"{compliance_score:.1f}"
        combined_display = f"{combined_score:.1f}"
        score_plot = _plot_score_history(score_history)

        return (
            status,
            progress,
            log_display,
            iteration_display,
            reviewer_display,
            compliance_display,
            combined_display,
            score_plot,
            final_summary,
            langfuse_info,
        )

    log(f"🚀 Starting CSR pipeline (target={target_confidence}, max_iter={max_iterations})")
    # initial state
    yield make_yield(status="Starting...", progress=0.0)

    try:
        # 1) KnowledgeAgent
        current_status = "KnowledgeAgent: extracting sections"
        log("1) Running KnowledgeAgent...")
        yield make_yield(status=current_status, progress=0.05)

        knowledge_agent = KnowledgeAgent()
        extraction = knowledge_agent.extract_sections()
        log("✅ KnowledgeAgent completed.")
        yield make_yield(status="KnowledgeAgent completed", progress=0.15)

        # 2) DocumentComposerAgent
        current_status = "DocumentComposerAgent: composing initial CSR"
        log("2) Running DocumentComposerAgent...")
        yield make_yield(status=current_status, progress=0.25)

        composer_agent = DocumentComposerAgent()
        initial_csr_path = composer_agent.compose_document(extraction)
        latest_csr_path = initial_csr_path
        log(f"✅ Initial CSR generated at: {initial_csr_path} (v0)")
        yield make_yield(status="Initial CSR generated", progress=0.35)

        # 3) Improvement loop
        reviewer_agent = ReviewerAgent()
        compliance_agent = ComplianceAgent()
        reviser_agent = ReviserAgent()

        csr_base = Path(initial_csr_path)
        csr_dir = csr_base.parent
        csr_stem = csr_base.stem

        # We'll map iteration to progress between 0.35 and 0.95
        def iteration_progress(i: int) -> float:
            if max_iterations <= 0:
                return 0.95
            return 0.35 + (0.60 * i / max_iterations)

        for iteration in range(1, max_iterations + 1):
            current_iteration = iteration
            current_status = f"Iteration {iteration}: Reviewer + Compliance"
            log(f"🔁 Starting iteration {iteration}...")
            yield make_yield(status=current_status, progress=iteration_progress(iteration) - 0.1)

            iter_csr_path = str(csr_dir / f"{csr_stem}_v{iteration}.docx")
            iter_review_path = str(csr_dir / f"{csr_stem}_review_v{iteration}.docx")
            iter_compliance_path = str(csr_dir / f"{csr_stem}_compliance_v{iteration}.docx")

            # ReviewerAgent
            log(f"🔍 Iteration {iteration}: ReviewerAgent starting...")
            yield make_yield(status=f"Iteration {iteration}: ReviewerAgent reviewing", progress=iteration_progress(iteration) - 0.08)

            review_report_path, reviewer_score = reviewer_agent.review_document(
                csr_path=latest_csr_path,
                output_path=iter_review_path,
            )
            log(f"Iteration {iteration}: Reviewer score = {reviewer_score:.1f}")
            yield make_yield(status=f"Iteration {iteration}: ReviewerAgent completed", progress=iteration_progress(iteration) - 0.05)

            # ComplianceAgent
            log(f"🧪 Iteration {iteration}: ComplianceAgent starting...")
            yield make_yield(status=f"Iteration {iteration}: ComplianceAgent checking", progress=iteration_progress(iteration) - 0.03)

            compliance_report_path, compliance_score = compliance_agent.check_regulatory_compliance(
                csr_path=latest_csr_path,
                output_path=iter_compliance_path,
            )
            log(f"Iteration {iteration}: Compliance score = {compliance_score:.1f}")
            yield make_yield(status=f"Iteration {iteration}: ComplianceAgent completed", progress=iteration_progress(iteration) - 0.01)

            # Combined score
            combined_score = (reviewer_score + compliance_score) / 2.0
            score_history.append(
                {
                    "iteration": iteration,
                    "review": reviewer_score,
                    "compliance": compliance_score,
                    "combined": combined_score,
                }
            )
            log(
                f"📊 Iteration {iteration}: Combined score = {combined_score:.1f} "
                f"(target={target_confidence})"
            )
            yield make_yield(status=f"Iteration {iteration}: Scores updated", progress=iteration_progress(iteration))

            # Check stopping criterion
            if combined_score >= target_confidence:
                log(
                    f"✅ Target confidence reached at iteration {iteration} "
                    f"with combined score {combined_score:.1f}"
                )
                break

            # ReviserAgent
            current_status = f"Iteration {iteration}: ReviserAgent revising CSR"
            log(f"✏️ Iteration {iteration}: ReviserAgent starting...")
            yield make_yield(status=current_status, progress=iteration_progress(iteration) + 0.02)

            latest_csr_path = reviser_agent.revise_document(
                csr_path=latest_csr_path,
                review_path=review_report_path,
                compliance_path=compliance_report_path,
                output_path=iter_csr_path,
            )
            log(f"Iteration {iteration}: Revised CSR saved to {latest_csr_path}")
            yield make_yield(status=f"Iteration {iteration}: ReviserAgent completed", progress=iteration_progress(iteration) + 0.05)

        elapsed = time.time() - start_time
        final_summary = (
            f"Final combined score: {combined_score:.1f} "
            f"(review={reviewer_score:.1f}, compliance={compliance_score:.1f}) "
            f"after iteration {current_iteration}. "
            f"Elapsed: {elapsed:.1f}s"
        )
        log("🎉 Pipeline completed.")
        log(final_summary)

        # Final yield
        yield make_yield(status="Done", progress=1.0, final_summary=final_summary)

    except Exception as e:
        logger.exception("Pipeline failure in Gradio run_full_pipeline_stream")
        log(f"❌ Pipeline failed: {e}")
        final_summary = f"Pipeline failed: {e}"
        # Error state
        yield make_yield(status="Error", progress=1.0, final_summary=final_summary)


# -------------------------------------------------------------------
# Preload document lists for dropdowns (auto on app start)
# -------------------------------------------------------------------

INIT_CSR_FILES, INIT_REVIEW_FILES, INIT_COMPLIANCE_FILES = list_output_documents()
INIT_ALL_FILES = sorted(set(INIT_CSR_FILES + INIT_REVIEW_FILES + INIT_COMPLIANCE_FILES))


# -------------------------------------------------------------------
# Swimlane HTML describing the pipeline visually
# -------------------------------------------------------------------

SWIMLANE_HTML = """
<style>
.swimlane-container {
  font-family: sans-serif;
  font-size: 13px;
  margin-top: 8px;
}
.swimlane-title {
  font-weight: bold;
  margin-bottom: 4px;
}
.swimlane-lane {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}
.swimlane-agent {
  width: 170px;
  font-weight: 600;
}
.swimlane-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.swimlane-step {
  border: 1px solid #cccccc;
  border-radius: 8px;
  padding: 3px 8px;
  background-color: #f9fafb;
  white-space: nowrap;
}
</style>

<div class="swimlane-container">
  <div class="swimlane-title">Pipeline Swimlane (Logical Flow of Agents & Steps)</div>

  <div class="swimlane-lane">
    <div class="swimlane-agent">Knowledge Agent</div>
    <div class="swimlane-steps">
      <div class="swimlane-step">Load clinical JSON</div>
      <div class="swimlane-step">Extract structured sections</div>
      <div class="swimlane-step">Prepare content for CSR</div>
    </div>
  </div>

  <div class="swimlane-lane">
    <div class="swimlane-agent">Document Composer Agent</div>
    <div class="swimlane-steps">
      <div class="swimlane-step">Use CSR template</div>
      <div class="swimlane-step">Draft initial CSR (v0)</div>
    </div>
  </div>

  <div class="swimlane-lane">
    <div class="swimlane-agent">Reviewer Agent</div>
    <div class="swimlane-steps">
      <div class="swimlane-step">Review current CSR version</div>
      <div class="swimlane-step">Generate review report</div>
      <div class="swimlane-step">Score quality (0–100)</div>
    </div>
  </div>

  <div class="swimlane-lane">
    <div class="swimlane-agent">Compliance Agent</div>
    <div class="swimlane-steps">
      <div class="swimlane-step">Check regulatory compliance</div>
      <div class="swimlane-step">Generate compliance report</div>
      <div class="swimlane-step">Score compliance (0–100)</div>
    </div>
  </div>

  <div class="swimlane-lane">
    <div class="swimlane-agent">Reviser Agent</div>
    <div class="swimlane-steps">
      <div class="swimlane-step">Merge review & compliance feedback</div>
      <div class="swimlane-step">Revise CSR to next version</div>
      <div class="swimlane-step">Repeat until target score reached</div>
    </div>
  </div>

  <div style="margin-top:4px; font-size: 12px; color:#555;">
    Note: The pipeline runs these steps sequentially. Reviewer and Compliance run in each iteration,
    then the Reviser updates the CSR until the combined score meets the target confidence.
  </div>
</div>
"""


# -------------------------------------------------------------------
# Gradio App Layout
# -------------------------------------------------------------------

with gr.Blocks(title="CSR Multi-Agent Assistant") as demo:
    gr.Markdown("## 📘 CSR Multi-Agent Assistant")

    with gr.Tabs():
        # -------------------------------------------------------------
        # Tab 1: Pipeline Configuration
        # -------------------------------------------------------------
        with gr.Tab("1️⃣ Pipeline Configuration"):
            gr.Markdown("### Configure and Start the Pipeline")

            with gr.Row():
                with gr.Column():
                    clinical_file = gr.File(
                        label="Clinical Data JSON",
                        file_types=[".json"],
                    )
                    save_json_btn = gr.Button("💾 Save Clinical JSON")
                    save_json_status = gr.Textbox(
                        label="Save Status",
                        interactive=False,
                        lines=2,
                    )

                with gr.Column():
                    gr.Markdown("#### Current Configuration (from .env / config.py)")
                    gr.Markdown(f"- Clinical JSON path: `{INPUT_DATA_JSON}`")
                    gr.Markdown(f"- CSR Template path: `{CSR_TEMPLATE_PATH}`")
                    gr.Markdown(f"- Sample CSR path: `{CSR_SAMPLE_REPORT_PATH}`")
                    gr.Markdown(f"- Target Confidence: `{CONFIDENCE_THRESHOLD}%`")
                    gr.Markdown(f"- Max Iterations: `{MAX_ITERATIONS}`")

            start_pipeline_btn = gr.Button("🚀 Start Pipeline", size="lg", variant="primary")

            save_json_btn.click(
                fn=save_clinical_json,
                inputs=[clinical_file],
                outputs=[save_json_status],
            )

        # -------------------------------------------------------------
        # Tab 2: Live Execution Monitor
        # -------------------------------------------------------------
        with gr.Tab("2️⃣ Live Execution Monitor"):
            gr.Markdown("### Execution Monitor (real-time updates)")
            gr.HTML(SWIMLANE_HTML)

            status_display = gr.Textbox(
                label="Current Agent Status",
                interactive=False,
            )
            progress_bar = gr.Slider(
                label="Progress",
                minimum=0,
                maximum=1,
                value=0,
                step=0.01,
                interactive=False,
            )
            iteration_display = gr.Textbox(
                label="Current Iteration",
                value="0",
                interactive=False,
            )
            log_display = gr.Textbox(
                label="Pipeline Log (Last 20 Lines)",
                lines=20,
                interactive=False,
            )

            with gr.Row():
                reviewer_score_display = gr.Textbox(
                    label="Reviewer Score",
                    value="0.0",
                    interactive=False,
                )
                compliance_score_display = gr.Textbox(
                    label="Compliance Score",
                    value="0.0",
                    interactive=False,
                )
                combined_score_display = gr.Textbox(
                    label="Combined Score",
                    value="0.0",
                    interactive=False,
                )

            score_plot = gr.Plot(label="Score History")
            final_summary_display = gr.Textbox(
                label="Final Summary",
                lines=3,
                interactive=False,
            )

            # Langfuse section
            gr.Markdown("### Langfuse Metrics")
            langfuse_metrics_box = gr.Textbox(
                label="Langfuse Metrics / Trace Info",
                lines=4,
                interactive=False,
            )

        # -------------------------------------------------------------
        # Tab 3: Results & Document Viewer
        # -------------------------------------------------------------
        with gr.Tab("3️⃣ Results & Documents"):
            gr.Markdown("### CSR Versions, Review & Compliance Reports")
            
            refresh_docs_btn = gr.Button("🔄 Refresh Document Lists", size="sm")

            with gr.Row():
                with gr.Column(scale=3):
                    csr_file_list = gr.Dropdown(
                        label="CSR Versions",
                        choices=INIT_CSR_FILES,
                        value=INIT_CSR_FILES[0] if INIT_CSR_FILES else None,
                        interactive=True,
                    )
                with gr.Column(scale=1):
                    export_csr_btn = gr.Button("📥 Export CSR", size="sm")
                    csr_download = gr.File(label="Download CSR", visible=False)
            
            with gr.Row():
                with gr.Column(scale=3):
                    review_file_list = gr.Dropdown(
                        label="Review Reports",
                        choices=INIT_REVIEW_FILES,
                        value=INIT_REVIEW_FILES[0] if INIT_REVIEW_FILES else None,
                        interactive=True,
                    )
                with gr.Column(scale=1):
                    export_review_btn = gr.Button("📥 Export Review", size="sm")
                    review_download = gr.File(label="Download Review", visible=False)
            
            with gr.Row():
                with gr.Column(scale=3):
                    compliance_file_list = gr.Dropdown(
                        label="Compliance Reports",
                        choices=INIT_COMPLIANCE_FILES,
                        value=INIT_COMPLIANCE_FILES[0] if INIT_COMPLIANCE_FILES else None,
                        interactive=True,
                    )
                with gr.Column(scale=1):
                    export_compliance_btn = gr.Button("📥 Export Compliance", size="sm")
                    compliance_download = gr.File(label="Download Compliance", visible=False)
            
            gr.Markdown("---")
            gr.Markdown("### Document Comparison")

            with gr.Row():
                with gr.Column():
                    doc_type_a = gr.Dropdown(
                        label="Document Type A",
                        choices=["CSR Versions", "Review Reports", "Compliance Reports"],
                        value="CSR Versions",
                        interactive=True,
                    )
                    doc_a_dropdown = gr.Dropdown(
                        label="Select Document A",
                        choices=INIT_CSR_FILES,
                        value=INIT_CSR_FILES[0] if INIT_CSR_FILES else None,
                        interactive=True,
                    )
                with gr.Column():
                    doc_type_b = gr.Dropdown(
                        label="Document Type B",
                        choices=["CSR Versions", "Review Reports", "Compliance Reports"],
                        value="CSR Versions",
                        interactive=True,
                    )
                    doc_b_dropdown = gr.Dropdown(
                        label="Select Document B",
                        choices=INIT_CSR_FILES,
                        value=INIT_CSR_FILES[1] if len(INIT_CSR_FILES) > 1 else (INIT_CSR_FILES[0] if INIT_CSR_FILES else None),
                        interactive=True,
                    )

            comparison_mode = gr.Radio(
                label="Comparison Mode",
                choices=[
                    "Line-by-line (full document)",
                    "Section-wise by numbered headings",
                ],
                value="Line-by-line (full document)",
            )

            compare_btn = gr.Button("🔍 Compare Side-by-Side")

            # HTML diff output with legend and tables
            compare_result_html = gr.HTML(
                label="Comparison Result (color-coded)",
            )

            

    # ----------------------------------------------------------------
    # Wiring callbacks
    # ----------------------------------------------------------------

    # Export buttons for documents
    export_csr_btn.click(
        fn=export_document,
        inputs=[csr_file_list],
        outputs=[csr_download],
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[csr_download],
    )
    
    export_review_btn.click(
        fn=export_document,
        inputs=[review_file_list],
        outputs=[review_download],
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[review_download],
    )
    
    export_compliance_btn.click(
        fn=export_document,
        inputs=[compliance_file_list],
        outputs=[compliance_download],
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[compliance_download],
    )

    # Refresh document lists button - now updates comparison dropdowns based on current type selection
    def refresh_all_docs():
        csr_files, review_files, compliance_files = list_output_documents()
        # For comparison dropdowns, use the currently selected doc type
        # This is a simplified refresh - comparison dropdowns will be updated by their type change handlers
        return (
            gr.update(choices=csr_files, value=csr_files[0] if csr_files else None),
            gr.update(choices=review_files, value=review_files[0] if review_files else None),
            gr.update(choices=compliance_files, value=compliance_files[0] if compliance_files else None),
        )
    
    refresh_docs_btn.click(
        fn=refresh_all_docs,
        inputs=[],
        outputs=[
            csr_file_list,
            review_file_list,
            compliance_file_list,
        ],
    )
    
    # Update comparison dropdowns when document type changes
    doc_type_a.change(
        fn=update_comparison_dropdown,
        inputs=[doc_type_a],
        outputs=[doc_a_dropdown],
    )
    
    doc_type_b.change(
        fn=update_comparison_dropdown,
        inputs=[doc_type_b],
        outputs=[doc_b_dropdown],
    )

    # Streaming pipeline → real-time monitor + Langfuse box
    start_pipeline_btn.click(
        fn=run_full_pipeline_stream,
        inputs=[],
        outputs=[
            status_display,
            progress_bar,
            log_display,
            iteration_display,
            reviewer_score_display,
            compliance_score_display,
            combined_score_display,
            score_plot,
            final_summary_display,
            langfuse_metrics_box,
        ],
    )

    compare_btn.click(
        fn=compare_documents,
        inputs=[doc_a_dropdown, doc_b_dropdown, comparison_mode],
        outputs=[compare_result_html],
    )

if __name__ == "__main__":
    demo.launch(share=True)
