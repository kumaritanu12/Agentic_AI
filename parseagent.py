
from typing import Optional
from pydantic import BaseModel, Field

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from openpyxl import load_workbook
from docx import Document
from langchain_core.tools import tool
from langchain.agents import create_agent

# 1. Define structured output
class LotExtraction(BaseModel):

    lot_id: Optional[str] = Field(
        description="Primary customer or production lot ID"
    )

    foundry_lot_id: Optional[str] = Field(
        description="Foundry lot ID, if available"
    )

    lot_id_candidates: list[str] = Field(
        default_factory=list,
        description="Other plausible lot ID candidates"
    )

    evidence: str = Field(
        description="Exact supporting text from the email"
    )

    confidence: float = Field(
        description="Self-reported confidence between 0 and 1"
    )

from langchain_core.tools import tool
from openpyxl import load_workbook
from docx import Document

@tool
def read_excel(file_path: str) -> str:
    """Read and return the first five rows of an Excel file."""

    workbook = load_workbook(file_path, data_only=True)
    result = []

    for sheet in workbook.worksheets:
        result.append(f"Sheet: {sheet.title}")

        for row in sheet.iter_rows(
            min_row=1,
            max_row=5,
            values_only=True
        ):
            result.append(str(row))

    workbook.close()
    return "\n".join(result)


@tool
def read_word(file_path: str) -> str:
    """Read and return the first five paragraphs of a Word document."""

    document = Document(file_path)

    paragraphs = [
        p.text for p in document.paragraphs if p.text.strip()
    ]

    return "\n".join(paragraphs[:5])

llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0
)

attachment_tools = [read_excel, read_word]

attachment_agent = create_agent(
    model=llm,
    tools=attachment_tools,
    system_prompt="""
    You are an email attachment processing agent.

    Identify the attachment file type from its file path.

    - For XLSX files, call read_excel.
    - For DOCX files, call read_word.

    Always use the appropriate tool.
    Return the extracted content clearly.
    Do not invent file contents.
    """
)


# 2. Initialize Ollama LLM
llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0
)


# 3. Initialize output parser
parser = PydanticOutputParser(
    pydantic_object=LotExtraction
)


# 4. Define extraction prompt
prompt = PromptTemplate(
    template="""
You are a semiconductor OSAT email parsing assistant.

Extract lot information from the email.

Rules:
1. Extract the primary customer or production Lot ID.
2. Extract Foundry Lot ID separately.
3. Preserve exact ID formatting.
4. Do not confuse wafer IDs, die IDs, or test run IDs with Lot IDs.
5. If multiple plausible primary lot IDs exist and
   no clear primary ID is identifiable, set lot_id to null
   and list the candidates.
6. If the email explicitly identifies the primary lot,
   extract it even if other IDs are present.
7. If no Lot ID exists, return null.
8. Never invent identifiers.
9. Include exact supporting text in evidence.
10. Do not include foundry IDs as primary lot candidates.

Email:
{email_body}

{format_instructions}
""",
    input_variables=["email_body"],
    partial_variables={
        "format_instructions": parser.get_format_instructions()
    }
)


# 5. Create LangChain pipeline
parser_chain = prompt | llm | parser
