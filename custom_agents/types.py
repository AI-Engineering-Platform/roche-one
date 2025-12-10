import os
from dataclasses import dataclass
from utils.file_utils import read_docx_text, write_docx_text


@dataclass
class KnowledgeContent:
    nct_id: str
    content_by_section: dict[str, str]


@dataclass
class CsrDocument:
    filename: str
    content: str

    def __post_init__(self):
        if not self.filename.endswith(".docx"):
            raise ValueError("Filename must end with .docx")
        
        if self.content.strip() == "":
            read_docx_text(self.filename)
        else:
            write_docx_text(os.path.join("data/output/", self.filename), self.content)
