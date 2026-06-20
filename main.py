from __future__ import annotations

import ast
import importlib
import inspect
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.requests import Request

from app.intent_extractor.extractor import extract_intent
from app.system_designer.designer import design_system
from app.schema_generator.generator import generate_schema
from app.validator.validator import validate_schema
from app.repair_engine.repair import repair_schema
from app.code_generator.generator import generate_project

APP_TITLE = "AI App Compiler"
ROOT_DIR = Path(__file__).resolve().parent
GENERATED_APP_DIR = ROOT_DIR / "generated_app"
STATE_FILE = ROOT_DIR / ".ai_app_compiler_state.json"
MAX_PREVIEW_BYTES = 160_000

BACKEND_EXTENSIONS = {".py", ".toml", ".ini", ".cfg", ".txt", ".md", ".json", ".yaml", ".yml"}
FRONTEND_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".json",
    ".md",
}
SCHEMA_MARKERS = (
    "__tablename__",
    "BaseModel",
    "Column(",
    "mapped_column(",
    "Table(",
    "CREATE TABLE",
)
LOG_EXTENSIONS = {".log", ".out", ".err"}
PIPELINE_STAGES = [
    "Intent Extraction",
    "System Design",
    "Schema Generation",
    "Validation",
    "Repair Engine",
    "Code Generation",
    "Packaging",
]


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


app = FastAPI(title=APP_TITLE)
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_generated_project() -> bool:
    return GENERATED_APP_DIR.exists() and any(path.is_file() for path in GENERATED_APP_DIR.rglob("*"))


def safe_relative(path: Path) -> str:
    return path.relative_to(GENERATED_APP_DIR).as_posix()


def collect_project_files() -> list[Path]:
    if not GENERATED_APP_DIR.exists():
        return []
    return sorted(path for path in GENERATED_APP_DIR.rglob("*") if path.is_file())


def read_text_file(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > MAX_PREVIEW_BYTES:
        head = data[:MAX_PREVIEW_BYTES].decode("utf-8", errors="replace")
        return f"{head}\n\n[File preview truncated at {MAX_PREVIEW_BYTES} bytes]"
    return data.decode("utf-8", errors="replace")


def read_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def extract_project_name(prompt: str) -> str:
    cleaned = " ".join(prompt.strip().split())
    cleaned = re.sub(r"^(build|create|generate|make|develop|design)\s+(an?|the)?\s*", "", cleaned, flags=re.I)
    cleaned = re.split(r"\s+(with|that|which|for|using|including)\s+", cleaned, maxsplit=1, flags=re.I)[0]
    cleaned = cleaned.strip(" .,:;-")
    return cleaned or prompt.strip()


def discover_backend_files() -> list[Path]:
    backend_dir = GENERATED_APP_DIR / "backend"
    if not backend_dir.exists():
        return []
    return [
        path
        for path in collect_project_files()
        if backend_dir in path.parents and path.suffix.lower() in BACKEND_EXTENSIONS
    ]


def discover_frontend_files() -> list[Path]:
    frontend_dir = GENERATED_APP_DIR / "frontend"
    if not frontend_dir.exists():
        return []
    return [
        path
        for path in collect_project_files()
        if frontend_dir in path.parents and path.suffix.lower() in FRONTEND_EXTENSIONS
    ]


def discover_schema_files() -> list[Path]:
    schema_files: list[Path] = []
    for path in discover_backend_files():
        content = read_text_file(path)
        if any(marker in content for marker in SCHEMA_MARKERS):
            schema_files.append(path)
    return schema_files


def discover_log_files() -> list[Path]:
    return [
        path
        for path in collect_project_files()
        if path.suffix.lower() in LOG_EXTENSIONS or "log" in path.name.lower()
    ]


def count_apis() -> int:
    count = 0
    pattern = re.compile(r"^\s*@(?:\w+\.)?(?:get|post|put|delete|patch|options|head)\s*\(", re.MULTILINE)
    for path in discover_backend_files():
        if path.suffix.lower() == ".py":
            count += len(pattern.findall(read_text_file(path)))
    return count


def count_tables() -> int:
    count = 0
    for path in discover_backend_files():
        if path.suffix.lower() != ".py":
            continue
        content = read_text_file(path)
        count += len(re.findall(r"__tablename__\s*=", content))
        count += len(re.findall(r"\bTable\s*\(", content))
    return count


def count_pages() -> int:
    page_extensions = {".html", ".jsx", ".tsx", ".vue", ".svelte"}
    return sum(1 for path in discover_frontend_files() if path.suffix.lower() in page_extensions)


def build_tree() -> str:
    files = collect_project_files()
    if not files:
        return ""

    root: dict[str, Any] = {}
    for file_path in files:
        current = root
        for part in file_path.relative_to(GENERATED_APP_DIR).parts:
            current = current.setdefault(part, {})

    lines = ["generated_app/"]

    def walk(node: dict[str, Any], depth: int) -> None:
        names = sorted(node)
        for index, name in enumerate(names):
            branch = "`-- " if index == len(names) - 1 else "|-- "
            lines.append(f"{'    ' * depth}{branch}{name}")
            if node[name]:
                walk(node[name], depth + 1)

    walk(root, 0)
    return "\n".join(lines)


def file_payload(path: Path) -> dict[str, str]:
    return {
        "path": safe_relative(path),
        "name": path.name,
        "language": language_for(path),
        "content": read_text_file(path),
    }


def language_for(path: Path) -> str:
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".sql": "sql",
    }.get(path.suffix.lower(), "text")


