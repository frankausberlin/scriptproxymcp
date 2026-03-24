# Architecture Fix: Unified Folder Scanning

## Neue Architektur

### Grundprinzipien

1. **Folder-Name = MCP-Server-Name** - Einfach und direkt
2. **`mcpproxy.md` ist Pflicht** - Enthält Server-Beschreibung
3. **Rekursives `.sh` Scannen** - Keine `scripts/` Konvention mehr
4. **`.prompt` Dateien** - Standardkonforme MCP Prompts
5. **Skills in Unterordnern** - Erkannt durch `SKILL.md`

### Ablauf

```
mcpserver/
├── mcpproxy.md              # Server-Beschreibung (Pflicht!)
├── script1.sh               # Tool
├── subfolder/
│   ├── script2.sh           # Tool
│   └── SKILL.md            # Skill → Resource
└── myprompt.prompt          # Prompt
```

## Komponenten

### 1. Server-Config (`mcpproxy.md`)

```markdown
# Arithmetic MCP Server

This server provides basic arithmetic operations.
```

- **Kein spezielles Marker** nötig
- **Erste Zeile** = Server-Name (aus Folder-Name)
- **Inhalt** = Server-Beschreibung

### 2. Script-Scanning (rekursiv)

- Findet alle `*.sh` Dateien im Folder
- Parst `#mcp@name` und `#mcp@description` für Tools
- Optional: `#mcp@param` für Parameter

### 3. Skill-Scanning

- Unterordner mit `SKILL.md` werden als Skills erkannt
- `SKILL.md` → Resource `skills://<skill_name>/SKILL.md`
- `scripts/` Unterordner → Tools mit Prefix `<skill_name>_`

### 4. Prompt-Scanning

- `.prompt` Dateien werden als Prompts registriert
- Format: JSON mit `name`, `description`, optional `arguments`
- Intern generierter Prompt für Skills

## Implementierung

### server.py

```python
class MCPScriptProxy:
    def __init__(self, folder: str):
        self.folder_path = Path(folder)
        self.server_name = self.folder_path.name
        self.server_description = self._read_mcpproxy_md()
        
    def scan(self):
        # 1. Prüfe mcpproxy.md existiert
        # 2. Scanne alle *.sh rekursiv → Tools
        # 3. Scanne Unterordner mit SKILL.md → Resources + intern Prompt
        # 4. Scanne *.prompt → Prompts
```

### datatypes.py

```python
@dataclass
class ServerInfo:
    name: str
    description: str
    folder: Path

@dataclass  
class ToolInfo:
    name: str
    path: Path
    params: list[dict]
    description: str

@dataclass
class PromptInfo:
    name: str
    description: str
    template: str  # or JSON for arguments
```

## Demos

### demo/arithmeticmcp/

```
demo/arithmeticmcp/
├── mcpproxy.md
├── add.sh
├── subtract.sh
├── multiply.sh
├── divide.sh
└── power.sh
```

### demo/skill_luxuspythonstack/

```
demo/skill_luxuspythonstack/
├── mcpproxy.md
├── SKILL.md
├── scripts/
│   └── pyinit.sh
└── references/
    ├── daily-commands.md
    └── luxus-python-stack.md
```

## To-Do

- [ ] 1. server.py komplett umbauen
- [ ] 2. mcpproxy.md als Pflichtdatei
- [ ] 3. Rekursives .sh Scannen
- [ ] 4. .prompt Dateien als Prompts
- [ ] 5. Skill-Prompt generierung intern
- [ ] 6. Tests anpassen
- [ ] 7. Demos anpassen
- [ ] 8. README aktualisieren
