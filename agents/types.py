from dataclasses import dataclass
from utils.docx_utils import read_docx_text, write_docx_text


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
            write_docx_text(self.filename, self.content)