def metrics_payload() -> dict[str, int]:
    return {
        "apis": count_apis(),
        "tables": count_tables(),
        "pages": count_pages(),
        "files": len(collect_project_files()),
    }


def status_payload() -> dict[str, Any]:
    state = read_state()
    generated = has_generated_project()
    return {
        "generated": generated,
        "projectName": state.get("project_name") if generated else None,
        "prompt": state.get("prompt") if generated else None,
        "updatedAt": state.get("updated_at") if generated else None,
        "stages": [
            {
                "name": stage,
                "status": "complete" if generated else "pending",
            }
            for stage in PIPELINE_STAGES
        ],
        "metrics": metrics_payload() if generated else {"apis": 0, "tables": 0, "pages": 0, "files": 0},
    }


def combine_files(files: list[Path]) -> list[dict[str, str]]:
    return [file_payload(path) for path in files]


def results_payload() -> dict[str, Any]:
    if not has_generated_project():
        return {
            "generated": False,
            "emptyTitle": "No project generated yet",
            "emptyMessage": "Generate an application to view results",
            "tabs": {
                "schema": [],
                "backend": [],
                "frontend": [],
                "structure": "",
                "logs": [],
            },
        }

    return {
        "generated": True,
        "tabs": {
            "schema": combine_files(discover_schema_files()),
            "backend": combine_files(discover_backend_files()),
            "frontend": combine_files(discover_frontend_files()),
            "structure": build_tree(),
            "logs": combine_files(discover_log_files()),
        },
    }


def compiler_candidates() -> list[tuple[str, str]]:
    return [
        ("app.runtime.compiler", "compile_app"),
        ("app.runtime.compiler", "generate_app"),
        ("app.runtime", "compile_app"),
        ("app.runtime", "generate_app"),
        ("app.code_generator", "generate_app"),
        ("app.code_generator.generator", "generate_app"),
        ("app.compiler", "compile_app"),
        ("app.pipeline", "run_pipeline"),
        ("app.pipeline", "compile_app"),
    ]


def find_compiler() -> Callable[..., Any] | None:
    for module_name, function_name in compiler_candidates():
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        candidate = getattr(module, function_name, None)
        if callable(candidate):
            return candidate
    return None

COMPILER_LOGS = []
async def invoke_compiler(prompt: str):
    
    #Intent Extraction
    COMPILER_LOGS.clear()

    COMPILER_LOGS.append("Intent Extraction Started")
    intent = extract_intent(prompt)
    COMPILER_LOGS.append("Intent Extraction Completed")

    #System Design
    COMPILER_LOGS.append("System Design Started")
    design = design_system(intent)
    COMPILER_LOGS.append("System Design Completed")

    #schema Generation
    COMPILER_LOGS.append("Schema Generation Started")
    schema = generate_schema(design)
    COMPILER_LOGS.append("Schema Generation Completed")

    #validation
    COMPILER_LOGS.append("Validation Started")
    validation_result = validate_schema(schema)
    COMPILER_LOGS.append("Validation Completed")

    #repair
    COMPILER_LOGS.append("Repair Started")
    repaired_schema = repair_schema(
    schema,
    validation_result
    )
    COMPILER_LOGS.append("Repair Completed")

    #code generation
    COMPILER_LOGS.append("Code Generation Started")
    result = generate_project(repaired_schema)
    COMPILER_LOGS.append("Code Generation Completed")

    COMPILER_LOGS.append("Packaging Completed")

    return {
        "ran": True,
        "message": "Compiler completed.",
        "result": result
    }

def validate_python_artifacts() -> list[str]:
    errors: list[str] = []
    for path in discover_backend_files():
        if path.suffix.lower() != ".py":
            continue
        try:
            ast.parse(read_text_file(path), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{safe_relative(path)}:{exc.lineno}: {exc.msg}")
    return errors


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_title": APP_TITLE
        }
    )


@app.post("/generate")
async def generate(payload: GenerateRequest) -> dict[str, Any]:
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    compiler_result = await invoke_compiler(prompt)
    generated = has_generated_project()

    if not compiler_result["ran"] or not generated:
        return {
            "ok": False,
            "message": compiler_result["message"],
            "status": status_payload(),
            "results": results_payload(),
        }

    state = {
        "prompt": prompt,
        "project_name": extract_project_name(prompt),
        "updated_at": utc_now(),
        "compiler": compiler_result,
        "validation_errors": validate_python_artifacts(),
    }
    write_state(state)

    return {
        "ok": True,
        "message": compiler_result["message"],
        "status": status_payload(),
        "results": results_payload(),
    }


@app.get("/status")
async def status() -> dict[str, Any]:
    return status_payload()


@app.get("/results")
async def results() -> dict[str, Any]:
    return results_payload()


@app.get("/download")
async def download() -> StreamingResponse:
    files = collect_project_files()
    if not files:
        raise HTTPException(status_code=404, detail="No project generated yet.")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path("generated_app") / path.relative_to(GENERATED_APP_DIR))
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="generated_app.zip"'},
    )
@app.get("/logs")
async def logs():
    return {
        "logs": COMPILER_LOGS
    }
