from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.intent_extractor.extractor import extract_intent
from app.system_designer.designer import design_system
from app.schema_generator.generator import generate_schema
from app.repair_engine.repair import repair_schema
from app.code_generator.generator import generate_project
from app.validator.validator import validate_schema

import io
import re
import time
import zipfile
from pathlib import Path

import streamlit as st


APP_NAME = "AI App Compiler"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_APP_DIR = PROJECT_ROOT / "generated_app"


st.set_page_config(
    page_title=APP_NAME,
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --bg: #050711;
            --panel: rgba(15, 23, 42, 0.72);
            --panel-strong: rgba(17, 24, 39, 0.92);
            --line: rgba(148, 163, 184, 0.18);
            --line-strong: rgba(125, 211, 252, 0.24);
            --text: #f8fafc;
            --muted: #94a3b8;
            --soft: #cbd5e1;
            --cyan: #22d3ee;
            --blue: #60a5fa;
            --violet: #8b5cf6;
            --green: #34d399;
            --amber: #fbbf24;
            --danger: #fb7185;
            --shadow: 0 24px 80px rgba(0, 0, 0, 0.36);
            --radius: 20px;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            color: var(--text);
            background:
                radial-gradient(circle at 8% 10%, rgba(34, 211, 238, 0.16), transparent 30%),
                radial-gradient(circle at 78% 4%, rgba(139, 92, 246, 0.19), transparent 28%),
                radial-gradient(circle at 54% 92%, rgba(52, 211, 153, 0.10), transparent 28%),
                linear-gradient(135deg, #050711 0%, #080b18 48%, #020617 100%);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148, 163, 184, 0.035) 1px, transparent 1px);
            background-size: 48px 48px;
            mask-image: linear-gradient(to bottom, black, transparent 85%);
        }

        header[data-testid="stHeader"], div[data-testid="stToolbar"], footer {
            display: none;
        }

        .block-container {
            max-width: 1480px;
            padding: 1.1rem 2.2rem 3rem;
        }

        section[data-testid="stSidebar"], button[kind="header"] {
            display: none;
        }

        .topbar {
            position: sticky;
            top: 0;
            z-index: 20;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.85rem 1rem;
            margin-bottom: 1.2rem;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.62);
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 70px rgba(0, 0, 0, 0.28);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-mark {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border-radius: 12px;
            color: white;
            font-weight: 800;
            letter-spacing: -0.04em;
            background: linear-gradient(135deg, var(--cyan), var(--violet));
            box-shadow: 0 0 35px rgba(34, 211, 238, 0.35);
        }

        .brand-title {
            font-weight: 800;
            letter-spacing: -0.035em;
            line-height: 1.05;
        }

        .brand-subtitle {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }

        .status-pill, .soft-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.74);
            color: var(--soft);
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.55rem 0.8rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--green);
            box-shadow: 0 0 18px rgba(52, 211, 153, 0.9);
        }

        .settings-button {
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.55rem 0.75rem;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text);
            font-weight: 800;
        }

        .hero {
            position: relative;
            overflow: hidden;
            padding: clamp(1.4rem, 4vw, 3rem);
            border: 1px solid var(--line-strong);
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.50)),
                radial-gradient(circle at 84% 20%, rgba(34, 211, 238, 0.22), transparent 28%);
            box-shadow: var(--shadow);
        }

        .hero::after {
            content: "";
            position: absolute;
            inset: auto -20% -45% 22%;
            height: 320px;
            background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.18), rgba(139, 92, 246, 0.18), transparent);
            filter: blur(34px);
            transform: rotate(-7deg);
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            padding: 0.48rem 0.72rem;
            border: 1px solid rgba(34, 211, 238, 0.26);
            border-radius: 999px;
            color: #a5f3fc;
            background: rgba(8, 145, 178, 0.13);
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .hero h1 {
            max-width: 940px;
            margin: 0;
            font-size: clamp(2.4rem, 5vw, 5.4rem);
            line-height: 0.96;
            letter-spacing: -0.075em;
        }

        .gradient-text {
            background: linear-gradient(90deg, #fff, #a5f3fc 45%, #c4b5fd);
            -webkit-background-clip: text;
            color: transparent;
        }

        .hero p {
            max-width: 760px;
            color: var(--muted);
            font-size: clamp(1rem, 1.5vw, 1.25rem);
            margin: 1.15rem 0 0;
        }

        .prompt-shell, .glass-panel, .metric-card, .summary-card {
            border: 1px solid var(--line);
            border-radius: var(--radius);
            background: var(--panel);
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 70px rgba(0, 0, 0, 0.22);
        }

        .prompt-shell {
            padding: 1rem;
            margin-top: -1.2rem;
            position: relative;
            z-index: 2;
        }

        .prompt-label {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.7rem;
            color: var(--soft);
            font-weight: 800;
        }

        div[data-testid="stTextArea"] textarea {
            min-height: 162px !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 18px !important;
            background: rgba(2, 6, 23, 0.72) !important;
            color: #f8fafc !important;
            font-size: 1rem !important;
            line-height: 1.65 !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: rgba(34, 211, 238, 0.55) !important;
            box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.13) !important;
        }

        .stButton > button, .stDownloadButton > button {
            width: 100%;
            border: 0;
            border-radius: 15px;
            color: white;
            font-weight: 850;
            letter-spacing: -0.01em;
            padding: 0.95rem 1.1rem;
            background: linear-gradient(135deg, #06b6d4, #2563eb 48%, #7c3aed);
            box-shadow: 0 18px 44px rgba(37, 99, 235, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.22);
            transition: transform 160ms ease, filter 160ms ease, box-shadow 160ms ease;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.08);
            box-shadow: 0 24px 60px rgba(37, 99, 235, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.28);
        }

        .example-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.85rem;
        }

        .example-chip {
            border: 1px solid var(--line);
            border-radius: 13px;
            padding: 0.7rem 0.75rem;
            background: rgba(255, 255, 255, 0.045);
            color: var(--soft);
            font-size: 0.85rem;
            font-weight: 700;
        }

        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 1rem;
            margin: 2rem 0 0.85rem;
        }

        .section-title h2 {
            margin: 0;
            font-size: 1.35rem;
            letter-spacing: -0.035em;
        }

        .section-title p {
            margin: 0.25rem 0 0;
            color: var(--muted);
            font-size: 0.92rem;
        }

         .pipeline {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1rem;
            width: 100%;
            margin-top: 1rem;
        }

        .stage {
    position: relative;
    overflow: hidden;

    width: 100%;
    min-height: 220px;
    border-radius: 20px;
    padding: 1.5rem;
    background: rgba(15,23,42,.8);
    border: 1px solid rgba(148,163,184,.15);
}

        .stage.active {
            border-color: rgba(34, 211, 238, 0.65);
            box-shadow: 0 0 42px rgba(34, 211, 238, 0.13);
        }

        .stage.done {
            border-color: rgba(52, 211, 153, 0.38);
        }

        .stage.active::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(110deg, transparent, rgba(255, 255, 255, 0.09), transparent);
    animation: shimmer 1.8s linear infinite;
}

