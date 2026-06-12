import os


def generate_project(schema):

    os.makedirs("generated_app/frontend", exist_ok=True)
    os.makedirs("generated_app/backend", exist_ok=True)

    # =========================
    # DYNAMIC REACT PAGES
    # =========================

    page_schema = (
        schema.get("ui_schema", {})
        .get("pages", [])
    )

    for page in page_schema:

        page_name = (
            page["name"]
            .replace(" ", "")
            .replace("-", "")
        )

        file_path = (
            f"generated_app/frontend/{page_name}.jsx"
        )

        fields = []

        page_title = page["name"].lower()

        if "login" in page_title:

            fields = [
                "username",
                "password"
            ]

        elif "contact" in page_title:

            fields = [
                "contact_name",
                "contact_email"
            ]

        form_fields = ""

        for field in fields:

            form_fields += f"""
            <div>
                <label>{field}</label>
                <input
                    type="text"
                    placeholder="{field}"
                />
            </div>
"""

        component_code = f"""
export default function {page_name}() {{
    return (
        <div>
            <h1>{page['name']}</h1>

{form_fields}

            <button>
                Submit
            </button>
        </div>
    );
}}
"""

        with open(file_path, "w") as f:
            f.write(component_code)
    # =========================
    # SQLALCHEMY MODELS
    # =========================

    model_code = """
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

"""

    if "db_schema" in schema:

        tables = schema["db_schema"].get(
            "tables",
            []
        )

        for table in tables:

            class_name = table["name"].title()

            table_name = table["name"].lower()

            model_code += f"""

class {class_name}(Base):

    __tablename__ = "{table_name}"

"""

            columns = table.get(
                "columns",
                []
            )

            if len(columns) == 0:

                model_code += (
                    "    pass\n"
                )

            else:

                first_column = True

                for column in columns:

                    field_name = column["name"]

                    if first_column:

                        model_code += (
                            f'    {field_name} = Column(String, primary_key=True)\n'
                        )

                        first_column = False

                    else:

                        model_code += (
                            f'    {field_name} = Column(String)\n'
                        )

    with open(
        "generated_app/backend/models.py",
        "w"
    ) as f:

        f.write(model_code)

    # =========================
    # FASTAPI ROUTES
    # =========================

    route_code = """
from fastapi import APIRouter

router = APIRouter()

"""

    if "api_schema" in schema:

        endpoints = schema["api_schema"].get(
            "endpoints",
            []
        )

        for endpoint in endpoints:

            method = endpoint.get(
                "method",
                "GET"
            ).lower()

            path = endpoint.get(
                "path",
                "/"
            )

            function_name = (
                method
                + "_"
                + path.replace("/", "_")
                      .replace("-", "_")
                      .replace(":", "")
                      .replace("{", "")
                      .replace("}", "")
                      .strip("_")
            )

            route_code += f"""

@router.{method}("{path}")
def {function_name}():
    return {{
        "endpoint": "{path}",
        "method": "{method.upper()}",
        "status": "success"
    }}
"""

    with open(
        "generated_app/backend/routes.py",
        "w"
    ) as f:
        f.write(route_code)

    # =========================
    # MAIN.PY
    # =========================

    main_code = '''
from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Generated API"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Generated API Running"
    }
'''

    with open(
        "generated_app/backend/main.py",
        "w"
    ) as f:
        f.write(main_code)

        # =========================
    # DATABASE.PY
    # =========================

    database_code = '''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
'''
    with open(
        "generated_app/backend/database.py",
        "w"
    ) as f:
        f.write(database_code)

       # =========================
    # BACKEND REQUIREMENTS
    # =========================

    backend_requirements = """
fastapi
uvicorn
sqlalchemy
"""

    with open(
        "generated_app/backend/requirements.txt",
        "w"
    ) as f:
        f.write(
            backend_requirements.strip()
        )
        
    with open(
    "generated_app/requirements.txt",
    "w"
     ) as f:

       f.write(
        """fastapi
uvicorn
sqlalchemy
"""
    )

    # =========================
    # README.MD
    # =========================

    with open(
        "generated_app/README.md",
        "w"
    ) as f:

        f.write(
            """# Generated Application

This project was generated automatically by AI App Compiler.

## Run Backend

cd backend

pip install -r requirements.txt

uvicorn main:app --reload
"""
        )

    return {
        "status": "success",
        "folder": "generated_app"
    }