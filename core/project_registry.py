import json
from pathlib import Path

from amadeus.models.state import ProjectRegistryEntry, ProjectState, utc_now_iso

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
            if e.is_active and not e.is_archived:
                return e
        return None

    def get_by_name(self, project_name: str) -> ProjectRegistryEntry | None:
        entries = self._load()
        for e in entries:
            if e.project_name == project_name:
                return e
        return None

    def list_projects(self, include_archived: bool = False) -> list[ProjectRegistryEntry]:
        entries = self._load()
        if include_archived:
            return entries
        return [e for e in entries if not e.is_archived]

    def remove(self, project_name: str) -> None:
        entries = self._load()
        entries = [e for e in entries if e.project_name != project_name]
        self._save(entries)

    def archive(self, project_name: str) -> bool:
        entries = self._load()
        found = False
        for e in entries:
            if e.project_name == project_name:
                e.is_archived = True
                e.is_active = False
                e.updated_at = utc_now_iso()
                found = True
                break
        if found:
            self._save(entries)
        return found

    def find_similar_names(self, name: str) -> list[str]:
        entries = self._load()
        normalized = name.lower().replace("-", "").replace("_", "").replace(" ", "")
        similar = []
        for e in entries:
            existing = e.project_name.lower().replace("-", "").replace("_", "").replace(" ", "")
            if existing == normalized and e.project_name != name:
                similar.append(e.project_name)
            elif normalized in existing or existing in normalized:
                similar.append(e.project_name)
        return similar

    def update_state(self, project_name: str, state: ProjectState) -> None:
        entries = self._load()
        for e in entries:
            if e.project_name == project_name:
                e.phase = state.phase
                e.readiness_score = state.readiness.score
                e.input_count = len(state.raw_inputs)
                e.updated_at = state.updated_at
                break
        self._save(entries)
