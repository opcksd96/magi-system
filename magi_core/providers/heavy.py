import asyncio
from typing import Optional, List
from magi_core.providers.base import ModelProvider, MagiResponse
from magi_core.logic.casper import CasperEngine
from magi_core.prompts import MAGI_SYSTEM_PROMPTS, CRITIQUE_PROMPT
from magi_core.utils.logger import SessionLogger


class HeavyProvider(ModelProvider):
    """
    A Meta-Provider that implements the 3-phase Multi-Agent Debate cycle.
    Divergence -> Critique -> Convergence.
    """

    def __init__(
        self,
        advisor_providers: List[ModelProvider],  # [Melchior, Balthasar, Casper]
        judge_provider: ModelProvider,
        model_name: str = "MAGI-HEAVY-CHAIN",
        max_concurrency: int = 1,  # MAGI supports strict resource management
        logger: Optional[SessionLogger] = None,
    ):
        super().__init__()
        if len(advisor_providers) != 3:
            raise ValueError("HeavyProvider requires exactly 3 advisor providers.")

        self.melchior = advisor_providers[0]
        self.balthasar = advisor_providers[1]
        self.casper = advisor_providers[2]
        self.engine = CasperEngine(judge_provider=judge_provider)
        self.model_name = model_name
        # Semaphore to ensure only N requests process heavy chains simultaneously
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.logger = logger

    async def generate_raw(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        request_id: str = "SYSTEM",
    ) -> MagiResponse:
        """
        Executes the full 3-phase debate cycle with detailed step-based logging.
        """
        raw_response = {"phases": []}

        async def add_phase(name: str):
            raw_response["phases"].append(name)
            if self.logger:
                await self.logger.update_active_job_phase(name)

        import time
        import math
        import datetime

        start_time = time.time()

        # Helper for console steps with 5W1H telemetry
        def log_step(
            step: int, who: str, what: str, methodology: str, where: str, tools: str
        ):
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{ts}] [STEP-{step}]")
            print(f"  > WHO: {who}")
            print(f"  > WHAT: {what}")
            print(f"  > HOW: {methodology}")
            print(f"  > WHERE: {where}")
            print(f"  > WITH: {tools}")

        async with self.semaphore:
            # --- ステップ1: プロンプト受付 & 初期解析 ---
            log_step(
                1,
                who="SYSTEM (ORCHESTRATOR)",
                what="プロンプト受付 & 初期解析",
                methodology="HEURISTIC TOKEN ESTIMATION",
                where="API RECEPTION LAYER",
                tools="LILITH-ESTIMATOR",
            )

            # Simple token estimation
            est_tokens = math.ceil(len(prompt) / 2.5)
            print(f"  [METRIC] 推定トークン量: ~{est_tokens} tokens")

            est_seconds = (est_tokens * 3) / 15
            print(f"  [METRIC] 予想処理時間: {est_seconds:.1f}s")

            await add_phase("ステップ1: プロンプト解析開始")

            log_step(
                1,
                who="LLM ADVISORS (MEL/BAL/CAS)",
                what="DIVERGENCE PHASE (各員による初期分析)",
                methodology="PARALLEL ASYNC GENERATION",
                where="INDEPENDENT OLLAMA WORKERS",
                tools=f"MODEL: {self.melchior.model}",
            )

            step1_start = time.time()
            tasks = [
                self.melchior.generate(prompt, MAGI_SYSTEM_PROMPTS["MELCHIOR"]),
                self.balthasar.generate(prompt, MAGI_SYSTEM_PROMPTS["BALTHASAR"]),
                self.casper.generate(prompt, MAGI_SYSTEM_PROMPTS["CASPER"]),
            ]
            mel_1, bal_1, cas_1 = await asyncio.gather(*tasks)
            step1_end = time.time()

            print(f"  [RESULT] 解析完了 (処理時間: {step1_end - step1_start:.2f}s)")
            await add_phase("ステップ1: 解析完了")

            # --- ステップ2: オーケストレータ & 議論 ---
            log_step(
                2,
                who="MAGI ORCHESTRATOR",
                what="DEBATE PHASE (多角的議論の開始)",
                methodology="MULTI-ROUND CRITIQUE RECURSION",
                where="HEAVY CHAIN ENGINE",
                tools="MAGI_CORE V2.1",
            )

            from magi_core.utils.config import ConfigManager

            config = ConfigManager()
            max_rounds = int(config.get_setting("magi.max_debate_rounds", 1))
            debate_history = []

            current_mel, current_bal, current_cas = mel_1, bal_1, cas_1

            for round_num in range(max_rounds):
                phase_name = f"ステップ2: 議論ラウンド {round_num + 1}"
                print(f"\n  --- ROUND {round_num + 1} ---")

                await add_phase(f"{phase_name} 開始")

                debate_history.append(
                    {
                        "round": round_num,
                        "mel": current_mel.content,
                        "bal": current_bal.content,
                        "cas": current_cas.content,
                    }
                )

                personas = [
                    ("MELCHIOR", "Scientist", current_mel),
                    ("BALTHASAR", "Mother", current_bal),
                    ("CASPER", "Woman", current_cas),
                ]

                debate_tasks = []
                for i, (name, desc, own_resp) in enumerate(personas):
                    others = [p[2].content for j, p in enumerate(personas) if i != j]
                    other_text = "\n\n".join(
                        [f"ADVISOR {j+1}:\n{text}" for j, text in enumerate(others)]
                    )
                    critique_prompt = CRITIQUE_PROMPT.format(
                        persona_name=name,
                        persona_description=desc,
                        prompt=prompt,
                        own_analysis=own_resp.content,
                        other_analyses=other_text,
                    )
                    provider = [self.melchior, self.balthasar, self.casper][i]
                    debate_tasks.append(provider.generate(critique_prompt))

                log_step(
                    2,
                    who=f"REFINEMENT UNIT (R-{round_num+1})",
                    what=f"議論プロンプト送信 (Round {round_num+1})",
                    methodology="CROSS-CRITIQUE INJECTION",
                    where="DISTRIBUTED WORKER NODES",
                    tools=f"CTX SIZE: {len(current_mel.content)+len(current_bal.content)+len(current_cas.content)}",
                )

                current_mel, current_bal, current_cas = await asyncio.gather(
                    *debate_tasks
                )

                # Track current votes for state sync
                def get_vote(content: str):
                    c = content.upper()
                    if "APPROVE" in c:
                        return "APPROVE"
                    if "DENY" in c or "REJECT" in c:
                        return "DENY"
                    return None

                round_votes = {
                    "MELCHIOR": get_vote(current_mel.content),
                    "BALTHASAR": get_vote(current_bal.content),
                    "CASPER": get_vote(current_cas.content),
                }

                print(f"  [RESULT] ラウンド {round_num+1} 完了. Votes: {round_votes}")
                await add_phase(f"{phase_name} 完了")

            # --- ステップ3: 集約 & 統合 ---
            log_step(
                3,
                who="CASPER ENGINE (JUDGE)",
                what="CONVERGENCE PHASE (議論結果の集約・最終審議)",
                methodology="CONSENSUS ALGORITHM (VOTE WEIGHTING)",
                where="NERV HQ CENTRAL COMPUTE",
                tools="JUDGE MODEL",
            )

            await add_phase("ステップ3: 最終審議開始")
            decision = await self.engine.deliberate(
                current_mel, current_bal, current_cas, debate_history
            )
            await add_phase("ステップ3: 審議完了")

            log_step(
                3,
                who="SYSTEM (ORCHESTRATOR)",
                what="最終判決の確定 & 出力準備",
                methodology="JSON SCHEMA VALIDATION",
                where="OUTPUT LAYER",
                tools=f"RULING: {decision.main_ruling}",
            )

            end_time = time.time()
            total_duration = end_time - start_time

            print("\n[SUMMARY TELEMETRY]")
            print(
                f"  > TIMESTAMP: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"  > TOTAL TIME: {total_duration:.2f}s")
            print(f"  > EST TOKENS: ~{est_tokens * (1 + max_rounds)} tokens")
            print("  > STATUS: TERMINATED SUCCESSFULLY")

            # Build thinking process log for UI
            history_log = ""
            for h in debate_history:
                history_log += f"\n### ROUND {h['round']} STATE\n[MEL]: {h['mel'][:100]}...\n[BAL]: {h['bal'][:100]}...\n[CAS]: {h['cas'][:100]}...\n"

            thinking = f"### PHASE 1: DIVERGENCE\n[MEL]: {mel_1.content}\n\n### PHASE 2: DEBATE\n{history_log}\n\n### PHASE 3: CONVERGENCE\n{decision.main_ruling}"

            raw_response.update(
                {
                    "decision": decision,
                    "refined_responses_full": [current_mel, current_bal, current_cas],
                    "debate_history": debate_history,
                    "final_votes": round_votes if "round_votes" in locals() else {},
                }
            )

            return MagiResponse(
                content=f"RULING: {decision.main_ruling}\n\n{decision.reasoning}\n\nSUMMARY: {decision.summary}",
                model_name=self.model_name,
                provider_name="HeavyChain",
                thinking_process=thinking.strip(),
                raw_response=raw_response,
                execution_time=total_duration,
            )

    async def health_check(self) -> bool:
        """Checks if all underlying providers are healthy."""
        results = await asyncio.gather(
            self.melchior.health_check(),
            self.balthasar.health_check(),
            self.casper.health_check(),
            self.engine.judge.health_check(),
        )
        return all(results)