@keyframes shimmer {
    from { transform: translateX(-100%); }
    to { transform: translateX(100%); }
}

        @keyframes shimmer {
            from { transform: translateX(-100%); }
            to { transform: translateX(100%); }
        }

        .stage-index {
            display: inline-grid;
            place-items: center;
            width: 30px;
            height: 30px;
            margin-bottom: 0.8rem;
            border-radius: 10px;
            background: rgba(34, 211, 238, 0.13);
            color: #a5f3fc;
            font-weight: 850;
        }

        .stage h3 {
            margin: 0;
            font-size: 0.95rem;
            letter-spacing: -0.02em;
        }

        .stage small {
            display: block;
            color: var(--muted);
            margin-top: 0.35rem;
            font-weight: 700;
        }

        .progress-track {
            height: 5px;
            margin-top: 0.9rem;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.14);
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, var(--cyan), var(--violet));
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
        }

        .metric-card {
            padding: 1.05rem;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }

        .metric-value {
            margin-top: 0.45rem;
            font-size: 2rem;
            line-height: 1;
            font-weight: 850;
            letter-spacing: -0.055em;
        }

        .metric-note {
            color: var(--green);
            margin-top: 0.55rem;
            font-size: 0.84rem;
            font-weight: 750;
        }

        .tabs-panel {
            border: 1px solid var(--line);
            border-radius: var(--radius);
            background: rgba(2, 6, 23, 0.52);
            overflow: hidden;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            padding: 0.45rem;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: rgba(15, 23, 42, 0.74);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 12px;
            padding: 0.65rem 1rem;
            color: var(--muted);
            font-weight: 800;
        }

        .stTabs [aria-selected="true"] {
            color: white;
            background: rgba(255, 255, 255, 0.075);
        }

        div[data-testid="stCodeBlock"] {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            overflow: hidden;
        }

        div[data-testid="stCodeBlock"] pre {
            max-height: 520px;
            overflow: auto;
            font-family: 'JetBrains Mono', monospace !important;
        }

        .summary-card {
            padding: 1.2rem;
        }

        .summary-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.72rem 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }

        .summary-row:last-child {
            border-bottom: 0;
        }

        .summary-row span:first-child {
            color: var(--muted);
            font-weight: 700;
        }

        .summary-row span:last-child {
            color: var(--text);
            font-weight: 800;
            text-align: right;
        }

        .stAlert {
            border-radius: 16px;
            border: 1px solid var(--line);
            background: rgba(15, 23, 42, 0.70);
        }

        @media (max-width: 1100px) {
            .pipeline, .metrics-grid, .example-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .block-container {
                padding-inline: 1rem;
            }
        }

        @media (max-width: 680px) {
            .topbar {
                align-items: flex-start;
                flex-direction: column;
            }
            .pipeline, .metrics-grid, .example-grid {
                grid-template-columns: 1fr;
            }
            .hero h1 {
                font-size: 2.4rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def read_file(path: Path) -> str:
    if not path.exists():
        return f"{path.name} has not been generated yet."
    return path.read_text(encoding="utf-8", errors="replace")


def collect_project_files() -> list[Path]:
    if not GENERATED_APP_DIR.exists():
        return []
    return sorted(path for path in GENERATED_APP_DIR.rglob("*") if path.is_file())


def count_apis() -> int:
    routes = read_file(GENERATED_APP_DIR / "backend" / "routes.py")
    return len(re.findall(r"@router\.(get|post|put|delete|patch)\(", routes))


def count_tables() -> int:
    models = read_file(GENERATED_APP_DIR / "backend" / "models.py")
    return len(re.findall(r"__tablename__\s*=", models))


def count_pages() -> int:
    frontend_dir = GENERATED_APP_DIR / "frontend"
    return len(list(frontend_dir.glob("*.jsx"))) + len(list(frontend_dir.glob("*.tsx"))) if frontend_dir.exists() else 0


def build_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in collect_project_files():
            ROOT = Path(__file__).resolve().parent.parent
    buffer.seek(0)
    return buffer.getvalue()


def render_topbar() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="logo-mark">AI</div>
                <div>
                    <div class="brand-title">AI App Compiler</div>
                    <div class="brand-subtitle">Natural language to production-ready project structure</div>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;">
                <div class="status-pill"><span class="status-dot"></span> Online compiler ready</div>
                <div class="soft-pill">Model pipeline v1</div>
                <div class="settings-button">Settings</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">AI Engineering Platform</div>
            <h1><span class="gradient-text">Build Full-Stack Applications From Natural Language</span></h1>
            <p>Describe your idea and instantly generate production-ready software.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_prompt() -> bool:
    if "app_prompt" not in st.session_state:
        st.session_state.app_prompt = ""

    st.markdown(
        """
        <div class="prompt-shell">
            <div class="prompt-label">
                <span>Describe the software you want to generate</span>
                <span class="soft-pill">System design + schema + code + ZIP</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_area(
        "Prompt",
        key="app_prompt",
        label_visibility="collapsed",
        placeholder=(
            "Example: Build a Hospital Management System with patient registration, doctor schedules, "
            "appointments, billing, admin dashboard, REST APIs, database schema, and responsive frontend."
        ),
    )
    submitted = st.button("Generate Full-Stack Application", type="primary")
    st.markdown(
        """
            <div class="example-grid">
                <div class="example-chip">Build a Hospital Management System</div>
                <div class="example-chip">Build an E-Commerce Platform</div>
                <div class="example-chip">Build a CRM Application</div>
                <div class="example-chip">Build a Learning Management System</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return submitted


def render_pipeline(active: bool) -> None:

    stages = [
        "Intent Extraction",
        "System Design",
        "Schema Generation",
        "Repair Engine",
        "Code Generation",
        "Project Packaging",
    ]

    cols = st.columns(6)

    for i, stage in enumerate(stages):
        with cols[i]:
            if st.session_state.get("generated"):
                st.success(f"{i+1}. {stage}")
            else:
                st.info(f"{i+1}. {stage}")
    html = ['<div class="pipeline">']
    for index, label in enumerate(stages, start=1):
        progress = 100 if st.session_state.get("generated") else (66 if active and index == 1 else 0)
        klass = "done" if progress == 100 else "active" if active and index == 1 else ""
        status = "Complete" if progress == 100 else "Running" if klass == "active" else "Queued"
        html.append(
            f"""
            <div class="stage {klass}">
                <div class="stage-index">{index}</div>
                <h3>{label}</h3>
                <small>{status}</small>
                <div class="progress-track"><div class="progress-fill" style="width:{progress}%"></div></div>
            </div>
            """
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_metrics() -> None:
    metrics = [
        ("Tables Generated", count_tables(), "Relational schema ready"),
        ("APIs Generated", count_apis(), "REST endpoints detected"),
        ("Pages Generated", count_pages(), "Frontend screens available"),
        ("Files Generated", len(collect_project_files()), "Packaged project files"),
    ]
    cards = ['<div class="metrics-grid">']
    for label, value, note in metrics:
        cards.append(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-note">{note}</div>
            </div>
            """
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def project_tree() -> str:
    files = collect_project_files()
    if not files:
        return "generated_app/\n  No generated files found."

    lines = ["generated_app/"]
    for path in files:
        relative = path.relative_to(GENERATED_APP_DIR)
        indent = "  " * len(relative.parts)
        lines.append(f"{indent}{relative.name}")
    return "\n".join(lines)


def render_results() -> None:
    schema_code = "\n\n".join(
        [
            "# models.py",
            read_file(GENERATED_APP_DIR / "backend" / "models.py"),
            "# schemas.py",
            read_file(GENERATED_APP_DIR / "backend" / "schemas.py"),
        ]
    )
    backend_code = "\n\n".join(
        [
            "# main.py",
            read_file(GENERATED_APP_DIR / "backend" / "main.py"),
            "# routes.py",
            read_file(GENERATED_APP_DIR / "backend" / "routes.py"),
        ]
    )
    frontend_code = read_file(GENERATED_APP_DIR / "frontend" / "Login.jsx")
    logs = f"""Compiler run complete.
Prompt: {st.session_state.get("app_prompt") or "No prompt submitted in this session."}
Artifacts: {len(collect_project_files())} files
APIs: {count_apis()}
Tables: {count_tables()}
Pages: {count_pages()}
Package: generated_app.zip ready for download"""

    tabs = st.tabs(["Schema", "Backend", "Frontend", "Project Structure", "Logs"])
    with tabs[0]:
        st.code(schema_code, language="python")
    with tabs[1]:
        st.code(backend_code, language="python")
    with tabs[2]:
        st.code(frontend_code, language="jsx")
    with tabs[3]:
        st.code(project_tree(), language="text")
    with tabs[4]:
        st.code(logs, language="text")


def render_download_section() -> None:
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-row"><span>Project Name</span><span>Generated Application</span></div>
                <div class="summary-row"><span>Technologies</span><span>FastAPI, SQLAlchemy, React</span></div>
                <div class="summary-row"><span>Number of APIs</span><span>{count_apis()}</span></div>
                <div class="summary-row"><span>Number of Tables</span><span>{count_tables()}</span></div>
                <div class="summary-row"><span>Number of Pages</span><span>{count_pages()}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="summary-card">
                <h3 style="margin:0 0 .45rem;letter-spacing:-.035em;">Download Project ZIP</h3>
                <p style="margin:0 0 1rem;color:#94a3b8;">Export the generated source tree for local development, demos, or handoff.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download ZIP",
            data=build_zip(),
            file_name="generated_app.zip",
            mime="application/zip",
            disabled=not GENERATED_APP_DIR.exists(),
        )


def section_title(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">
            <div>
                <h2>{title}</h2>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    render_topbar()
    render_hero()

    submitted = render_prompt()

    if "generated" not in st.session_state:
        st.session_state.generated = GENERATED_APP_DIR.exists()

    active = False

    if submitted:

         active = True

         with st.spinner("Compiling full-stack application..."):

               intent = extract_intent(
                     st.session_state.app_prompt
               )

               design = design_system(intent)

               schema = generate_schema(design)

               validation_result = validate_schema(schema)

               repaired_schema = repair_schema(
                    schema,
                    validation_result
                )

               project = generate_project(
                     repaired_schema
               )

               st.session_state.generated = True

    active = False

    st.success(
                    "Generation pipeline completed. Project artifacts are ready."
           )

    section_title("Generation Pipeline", "Track each compiler stage from product intent to packaged code.")
    render_pipeline(active)

    #section_title("Dashboard Metrics", "A fast summary of what the compiler produced.")
    #render_metrics()

    section_title("Generated Results", "Explore schema, APIs, frontend code, project structure, and logs.")
    render_results()

    section_title("Download Package", "Review the generated project summary and export the ZIP.")
    render_download_section()


if __name__ == "__main__":
    main()
