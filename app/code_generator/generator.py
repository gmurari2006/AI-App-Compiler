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
    with open(
        "generated_app/backend/models.py",
        "w"
    ) as f:
        f.write(
            """
class User:
    pass

class Contact:
    pass
"""
        )

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