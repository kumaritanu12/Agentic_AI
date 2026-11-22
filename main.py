
from pathlib import Path
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END

from parseagent import parser_chain


# ==========================================
# 1. DEFINE GRAPH STATE
# ==========================================

class ParserState(TypedDict):

    email_name: str
    email_body: str

    extraction: Optional[dict]
    validation_status: Optional[str]
    error: Optional[str]


# ==========================================
# 2. PARSER AGENT NODE
# ==========================================

def parse_email(state: ParserState):

    print("\n[Parser Agent] Extracting Lot ID...")

    try:

        result = parser_chain.invoke({
            "email_body": state["email_body"]
        })

        extraction = result.model_dump()

        print("[Parser Agent] Extraction completed")

        return {
            "extraction": extraction,
            "error": None
        }

    except Exception as e:

        print("[Parser Agent] Error:", str(e))

        return {
            "extraction": None,
            "error": str(e)
        }
#3: ATTACHMENT PROCESSING NODE NEWLY ADDED
def attachment_processing_node(state: ParserState):

    attachments = state["attachments"]

    if not attachments:
        print("No attachments found for this email.")
        return {"attachment_content": ""}

    all_content = []

    for attachment in attachments:

        file_path = attachment["file_path"]

        print(f"\nProcessing attachment: {file_path}")

        response = attachment_agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Read this attachment: {file_path}"
                }
            ]
        })

        result = response["messages"][-1].content

        print("\nExtracted attachment content:")
        print(result)

        all_content.append(result)

    return {
        "attachment_content": "\n".join(all_content)
    }
# ==========================================
# 4. VALIDATION NODE
# ==========================================

def validate_extraction(state: ParserState):

    print("[Validation Node] Validating extracted data...")

    extraction = state.get("extraction")

    if not extraction:

        return {
            "validation_status": "MISSING"
        }

    lot_id = extraction.get("lot_id")
    foundry_id = extraction.get("foundry_lot_id")
    candidates = extraction.get("lot_id_candidates") or []
    evidence = extraction.get("evidence") or ""

    # Check whether primary Lot ID is missing
    if not lot_id:

        if candidates:
            status = "AMBIGUOUS"
        else:
            status = "MISSING"

    # Verify evidence supports extracted Lot ID
    elif lot_id not in evidence:

        status = "REVIEW"

    elif foundry_id and foundry_id not in evidence:

        status = "REVIEW"

    else:
        status = "VALID"

    print(f"[Validation Node] Status: {status}")

    return {
        "validation_status": status
    }


# ==========================================
# 5. CONDITIONAL ROUTING
# ==========================================

def route_result(state: ParserState):

    status = state.get("validation_status")

    if status == "VALID":
        return "accepted"

    elif status == "AMBIGUOUS" or status == "REVIEW":
        return "human_review"

    else:
        return "exception"


# ==========================================
# 6. RESULT NODES
# ==========================================

def accepted_node(state: ParserState):

    print("[Accepted] Lot ID extraction accepted")

    return {}


def human_review_node(state: ParserState):

    print("[Human Review] Manual verification required")

    return {}


def exception_node(state: ParserState):

    print("[Exception] Lot ID missing or parsing failed")

    return {}


# ==========================================
# 7. BUILD LANGGRAPH
# ==========================================

workflow = StateGraph(ParserState)

workflow.add_node("parse_email", parse_email)
workflow.add_node("attachment_processing", attachment_processing_node)
workflow.add_node("validate_extraction", validate_extraction)

workflow.add_node("accepted", accepted_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("exception", exception_node)

workflow.add_edge(START, "parse_email")

workflow.add_edge("parse_email", "validate_extraction")

workflow.add_conditional_edges(
    "validate_extraction",
    route_result,
    {
        "accepted": "accepted",
        "human_review": "human_review",
        "exception": "exception"
    }
)

workflow.add_edge("accepted", END)
workflow.add_edge("human_review", END)
workflow.add_edge("exception", END)

app = workflow.compile()


# ==========================================
# 8. BATCH EMAIL PROCESSING
# ==========================================

sample_folder = Path("/Users/tanu/Test_folder/sample_mailbody")

email_files = sorted(sample_folder.glob("*.txt"))

print("\n===================================")
print("SEMTECH PARSER AGENT")
print("===================================")

print(f"Total sample emails: {len(email_files)}")


for email_file in email_files:

    print("\n\n===================================")
    print("EMAIL:", email_file.name)
    print("===================================")

    email_body = email_file.read_text(
        encoding="utf-8"
    )

    initial_state = {
        "email_name": email_file.name,
        "email_body": email_body,
        "extraction": None,
        "validation_status": None,
        "error": None
    }

    result = app.invoke(initial_state)

    print("\nEXTRACTION RESULT:")
    print(result["extraction"])

    print("\nFINAL STATUS:")
    print(result["validation_status"])

    if result["error"]:
        print("\nERROR:", result["error"])


print("\n===================================")
print("BATCH PROCESSING COMPLETED")
print("===================================")


