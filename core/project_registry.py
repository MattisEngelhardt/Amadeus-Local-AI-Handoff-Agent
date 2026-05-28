import json
from pathlib import Path

from amadeus.models.state import ProjectRegistryEntry, ProjectState

REGISTRY_DIR = Path.home() / ".amadeus"
REGISTRY_FILE = REGISTRY_DIR / "projects.json"


class ProjectRegistry:
    def __init__(self, registry_file: Path | None = None):
        self.registry_file = registry_file or REGISTRY_FILE

    def _load(self) -> list[ProjectRegistryEntry]:
        if not self.registry_file.exists():
            return []
        try:
            data = json.loads(self.registry_file.read_text(encoding="utf-8"))
            return [ProjectRegistryEntry.model_validate(item) for item in data]
        except Exception:
            return []

    def _save(self, entries: list[ProjectRegistryEntry]) -> None:
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        data = [entry.model_dump() for entry in entries]
        self.registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register(self, entry: ProjectRegistryEntry) -> None:
        entries = self._load()
        # Remove existing if any
        entries = [e for e in entries if e.project_name != entry.project_name]
        entries.append(entry)
        self._save(entries)

    def set_active(self, project_name: str) -> None:
        entries = self._load()
        for e in entries:
            e.is_active = e.project_name == project_name
        self._save(entries)

    def get_active(self) -> ProjectRegistryEntry | None:
        entries = self._load()
        for e in entries:
            if e.is_active:
                return e
        return None

    def list_projects(self) -> list[ProjectRegistryEntry]:
        return self._load()

    def remove(self, project_name: str) -> None:
        entries = self._load()
        entries = [e for e in entries if e.project_name != project_name]
        self._save(entries)

    def update_state(self, project_name: str, state: ProjectState) -> None:
        entries = self._load()
        for e in entries:
            if e.project_name == project_name:
                e.phase = state.phase
                e.readiness_score = state.readiness.score
                e.updated_at = state.updated_at
                break
        self._save(entries)
