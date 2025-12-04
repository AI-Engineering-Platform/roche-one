CSR Multi-Agent Assistant

Automated Clinical Study Report Generation, Review, Compliance Check & Revision

This project provides an end-to-end, multi-agent system for generating, reviewing, validating, and revising Clinical Study Reports (CSRs) using OpenAI LLMs.
It includes a structured folder layout, and several specialized AI Agents performing different steps of the CSR pipeline.

| Agent                     | Responsibility                                                 |
| ------------------------- | -------------------------------------------------------------- |
| **KnowledgeAgent**        | Extracts study insights from a clinical JSON & the CSR template|
| **DocumentComposerAgent** | Generates the first CSR draft using extracted content          |
| **ReviewerAgent**         | Evaluates the CSR vs. a reference sample CSR                   |
| **ComplianceAgent**       | Checks regulatory compliance (ICH E3-style)                    |
| **ReviserAgent**          | Produces an improved CSR based on review + compliance feedback |
