from typing import List, Optional
from dataclasses import dataclass, field
from magi_core.providers.base import ModelProvider, MagiResponse


@dataclass
class MagiDecision:
    decision: str  # "APPROVE", "DENY", "CONDITIONAL"
    reasoning: str
    confidence_score: int
    main_ruling: str
    appendices: List[str]
    report_markdown: str = ""
    summary: str = ""  # Phase 4: natural-language summary of the full debate path


class CasperEngine:
    """
    The Consensus Engine (Casper).
    Aggregates responses from Melchior, Balthasar, and Casper (Personas),
    and uses a 'Judge' model to determine the final ruling.
    """

    def __init__(self, judge_provider: ModelProvider):
        self.judge = judge_provider

    async def deliberate(
        self,
        melchior_response: MagiResponse,
        balthasar_response: MagiResponse,
        casper_response: MagiResponse,
        debate_history: Optional[List[dict]] = None,
    ) -> MagiDecision:

        # Build optional debate history context
        history_block = ""
        if debate_history:
            rounds_text = []
            for entry in debate_history:
                rounds_text.append(
                    f"--- Round {entry['round']} ---\n"
                    f"[MELCHIOR]: {entry['mel']}\n"
                    f"[BALTHASAR]: {entry['bal']}\n"
                    f"[CASPER]: {entry['cas']}"
                )
            history_block = "\n\nDEBATE HISTORY (for context):\n" + "\n\n".join(
                rounds_text
            )

        # Construct the "Court Record" for the Judge (Supreme Court Style)
        prompt = f"""
        You are the Supreme Judge of the MAGI System. 
        Three advisors (The Magi) have provided their opinions on a matter.
        
        [MELCHIOR - The Scientist]
        {melchior_response.content}
        
        [BALTHASAR - The Mother]
        {balthasar_response.content}
        
        [CASPER - The Woman]
        {casper_response.content}
        {history_block}
        Based on these opinions, provide a final ruling.
        You MUST follow the Supreme Court of Japan (最高裁判所) format exactly:

        DECISION: [APPROVE | DENY | CONDITIONAL]
        CONFIDENCE: [0-100]

        REPORT_MARKDOWN:
        # 結 論（主 文）
        [A concise decision statement]

        # 理 由
        [Detailed explanation of why this decision was reached, citing the advisors' logic, ethics, and pragmatism]

        # 付帯決議（反対意見）
        [If there were dissenting or supplementary views among the advisors, summarize them here. If none, state "None."]

        # 参照情報
        [List relevant codes, data files, or technical standards referenced during the analysis]

        RULING: [A concise one-line summary for the UI]
        REASONING: [Brief summary for logs]
        SUMMARY: [2-3 sentence human-readable explanation of what the debate covered and why this conclusion was reached]
        APPENDIX: [Any conditions, one per line starting with -]
        """

        judgement = await self.judge.generate(prompt)
        parsed = self._parse_judgement(judgement.content)
        return parsed

    def _parse_judgement(self, content: str) -> MagiDecision:
        # Simple parsing logic (robustness improvements needed later)
        lines = content.strip().split("\n")
        decision = "UNKNOWN"
        confidence = 0
        ruling = ""
        reasoning = ""
        summary = ""
        report_markdown = ""
        appendices = []

        current_section = None

        for line in lines:
            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = int(line.split(":", 1)[1].strip())
                except ValueError:
                    confidence = 0
            elif line.startswith("RULING:"):
                ruling = line.split(":", 1)[1].strip()
            elif line.startswith("REASONING:"):
                current_section = "REASONING"
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("SUMMARY:"):
                current_section = "SUMMARY"
                summary = line.split(":", 1)[1].strip()
            elif line.startswith("REPORT_MARKDOWN:"):
                current_section = "REPORT_MARKDOWN"
            elif line.startswith("APPENDIX:"):
                current_section = "APPENDIX"
            elif line.strip().startswith("-") and current_section == "APPENDIX":
                appendices.append(line.strip()[1:].strip())
            elif current_section == "REASONING":
                reasoning += " " + line.strip()
            elif current_section == "SUMMARY":
                summary += " " + line.strip()
            elif current_section == "REPORT_MARKDOWN":
                report_markdown += line + "\n"

        return MagiDecision(
            decision=decision,
            reasoning=reasoning,
            confidence_score=confidence,
            main_ruling=ruling,
            appendices=appendices,
            report_markdown=report_markdown.strip(),
            summary=summary.strip(),
        )
