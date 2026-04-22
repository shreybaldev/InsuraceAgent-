import json
import re

from loguru import logger

from insurance_rag.config import get_db, get_openai_client
from insurance_rag.db import get_user_policies
from insurance_rag.prompts import QA_SYSTEM_PROMPT, POLICY_SCORE_PROMPT, GENERAL_INSURANCE_FAQ

POLICY_SCORE_PATTERN = re.compile(
    r"\b(policy\s*(?:health\s*)?score|rate\s*my\s*(?:insurance\s*)?policy|"
    r"grade\s*my\s*(?:insurance\s*)?policy|score\s*my\s*(?:insurance\s*)?policy|"
    r"policy\s*rating|policy\s*grade|"
    r"how\s*good\s*is\s*my\s*(?:insurance\s*)?policy|"
    r"evaluate\s*my\s*(?:insurance\s*)?policy|policy\s*review|"
    r"check\s*my\s*(?:insurance\s*)?policy\s*(?:health\s*)?score)\b",
    re.IGNORECASE,
)


def _is_policy_score_intent(query: str) -> bool:
    """Detect if the user is asking for a policy score/grade."""
    return bool(POLICY_SCORE_PATTERN.search(query))


async def _answer_policy_score(user_doc: dict, user_id: str) -> dict:
    """Grade the user's policy using structured_content metrics."""
    structured_metrics = []
    policy_statuses = []

    for policy in user_doc["policies"]:
        structured_block = policy.get("structured_content", {})
        content_block = policy.get("content", {})
        policy_statuses.append({
            "policy_name": policy["policy_name"],
            "content_status": content_block.get("status"),
            "structured_content_status": structured_block.get("status"),
        })

        if structured_block.get("data"):
            structured_metrics.append({
                "policy_name": policy["policy_name"],
                "metrics": structured_block["data"],
            })

    if not structured_metrics:
        still_extracting = any(
            s.get("structured_content_status") == "in_progress" for s in policy_statuses
        )
        if still_extracting:
            return {
                "answer": "Your policy is still being analyzed. Please try again shortly.",
                "source_pages": [],
                "processing_status": policy_statuses,
            }
        return {
            "answer": "Structured policy data is not available yet. Please upload a policy document first.",
            "source_pages": [],
            "processing_status": policy_statuses,
        }

    structured_content_str = json.dumps(structured_metrics, indent=2)

    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": POLICY_SCORE_PROMPT.format(structured_content=structured_content_str),
            },
            {"role": "user", "content": "Score and grade my insurance policy."},
        ],
        max_tokens=2048,
    )

    answer = response.choices[0].message.content.strip()

    logger.info(f"Policy score generated for user {user_id}")

    return {
        "answer": answer,
        "source_pages": [],
        "processing_status": policy_statuses,
    }


async def answer_question(user_id: str, query: str) -> dict:
    """Answer a user's insurance question using extracted policy page content via GPT-4o-mini."""
    db = get_db()

    logger.info(f"QA query received for user {user_id}")

    user_doc = await get_user_policies(db, user_id)
    if not user_doc or not user_doc.get("policies"):
        logger.warning(f"No policies found for user {user_id}")
        return {
            "answer": "No insurance document found for this user. Please upload a PDF first.",
            "source_pages": [],
            "processing_status": None,
        }

    # Check for policy score intent
    if _is_policy_score_intent(query):
        logger.info(f"Policy score intent detected for user {user_id}")
        return await _answer_policy_score(user_doc, user_id)

    # Build context from all policies' page content
    all_pages = []
    policy_statuses = []
    for policy in user_doc["policies"]:
        content_block = policy.get("content", {})
        policy_statuses.append({
            "policy_name": policy["policy_name"],
            "content_status": content_block.get("status"),
            "structured_content_status": policy.get("structured_content", {}).get("status"),
        })
        if content_block.get("data"):
            for page in content_block["data"]:
                all_pages.append(page)

    if not all_pages:
        logger.info(f"No pages available yet for user {user_id}, documents still processing")
        return {
            "answer": "Document is being processed. Please try again shortly.",
            "source_pages": [],
            "processing_status": policy_statuses,
        }

    still_processing = any(
        s.get("content_status") == "in_progress" for s in policy_statuses
    )

    if still_processing:
        logger.info(f"Answering with partial data for user {user_id}: {len(all_pages)} page(s) available so far")
    else:
        logger.info(f"Answering with full data for user {user_id}: {len(all_pages)} page(s)")

    context = "\n\n".join(
        f"--- Page {p['page_number']} ---\n{p['text']}" for p in all_pages
    )

    # Build FAQ context for fallback
    faq_context = "\n\n".join(
        f"Q: {key.replace('_', ' ').title()}\nA: {entry['answer']}"
        for key, entry in GENERAL_INSURANCE_FAQ.items()
    )

    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": QA_SYSTEM_PROMPT.format(context=context, faq_context=faq_context)},
            {"role": "user", "content": query},
        ],
        max_tokens=2048,
    )

    raw_answer = response.choices[0].message.content.strip()

    # Parse source pages cited by the LLM
    source_pages_match = re.search(r"SOURCE_PAGES:\s*\[([^\]]*)\]", raw_answer)
    if source_pages_match:
        try:
            source_pages = [int(x.strip()) for x in source_pages_match.group(1).split(",") if x.strip()]
        except ValueError:
            source_pages = [p["page_number"] for p in all_pages]
        # Remove the SOURCE_PAGES line from the user-facing answer
        answer = re.sub(r"\n*SOURCE_PAGES:\s*\[[^\]]*\]", "", raw_answer).strip()
    else:
        source_pages = [p["page_number"] for p in all_pages]
        answer = raw_answer

    if still_processing:
        total_pages = sum(
            policy.get("content", {}).get("total_pages", 0)
            for policy in user_doc["policies"]
        )
        pages_extracted = len(all_pages)
        progress = f" ({pages_extracted}/{total_pages} pages extracted)" if total_pages else ""
        answer = (
            answer
            + f"\n\n**Note: Document is still being processed{progress}. "
            "The answer above is based on pages extracted so far.**"
        )

    logger.info(f"QA response generated for user {user_id}, source pages: {source_pages}")

    return {
        "answer": answer,
        "source_pages": source_pages,
        "processing_status": policy_statuses,
    }
