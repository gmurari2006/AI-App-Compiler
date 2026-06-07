
from fastapi import APIRouter

router = APIRouter()



@router.post("/login")
def post_login():
    return {
        "endpoint": "/login",
        "method": "POST",
        "status": "success"
    }


@router.get("/dashboard")
def get_dashboard():
    return {
        "endpoint": "/dashboard",
        "method": "GET",
        "status": "success"
    }


@router.get("/contacts")
def get_contacts():
    return {
        "endpoint": "/contacts",
        "method": "GET",
        "status": "success"
    }


@router.get("/admin/analytics")
def get_admin_analytics():
    return {
        "endpoint": "/admin/analytics",
        "method": "GET",
        "status": "success"
    }


@router.get("/admin/dashboard")
def get_admin_dashboard():
    return {
        "endpoint": "/admin/dashboard",
        "method": "GET",
        "status": "success"
    }
