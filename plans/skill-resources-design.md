# Skill Resources Design Proposal

## Overview

This document outlines the design for exposing skill folders (subfolders containing `SKILL.md`) as MCP resources.

## URI Structure

```
skills://                          → List all available skills
skills://<skill_name>/             → Metadata endpoint for a skill
skills://<skill_name>/SKILL.md     → Main SKILL.md file
skills://<skill_name>/<subpath>   → Any reference files (references/, scripts/, etc.)
```

## Example with Luxus-Python-Stack Skill

| URI | Content |
|-----|---------|
| `skills://` | List: `["luxus-python-stack"]` |
| `skills://luxus-python-stack/` | Metadata: `{name, description, path}` |
| `skills://luxus-python-stack/SKILL.md` | Full SKILL.md content |
| `skills://luxus-python-stack/references/luxus-python-stack.md` | Reference file |

## Proposed Implementation

### 1. New Datatype (`datatypes.py`)

```python
@dataclass
class SkillInfo:
    """Metadata for a skill."""
    name: str              # Folder name = skill name
    path: Path             # Path to skill folder
    description: str       # First line/summary from SKILL.md
    files: list[str]       # All files in skill (for resource listing)
```

### 2. New Scanner Class (`skillfolder.py`)

```python
class SkillFolder:
    """Scans a folder for subfolders containing SKILL.md files."""
    
    def __init__(self, path: Path | str):
        self.path = path if isinstance(path, Path) else Path(path)
        self.skills: list[SkillInfo] = []
    
    def scan(self) -> None:
        """Finds subfolders with SKILL.md inside."""
        for item in self.path.iterdir():
            if not item.is_dir():
                continue
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                self.skills.append(self._parse_skill(item))
```

### 3. Resource Provider Integration (`server.py`)

```python
def setup_skill_resources(self) -> None:
    """Registers skill resources with the MCP server."""
    
    @self.mcp.resource("skills://")
    def list_skills() -> list[str]:
        """Returns all available skill names."""
        return [s.name for s in self.skills]
    
    @self.mcp.resource("skills://{skill_name}/")
    def get_skill_info(skill_name: str) -> dict:
        """Returns metadata for a specific skill."""
        skill = self._find_skill(skill_name)
        return {"name": skill.name, "description": skill.description}
    
    @self.mcp.resource("skills://{skill_name}/**")
    def get_skill_file(skill_name: str, path: str) -> str:
        """Returns content of a skill file."""
        full_path = self._resolve_skill_file(skill_name, path)
        return Path(full_path).read_text()
```

## Open Questions for Feedback

1. **URI Schema**: Changed to `skills://` (plural, more consistent with collection semantics).

2. **Recursive Files**: Should all files in skill folder be accessible, or only specific ones (SKILL.md, references/, scripts/)?

3. **Metadata Schema**: Is `name` + `description` + `files` list sufficient, or need additional fields?

4. **Separate Folder vs. Integration**: Should there be a separate `--skills-folder` parameter, or should skills live alongside scripts?
