import os
from textwrap import dedent


def _class_name(name):
    return name.title().replace("_", "")


def _schema_name(name):
    return name.rstrip("s").title().replace("_", "")


def _route_function_name(method, path):
    name = (
        method
        + "_"
        + path.replace("/", "_")
              .replace("-", "_")
              .replace(":", "")
              .replace("{", "")
              .replace("}", "")
              .strip("_")
    )
    return name or f"{method}_root"


def generate_project(schema):
    os.makedirs("generated_app/frontend", exist_ok=True)
    os.makedirs("generated_app/backend", exist_ok=True)

    page_schema = schema.get("ui_schema", {}).get("pages", [])

    for page in page_schema:
        page_name = page["name"].replace(" ", "").replace("-", "")
        file_path = f"generated_app/frontend/{page_name}.jsx"

        fields = []
        page_title = page["name"].lower()

        if "login" in page_title:
            fields = ["username", "password"]
        elif "contact" in page_title:
            fields = ["contact_name", "contact_email"]

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
import {{ useEffect, useState }} from "react";
import axios from "axios";

export default function {page_name}() {{
    const [data, setData] = useState([]);

    useEffect(() => {{
        axios
            .get("http://127.0.0.1:8000/{page_name.lower()}")
            .then((response) => {{
                setData(response.data);
            }})
            .catch((error) => {{
                console.log(error);
            }});
    }}, []);

    return (
        <div>
            <h1>{page["name"]}</h1>

            <pre>
                {{JSON.stringify(data, null, 2)}}
            </pre>

{form_fields}

            <button>
                Submit
            </button>
        </div>
    );
}}
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(component_code)

    model_code = dedent("""
        from sqlalchemy import (
            Column,
            String,
            Integer,
            ForeignKey
        )

        from sqlalchemy.orm import declarative_base, relationship

        Base = declarative_base()
    """).lstrip()

    tables = schema.get("db_schema", {}).get("tables", [])

    for table in tables:
        class_name = _class_name(table["name"])
        table_name = table["name"].lower()

        model_code += f"""

class {class_name}(Base):
    __tablename__ = "{table_name}"
"""

        columns = table.get("columns", [])

        if not columns:
            model_code += "    pass\n"
            continue

        first_column = True
        for column in columns:
                field_name = column["name"]
                if first_column:
                    model_code += (
                         f"    {field_name} = Column(Integer, primary_key=True, index=True)\n"
                    )

                    first_column = False

                elif (
                     field_name.endswith("_id")
                     or field_name.endswith("Id")
                 ):

                        if field_name.endswith("_id"):

                             referenced_table = (
                                    field_name.replace("_id", "")
                                    + "s"
                            )

                        else:
                            referenced_table = (
                                 field_name.replace("Id", "")
                                .lower()
                                + "s"
                            )

                        model_code += (
                             f'    {field_name} = Column(Integer, ForeignKey("{referenced_table}.id"))\n'
                        )

                else:

                    model_code += (
                        f'    {field_name} = Column(String)\n'
                    )

    
    with open("generated_app/backend/models.py", "w", encoding="utf-8") as f:
        f.write(model_code)

    schema_code = "from pydantic import BaseModel\n\n"

    for table in tables:
        class_name = _schema_name(table["name"])
        schema_code += f"\nclass {class_name}Create(BaseModel):\n"

        fields_written = 0
        for column in table.get("columns", []):
            field_name = column["name"]
            if field_name == "id":
                continue
            schema_code += f"    {field_name}: str\n"
            fields_written += 1

        if fields_written == 0:
            schema_code += "    pass\n"

    with open("generated_app/backend/schemas.py", "w", encoding="utf-8") as f:
        f.write(schema_code)

    route_code = dedent("""
        from fastapi import APIRouter, Depends
        from sqlalchemy.orm import Session

        from database import get_db
        from models import *
        from schemas import *
        from auth import create_access_token

        router = APIRouter()
    """).lstrip()
    route_code += """

@router.post("/login")
def login():

    token = create_access_token(
        {"sub": "admin"}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

"""

    endpoints = schema.get("api_schema", {}).get("endpoints", [])

    for table in tables:
        table_name = table["name"].lower()
        singular = table_name.rstrip("s")
        model_name = _class_name(table["name"])
        schema_name = _schema_name(table["name"])

        route_code += f"""

@router.post("/{table_name}")
def create_{singular}(
    data: {schema_name}Create,
    db: Session = Depends(get_db)
):
    obj = {model_name}(**data.dict())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


@router.get("/{table_name}")
def list_{table_name}(
    db: Session = Depends(get_db)
):
    return db.query({model_name}).all()


@router.put("/{table_name}/{{id}}")
def update_{singular}(
    id: int,
    data: {schema_name}Create,
    db: Session = Depends(get_db)
):
    obj = db.query({model_name}).filter({model_name}.id == id).first()

    if not obj:
        return {{
            "error": "Record not found"
        }}

    for key, value in data.dict().items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)

    return obj


@router.delete("/{table_name}/{{id}}")
def delete_{singular}(
    id: int,
    db: Session = Depends(get_db)
):
    obj = db.query({model_name}).filter({model_name}.id == id).first()

    if not obj:
        return {{
            "error": "Record not found"
        }}

    db.delete(obj)
    db.commit()

    return {{
        "status": "deleted",
        "id": id
    }}
"""

    with open("generated_app/backend/routes.py", "w", encoding="utf-8") as f:
        f.write(route_code)

    main_code = dedent("""
        from fastapi import FastAPI
        from routes import router
        from models import Base
        from database import engine

        Base.metadata.create_all(bind=engine)

        app = FastAPI(
            title="Generated API"
        )

        app.include_router(router)

        @app.get("/")
        def root():
            return {
                "message": "Generated API Running"
            }
    """).lstrip()

    with open("generated_app/backend/main.py", "w", encoding="utf-8") as f:
        f.write(main_code)



    backend_requirements = """fastapi
uvicorn
sqlalchemy
pydantic
python-jose
passlib[bcrypt]
python-multipart
"""

    with open("generated_app/backend/requirements.txt", "w", encoding="utf-8") as f:
        f.write(backend_requirements)

    with open("generated_app/requirements.txt", "w", encoding="utf-8") as f:
        f.write(
    """fastapi
uvicorn
sqlalchemy
pydantic
python-jose
passlib[bcrypt]
python-multipart
"""
)

    readme = dedent("""
        # Generated Application

        This project was generated automatically by AI App Compiler.

        ## Run Backend

        cd backend

        pip install -r requirements.txt

        uvicorn main:app --reload
    """).lstrip()

    with open("generated_app/README.md", "w", encoding="utf-8") as f:
        f.write(readme)
        
        return {
        "status": "success",
        "folder": "generated_app"
    }