import os


def generate_project(schema):

    os.makedirs("generated_app/frontend", exist_ok=True)
    os.makedirs("generated_app/backend", exist_ok=True)

    # Frontend files
    with open(
        "generated_app/frontend/Login.jsx",
        "w"
    ) as f:
        f.write(
            """
export default function Login() {
    return <h1>Login Page</h1>;
}
"""
        )

    with open(
        "generated_app/frontend/Dashboard.jsx",
        "w"
    ) as f:
        f.write(
            """
export default function Dashboard() {
    return <h1>Dashboard Page</h1>;
}
"""
        )

    # Backend files
    entities = []

    if "db_schema" in schema:
        tables = schema["db_schema"].get("tables", [])

        for table in tables:
            entities.append(table["name"].title())

    model_code = ""

    for entity in entities:
        model_code += f"""
class {entity}:
    pass

"""

    with open(
        "generated_app/backend/models.py",
        "w"
    ) as f:
        f.write(model_code)

    with open(
        "generated_app/backend/routes.py",
        "w"
    ) as f:
        f.write(
            """
def get_contacts():
    return []
"""
        )

    return {
        "status": "success",
        "folder": "generated_app"
    }