# 📘 CSR Multi-Agent Assistant

**Automated Clinical Study Report Generation, Review, Compliance Check & Revision**

This project provides an end-to-end, multi-agent system for generating, reviewing, validating, and revising **Clinical Study Reports (CSRs)** using OpenAI LLMs.

It includes:

- A clear, modular **Python project structure**
- Multiple specialized **AI agents**, each responsible for a specific step in the CSR lifecycle
- Support for **iterative improvement** of the CSR based on review and compliance scores
- Optional integration with **Langfuse** for observability (via `langfuse.openai`)

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
Review .env_example for config details