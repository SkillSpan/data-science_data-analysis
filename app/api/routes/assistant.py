import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.assistant.config import settings
from app.assistant.prompt import FALLBACK_REPLY, SYSTEM_PROMPT, SYSTEM_PROMPT_VERSION, build_user_prompt
from app.assistant.providers import generate_reply
from app.assistant.rag.retrieval import Retriever
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/assistant", tags=["Assistant"])

_retriever: Retriever | None = None


def _retriever_for_request() -> Retriever | None:
    global _retriever
    if not settings.retrieval_configured:
        return None
    if _retriever is None:
        _retriever = Retriever.from_settings()
    return _retriever


def _looks_arabic(text: str) -> bool:
    return any("\u0600" <= char <= "\u06ff" for char in text)


@router.post("/chat", response_model=AssistantChatResponse, summary="Ask the bounded SkillSpan assistant")
async def assistant_chat(payload: AssistantChatRequest, request: Request) -> AssistantChatResponse:
    request_id = getattr(request.state, "request_id", "unknown")

    if payload.context:
        # Laravel is the source of truth for learner-specific state. When it
        # supplies an approved snapshot, use that snapshot directly and do not
        # mix it with documentation retrieval.
        context = payload.context
        sources = ["laravel_context"]
    else:
        retriever = _retriever_for_request()
        if retriever is None or not retriever.available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "assistant_retrieval_unavailable",
                    "message": "Assistant knowledge retrieval is unavailable.",
                },
            )

        hits = retriever.retrieve(payload.message)
        if not hits:
            reply = (
                "\u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0643\u0627\u0641\u064a\u0629 \u0641\u064a \u0642\u0627\u0639\u062f\u0629 \u0645\u0639\u0631\u0641\u0629 SkillSpan \u0627\u0644\u0645\u0639\u062a\u0645\u062f\u0629 \u0644\u0644\u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 \u0627\u0644\u0633\u0624\u0627\u0644."
                if payload.locale == "ar" or _looks_arabic(payload.message)
                else "I do not have enough information in the approved SkillSpan knowledge base to answer that question."
            )
            return AssistantChatResponse(
                status="insufficient_context",
                reply=reply,
                grounded=False,
                sources=[],
                provider_used=None,
                prompt_version=SYSTEM_PROMPT_VERSION,
                request_id=request_id,
            )

        context = "\n\n".join(hit.chunk.text for hit in hits)
        sources = sorted({hit.chunk.source for hit in hits})

    user_prompt = build_user_prompt(payload.message, context)
    if payload.intent:
        user_prompt = f"Approved assistant intent: {payload.intent}\n\n{user_prompt}"

    reply, provider_used = await generate_reply(SYSTEM_PROMPT, user_prompt)

    if reply is None or provider_used is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "assistant_provider_unavailable",
                "message": FALLBACK_REPLY,
            },
        )

    logger.info(
        "Assistant answered request_id=%s provider=%s sources=%s",
        request_id,
        provider_used,
        sources,
    )
    return AssistantChatResponse(
        status="answered",
        reply=reply,
        grounded=True,
        sources=sources,
        provider_used=provider_used,
        prompt_version=SYSTEM_PROMPT_VERSION,
        request_id=request_id,
    )
