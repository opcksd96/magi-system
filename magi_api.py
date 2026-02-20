from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import uuid
from magi_core.providers.ollama_provider import OllamaProvider
from magi_core.providers.heavy import HeavyProvider
from magi_core.utils.config import ConfigManager
from magi_core.utils.logger import SessionLogger
from magi_core.utils.result_store import ResultStore
from magi_core.utils.mime_router import MimeRouter

app = FastAPI(title="MAGI SYSTEM API")

# Initialize global management utilities
config = ConfigManager()
logger = SessionLogger()
result_store = ResultStore()
mime_router = MimeRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    prompt: str
    model: str = "lfm2.5-thinking:latest"


class AdvisorResponse(BaseModel):
    content: str


class MagiResponseModel(BaseModel):
    ruling: str
    reasoning: str
    thinking: str
    report_markdown: str = ""
    advisors: List[dict]  # Changed from str to dict to hold stats
    status_phases: List[str] = []
    telemetry: dict = {}


# --- PROVIDER INITIALIZATION ---
# Each advisor and the judge (Supervising Officer) are separate instances.
# This ensures independent reasoning and avoids 'dual-role' confusion.


def _make_provider(role: str) -> OllamaProvider:
    """Build an OllamaProvider from models.toml or fall back to config.yaml defaults."""
    m = config.models.get("models", {}).get(role, {})
    return OllamaProvider(
        model=m.get(
            "model", config.get_setting("magi.model", "lfm2.5-thinking:latest")
        ),
        base_url=m.get(
            "base_url", config.get_setting("magi.base_url", "http://localhost:11434")
        ),
        provider_name=m.get("id", role.upper()),
    )


# 4 independent souls
melchior_prov = _make_provider("melchior")
balthasar_prov = _make_provider("balthasar")
casper_prov = _make_provider("casper")
supervisor_prov = _make_provider("judge")  # The Supervising Officer

heavy = HeavyProvider(
    advisor_providers=[melchior_prov, balthasar_prov, casper_prov],
    judge_provider=supervisor_prov,
    max_concurrency=3,  # Increased to allow true parallel processing
    logger=logger,
)


@app.post("/judge", response_model=MagiResponseModel)
async def judge_query(query: Query):
    try:
        request_id = str(uuid.uuid4())[:8]  # Short ID for readability
        # Register job as active
        await logger.register_active_job(query.prompt, request_id)

        response = await heavy.generate(query.prompt, request_id=request_id)
        # We could update phases inside heavy.py if we pass the logger down,
        # but for now we update it upon completion to clear.

        # Parse the ruling from the content "RULING: [DECISION]\n\n[REASONING]"
        lines = response.content.split("\n\n", 1)
        ruling = lines[0].replace("RULING: ", "").strip()
        reasoning = lines[1] if len(lines) > 1 else ""

        # Prepare detailed advisor info for the UI
        advisor_stats = []
        total_tokens = 0

        # Map index → MAGI persona names (order matches HeavyProvider advisor_providers=[mel,bal,cas])
        PERSONA_NAMES = ["MELCHIOR-1", "BALTHASAR-2", "CASPER-3"]
        full_refined = response.raw_response.get("refined_responses_full", [])

        for idx, r in enumerate(full_refined):
            advisor_content = r.content or ""
            # Priority: Use explicit metadata vote if available, else parse from content
            final_votes = response.raw_response.get("final_votes", {})
            name = PERSONA_NAMES[idx]
            persona_base_name = name.split("-")[0]  # e.g., MELCHIOR

            meta_vote = final_votes.get(persona_base_name)

            if meta_vote:
                advisor_vote = meta_vote
            elif "APPROVE" in advisor_content.upper():
                advisor_vote = "APPROVE"
            elif (
                "DENY" in advisor_content.upper() or "REJECT" in advisor_content.upper()
            ):
                advisor_vote = "DENY"
            else:
                advisor_vote = ruling  # fallback to overall ruling

            # Trim opinion for UI (200 chars)
            opinion_text = advisor_content[:200].strip()
            if len(advisor_content) > 200:
                opinion_text += "…"

            advisor_stats.append(
                {
                    "name": name,
                    "model": r.model_name or "Unknown",
                    "tokens": (
                        r.token_usage.get("total_tokens", 0) if r.token_usage else 0
                    ),
                    "time": r.execution_time,
                    "vote": advisor_vote,
                    "opinion": opinion_text,
                }
            )
            if r.token_usage:
                total_tokens += r.token_usage.get("total_tokens", 0)

        result = MagiResponseModel(
            ruling=ruling,
            reasoning=reasoning,
            thinking=response.thinking_process or "",
            report_markdown=(
                response.raw_response.get("decision").report_markdown
                if response.raw_response.get("decision")
                else ""
            ),
            advisors=advisor_stats,
            status_phases=response.raw_response.get("phases", []),
            telemetry={
                "total_tokens": total_tokens,
                "total_time": response.execution_time,
                "judge_model": response.model_name,
            },
        )

        # 1. 永続化（ResultStore）
        saved_id = result_store.save_result(
            case_id=f"MAGI-{request_id}",
            result_data={
                "ruling": ruling,
                "reasoning": reasoning,
                "summary": (
                    response.raw_response.get("decision").summary
                    if response.raw_response.get("decision")
                    else ""
                ),
                "advisors": advisor_stats,
                "telemetry": result.telemetry,
            },
            prompt=query.prompt,
        )
        print(f"  [STORE] Result saved as {saved_id}")

        # 2. ログ記録 & アクティブジョブのクリア
        await logger.log_judgement(query.prompt, result.dict())
        await logger.clear_active_job()

        print("\n[MAGI] 処理終了")
        return result
    except Exception as e:
        import traceback

        traceback.print_exc()
        await logger.clear_active_job()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results")
async def list_results(limit: int = 20):
    """保存された最近の決議結果一覧を取得します。"""
    return result_store.list_results(limit=limit)


@app.get("/results/{case_id}")
async def get_result(case_id: str):
    """特定のケースIDの詳細を読み込みます。"""
    res = result_store.load_result(case_id)
    if not res:
        raise HTTPException(status_code=404, detail="Case ID not found")
    return res


@app.post("/upload")
async def upload_file(file_path: str):
    """
    ファイルをアップロード（モック）し、MimeRouterで内容を解釈します。
    """
    try:
        content = mime_router.route(file_path)
        return {"status": "success", "mime_result": str(content)[:200]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/active-job")
async def get_active_job():
    job = await logger.get_active_job()
    if job:
        return job
    return {"status": "idle"}


@app.get("/recent")
async def get_recent():
    return await logger.get_recent_activity()


@app.get("/health")
async def health_check():
    return {"status": "optimal", "version": "2.0.4-LILITH"}


@app.get("/ping")
async def ping_advisors():
    """
    アドバイザーへの導通確認を行います。UIはこれを受けてブリッジをアクティブにします。
    """
    import asyncio

    try:
        is_alive = await asyncio.wait_for(melchior_prov.health_check(), timeout=3.0)
    except (asyncio.TimeoutError, Exception):
        is_alive = False

    advisors_status = [
        {"name": "melchior", "online": is_alive},
        {"name": "balthasar", "online": is_alive},
        {"name": "casper", "online": is_alive},
    ]
    return {
        "status": "online" if is_alive else "offline",
        "advisors": advisors_status,
    }


@app.get("/config")
async def get_config():
    return config.settings


@app.post("/config")
async def update_config(new_settings: dict):
    config.settings.update(new_settings)
    await config.save_settings()
    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
