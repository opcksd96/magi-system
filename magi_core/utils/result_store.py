import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Optional


class ResultStore:
    """
    Handles persistence of MAGI adjudication results.
    Saves full JSON for system use and plain text for human audits.
    """

    def __init__(self, base_dir: str = "data/results"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_result(self, case_id: str, result_data: dict, prompt: str = ""):
        """Saves the result to disk in both JSON and TXT formats."""
        timestamp = datetime.now().isoformat()

        # Ensure Case ID is filesystem safe
        safe_id = "".join([c for c in case_id if c.isalnum() or c in ("-", "_")])

        # 1. Save Full JSON
        json_path = os.path.join(self.base_dir, f"{safe_id}.json")
        save_data = {
            "id": safe_id,
            "timestamp": timestamp,
            "prompt": prompt,
            "result": result_data,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        # 2. Save Human-Readable Text Summary
        txt_path = os.path.join(self.base_dir, f"{safe_id}.txt")
        ruling = result_data.get("ruling", "UNKNOWN")
        reasoning = result_data.get("reasoning", "")
        summary = result_data.get("summary", "")  # Phase 4 field

        text_content = f"""MAGI SYSTEM ADJUDICATION RECORD
CASE ID: {safe_id}
DATE: {timestamp}

PROMPT:
{prompt}

RULING: {ruling}

SUMMARY:
{summary}

REASONING:
{reasoning}

---
ADVISOR VOTES:
"""
        for adv in result_data.get("advisors", []):
            text_content += (
                f"- {adv.get('name')}: {adv.get('vote')} \n  \"{adv.get('opinion')}\"\n"
            )

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        return safe_id

    def load_result(self, case_id: str) -> Optional[dict]:
        """Loads the full JSON result for a given case ID."""
        json_path = os.path.join(self.base_dir, f"{case_id}.json")
        if not os.path.exists(json_path):
            return None

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading result {case_id}: {e}")
            return None

    def list_results(self, limit: int = 20) -> List[Dict]:
        """Lists recent results (metadata only)."""
        files = glob.glob(os.path.join(self.base_dir, "*.json"))
        files.sort(key=os.path.getmtime, reverse=True)

        results = []
        for fpath in files[:limit]:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(
                        {
                            "id": data.get("id"),
                            "timestamp": data.get("timestamp"),
                            "prompt": data.get("prompt"),
                            "ruling": data.get("result", {}).get("ruling"),
                        }
                    )
            except:
                continue
        return results
