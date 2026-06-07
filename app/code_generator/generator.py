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
    # DYNAMIC MODELS
    # =========================

    model_code = ""

    if "db_schema" in schema:

        tables = schema["db_schema"].get(
            "tables",
            []
        )

        for table in tables:

            class_name = table["name"].title()

            model_code += (
                f"\nclass {class_name}:\n"
            )

            columns = table.get(
                "columns",
                []
            )

            if len(columns) == 0:

                model_code += (
                    "    pass\n\n"
                )

            else:

                for column in columns:

                    field_name = column["name"]

                    model_code += (
                        f"    {field_name} = None\n"
                    )

                model_code += "\n"

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
    # REQUIREMENTS.TXT
    # =========================

    with open(
        "generated_app/requirements.txt",
        "w"
    ) as f:

        f.write(
            """fastapi
uvicorn
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

pip install -r requirements.txt

uvicorn backend.routes:router --reload
"""
        )

    return {
        "status": "success",
        "folder": "generated_app"
    }