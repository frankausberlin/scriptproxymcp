# Skill Scripts as MCP Tools - Design Proposal

## Overview

Extend SkillFolder to scan for `.sh` files within skill folders (especially in a `scripts/` subdirectory) and register those containing `#mcp@` metadata as MCP tools. This allows skills to provide executable scripts that can be used by LLMs.

## Motivation

Currently, skills are exposed as MCP resources (documentation, references). But skills often contain helper scripts that should be available as tools. This feature enables:

- Skills to provide executable bash scripts as MCP tools
- Unified discovery: both resources (SKILL.md) and tools (scripts) come from the same skill folder
- Reuse of existing `#mcp@` metadata format from ScriptFolder

## Design

### Architecture

```
SkillFolder
├── skills/
│   ├── luxus-python-stack/
│   │   ├── SKILL.md          → MCP Resource
│   │   ├── references/        → MCP Resource (files)
│   │   └── scripts/
│   │       ├── pyinit.sh      → MCP Tool (if #mcp@name exists)
│   │       └── other.sh       → MCP Tool (if #mcp@name exists)
```

### Implementation Options

#### Option A: Extend SkillFolder to collect scripts

SkillFolder already has `_collect_skill_files()`. We can add a method to:
1. Find `.sh` files in skill folder (especially `scripts/` subdirectory)
2. Parse `#mcp@` metadata using similar logic to ScriptFolder
3. Return a list of `ScriptInfo` objects per skill

**Pros:** Single scanner class handles both resources and tools
**Cons:** SkillFolder becomes more complex

#### Option B: ScriptFolder already supports this

Actually, ScriptFolder.scan() can scan ANY folder for scripts with `#mcp@` metadata. We could:
1. When scanning skills, also call ScriptFolder.scan() on each skill's `scripts/` subdirectory
2. Collect the resulting ScriptInfo objects

**Pros:** Reuse existing ScriptFolder logic, cleaner separation of concerns
**Cons:** Requires skill folders to have a `scripts/` subdirectory structure

#### Option C: Unified scanner

Create a new `SkillScanner` class that handles both resource discovery and tool discovery within skills.

**Pros:** Clean separation, doesn't modify existing classes
**Cons:** More code duplication

### Recommended: Option B

ScriptFolder already implements the script discovery logic. We can reuse it by:
1. Adding a `scripts_path` property to `SkillInfo` (optional path to scripts subfolder)
2. After scanning skills, for each skill, check if `skill.path / "scripts"` exists
3. If yes, run `ScriptFolder(skill.path / "scripts").scan()` and collect results
4. Store the resulting `ScriptInfo[]` in a new `skill_scripts` property

### Data Model Changes

#### skillfolder.py - SkillInfo extension

```python
@dataclass
class SkillInfo:
    """Metadata extracted from a skill folder containing SKILL.md."""

    name: str
    path: Path
    description: str = ""
    files: list[str] = field(default_factory=list)
    # NEW:
    scripts: list[ScriptInfo] = field(default_factory=list)  # Scripts in this skill
```

Or alternatively, store scripts separately:

```python
class SkillFolder:
    def __init__(self, path: Path | str) -> None:
        # ... existing
        self.skill_scripts: dict[str, list[ScriptInfo]] = {}  # skill_name -> scripts
```

### Server Integration

In `server.py`, after `_setup_skill_resources()`:

```python
def _setup_skill_tools(self) -> None:
    """Register skill scripts as MCP tools."""
    if not self.mcp:
        return
    
    for skill in self.skills_folder.skills:
        for script in skill.scripts:
            tool_func = create_tool_function(script)
            # Prefix tool name with skill name to avoid collisions
            tool_name = f"{skill.name}_{script.tool_name}"
            self.mcp.add_tool(
                tool_func,
                name=tool_name,
                description=f"[{skill.name}] {script.description}",
            )
            logger.info(f"Registered skill tool: {tool_name}")
```

### File Structure

```
src/scriptproxymcp/
├── scriptfolder.py     # Existing - ScriptFolder class
├── skillfolder.py      # Modified - add scripts discovery
├── datatypes.py        # Modified - optional scripts field in SkillInfo
└── server.py           # Modified - register skill scripts as tools
```

### Tool Naming Convention

To avoid name collisions between skills:
- `skillname_scriptname` (e.g., `luxus-python-stack_pyinit`)

### Discovery Path

Scripts are looked for in:
1. `<skill_folder>/scripts/` (recommended structure)
2. `<skill_folder>/` (root, fallback)

### Error Handling

- If `scripts/` doesn't exist: no tools registered for that skill (not an error)
- If a script lacks `#mcp@name` or `#mcp@description`: skip it (same as ScriptFolder)
- If a script file can't be read: skip with warning log

## Testing Strategy

1. **Unit tests for SkillFolder.scripts discovery**
   - Skill with scripts/ subfolder containing valid scripts
   - Skill with scripts/ but no #mcp@ metadata
   - Skill without scripts/ folder
   - Skill with scripts/ containing non-shell files

2. **Integration tests in server**
   - Server starts with skills folder containing script-enabled skills
   - Tools are registered with correct naming
   - Tools execute correctly

## Open Questions

1. **Should we scan recursively?** i.e., `<skill>/scripts/subdir/script.sh`?
   - Recommendation: No, only top-level `scripts/` folder

2. **Tool name collision handling?**
   - If two skills have a script with the same name
   - Solution: Prefix with skill name (already in design)

3. **File extensions?**
   - Only `.sh` files, or also `.py`, `.bash`?
   - Recommendation: Start with `.sh` only (matches current ScriptFolder behavior)
