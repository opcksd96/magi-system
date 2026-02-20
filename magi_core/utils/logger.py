import os
import json
import datetime
import asyncio
from typing import List, Dict, Optional


class SessionLogger:
    """Handles session-based logging and recent activity tracking."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(
            self.log_dir, f"session_{self.session_id}.jsonl"
        )
        self.activity_file = os.path.join(self.log_dir, "recent_activity.json")
        self.active_job_file = os.path.join(self.log_dir, "active_job.json")

    async def register_active_job(self, prompt: str, request_id: str):
        """Registers a new active job."""
        job = {
            "request_id": request_id,
            "prompt": prompt,
            "status": "judging",
            "phase": "PROMPT_RECEIVED",
            "timestamp": datetime.datetime.now().isoformat(),
        }
        await asyncio.to_thread(self._save_active_job, job)

    async def update_active_job_phase(self, phase: str):
        """Updates the phase of the currently active job."""
        job = await self.get_active_job()
        if job:
            job["phase"] = phase
            await asyncio.to_thread(self._save_active_job, job)

    async def clear_active_job(self):
        """Clears the active job record."""
        if os.path.exists(self.active_job_file):
            await asyncio.to_thread(os.remove, self.active_job_file)

    async def get_active_job(self) -> Optional[Dict]:
        """Retrieves the currently active job if it exists."""
        return await asyncio.to_thread(self._load_active_job)

    def _save_active_job(self, job: Dict):
        with open(self.active_job_file, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=2)

    def _load_active_job(self) -> Optional[Dict]:
        if os.path.exists(self.active_job_file):
            try:
                with open(self.active_job_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    async def log_judgement(self, prompt: str, result: Dict):
        """Logs a single judgement request and its result asynchronously."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "prompt": prompt,
            "ruling": result.get("ruling"),
            "telemetry": result.get("telemetry"),
            "advisors": result.get("advisors"),
        }

        # Offload blocking I/O to a thread
        await asyncio.to_thread(self._sync_log_judgement, entry)

    def _sync_log_judgement(self, entry: Dict):
        """Internal synchronous helper for file I/O."""
        # Append to session file
        with open(self.current_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Update recent activity
        activities = []
        if os.path.exists(self.activity_file):
            try:
                with open(self.activity_file, "r", encoding="utf-8") as f:
                    activities = json.load(f)
            except (json.JSONDecodeError, IOError):
                activities = []

        activities.insert(0, entry)
        activities = activities[:10]

        with open(self.activity_file, "w", encoding="utf-8") as f:
            json.dump(activities, f, ensure_ascii=False, indent=2)

    async def get_recent_activity(self) -> List[Dict]:
        """Returns the list of recent judgements asynchronously."""
        return await asyncio.to_thread(self._sync_get_recent_activity)

    def _sync_get_recent_activity(self) -> List[Dict]:
        """Internal synchronous helper for reading activity."""
        if os.path.exists(self.activity_file):
            try:
                with open(self.activity_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
