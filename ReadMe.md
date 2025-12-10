# 📘 CSR Multi-Agent Assistant

**Automated Clinical Study Report Generation, Review, Compliance Check & Revision**

This project provides an end-to-end, multi-agent system for generating, reviewing, validating, and revising **Clinical Study Reports (CSRs)** using OpenAI LLMs.

It includes:

- A clear, modular **Python project structure**
- Multiple specialized **AI agents**, each responsible for a specific step in the CSR lifecycle
- Support for **iterative improvement** of the CSR based on review and compliance scores
- **Interactive Gradio Web Interface** with real-time monitoring and document comparison
- Optional integration with **Langfuse** for observability (via `langfuse.openai`)

---

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
Launch the interactive Gradio app with visual monitoring and document management:
```bash
python app.py
```
The app will be available at `http://localhost:7860` and will generate a public shareable link.

### Option 2: Command Line
Run the pipeline programmatically:
```bash
python main.py
```

---

## 🖥️ Gradio Web Interface Features

The Gradio app provides a comprehensive web UI with four main tabs:

### 1️⃣ **Pipeline Configuration**
- Upload clinical data JSON files
- Configure pipeline parameters:
  - Target confidence score (60-100%)
  - Maximum iterations (1-10)
  - Model selection (GPT-4, Gemini, etc.)
- Visual pipeline swimlane showing agent workflow

### 2️⃣ **Live Execution Monitor**
- **Real-time progress tracking** with status updates
- Live log streaming showing agent activities
- **Score progression chart** displaying:
  - Reviewer scores over iterations
  - Compliance scores over iterations
  - Combined confidence scores
- Current iteration counter
- Langfuse integration metrics for observability

### 3️⃣ **Results & Documents**
- Browse and download all generated documents:
  - CSR versions (v0, v1, v2, ...)
  - Review reports
  - Compliance reports
- **🔄 Refresh button** to reload document lists after pipeline completion
- **Side-by-side document comparison** with:
  - Line-by-line diff view with color coding
  - Section-wise comparison by numbered headings
  - Interactive HTML diff viewer

### 4️⃣ **Session History**
- View all previous pipeline runs
- Compare performance across sessions
- Track scores and iterations over time
- Access historical documents and reports

---

## 🧠 Agents Overview

| Agent                     | Responsibility                                                                 |
| ------------------------- | ------------------------------------------------------------------------------ |
| **KnowledgeAgent**        | Extracts study insights from a clinical JSON & the CSR template                |
| **DocumentComposerAgent** | Generates the first CSR draft using extracted content                          |
| **ReviewerAgent**         | Evaluates the CSR for completeness and produces a structured review report and generates an overall score out of 100 |
| **ComplianceAgent**       | Checks regulatory compliance (e.g., ICH E3-style expectations) and generates an overall score out of 100   |
| **ReviserAgent**          | Produces an improved CSR based on review and compliance feedback if the score is below 80% or max number of iterations is reached            |

The pipeline is:

1. **KnowledgeAgent** → extract section-wise content  
2. **DocumentComposerAgent** → generate initial CSR draft  
3. **ReviewerAgent** → completeness assessment + score  
4. **ComplianceAgent** → regulatory assessment + score  
5. **ReviserAgent** → revise CSR based on both reports  

Optionally, steps 3–5 can run in a **loop** until a target confidence score (e.g., 80%) or max iterations is reached.

---

## ⚙️ Configuration

Review `.env_example` for configuration details including:
- API keys for OpenAI/Gemini models
- Langfuse credentials for observability
- Pipeline parameters (confidence threshold, max iterations)

Copy `.env_example` to `.env` and configure your credentials:
```bash
cp .env_example .env
# Edit .env with your API keys
```

---

## 📊 Key Features

### Real-Time Monitoring
- Live progress updates during pipeline execution
- Streaming logs showing agent activities
- Interactive score visualization with Plotly charts

### Document Management
- Automatic versioning of CSR drafts (v0, v1, v2, ...)
- Organized output structure in `data/output/`
- One-click refresh to reload latest documents

### Document Comparison
- Visual side-by-side diff viewer
- Section-wise comparison mode for structured analysis
- Color-coded additions, deletions, and changes

### Session History
- Persistent tracking of all pipeline runs
- Historical score and iteration data
- Quick access to previous documents and reports

---

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env_example .env
# Edit .env with your API keys
```

---

## 📁 Project Structure

```
agent-bootcamp/
├── app.py                      # Gradio web interface
├── main.py                     # CLI pipeline runner
├── config.py                   # Configuration settings
├── agents/                     # AI agent implementations
│   ├── knowledge_agent.py
│   ├── document_composer_agent.py
│   ├── reviewer_agent.py
│   ├── compliance_agent.py
│   └── reviser_agent.py
├── data/
│   ├── input/                  # Clinical data JSON files
│   └── output/                 # Generated CSRs and reports
├── utils/                      # Utility functions
└── requirements.txt
```

---

## 🎯 Usage Examples

### Using the Web Interface
1. Start the Gradio app: `python app.py`
2. Upload your clinical data JSON or use the default
3. Configure target score and max iterations
4. Click "Start Pipeline" and monitor progress
5. View results and download documents
6. Use the comparison tool to see improvements

### Using the Command Line
```bash
python main.py
```
Results will be saved to `data/output/` with versioned filenames.

---

## 📈 Output Files

Generated files follow this naming convention:
- `generated_csr_v0.docx` - Initial CSR draft
- `generated_csr_v1.docx` - First revision
- `generated_csr_review_v1.docx` - Review report for v1
- `generated_csr_compliance_v1.docx` - Compliance report for v1

---

## 🔧 Troubleshooting

**Port already in use (Gradio app):**
```bash
lsof -ti:7860 | xargs kill -9
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**API key errors:**
Ensure your `.env` file has valid API keys for OpenAI/Gemini.


- [GRADIO_README.md](GRADIO_README.md) - Detailed Gradio interface documentation
- `.env_example` - Configuration template with all available options