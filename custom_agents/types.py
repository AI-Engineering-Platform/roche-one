import os
from utils.file_utils import write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("CustomAgentsTypes")

from pydantic import BaseModel, Field, model_validator


class KnowledgeContent(BaseModel):
    nct_id: str = Field(description="The NCT ID from the clinical study data")
    content_by_section: dict[str, str] = Field(
        description="Dictionary mapping section names to their extracted content"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "nct_id": "NCT00000001",
                "content_by_section": {
                    "1. Introduction": "Study background...",
                    "2. Objectives": "Primary and secondary objectives..."
                }
            }
        }


class CsrDocument(BaseModel):
    nct_id: str = Field(description="The NCT ID of the clinical study")
    markdown: str = Field(description="The CSR content in markdown format")
    version: int = Field(default=0, description="Version number of the CSR")
    
    @model_validator(mode='after')
    def write_to_file(self):
        logger.info("Created CsrDocument instance")
        
        if self.markdown.strip() == "":
            raise ValueError("Content cannot be empty")

        logger.info(f"   Writing CSR document to file system ({self.filename})")
        write_docx_text(os.path.join("data/output/", self.filename), self.markdown)

    @property
    def filename(self):
        return f"CSR_{self.nct_id}_v{self.version}.docx"


class SectionContent(BaseModel):
    score: int = Field(description="Compliance score for this section")
    rationale: str = Field(description="Rationale for the score")
    gaps: str = Field(description="Identified gaps in this section")


class ReviewerContent(BaseModel):
    overall_score: int = Field(description="Overall review score")
    section_content: dict[str, SectionContent] = Field(
        description="Review scores and feedback for each section"
    )


class SupervisorContent(BaseModel):
    initial_csr_document: CsrDocument = Field(description="Initial generated CSR document")
    reviewer_report: ReviewerContent = Field(description="Reviewer's assessment report")
    compliance_report: ReviewerContent = Field(description="Compliance assessment report")
    final_csr_document: CsrDocument = Field(description="Final revised CSR document")
    initial_score: int = Field(description="Initial document score")
    final_score: int = Field(description="Final document score")
    iterations: int = Field(description="Number of revision iterations performed")
