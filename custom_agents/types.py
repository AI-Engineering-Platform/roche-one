import os
from dataclasses import dataclass
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("CustomAgentsTypes")

@dataclass
class KnowledgeContent:
    nct_id: str
    content_by_section: dict[str, str]


@dataclass
class CsrDocument:
    nct_id: str
    markdown: str
    version: int = 0

    def __post_init__(self):
        logger.info("Created CsrDocument instance")
        
        if self.markdown.strip() == "":
            raise ValueError("Content cannot be empty")

        logger.info(f"   Writing CSR document to file system ({self.filename})")
        write_docx_text(os.path.join("data/output/", self.filename), self.markdown)

    @property
    def filename(self):
        return f"CSR_{self.nct_id}_v{self.version}.docx"


@dataclass
class SectionContent:
    score: int
    rationale: str
    gaps: str


@dataclass
class ReviewerContent:
    overall_score: int
    section_content: dict[str, SectionContent]


@dataclass
class SupervisorContent:
    initial_csr_document: CsrDocument
    reviewer_report: ReviewerContent
    compliance_report: ReviewerContent
    final_csr_document: CsrDocument
    initial_score: int
    final_score: int
    iterations: int
