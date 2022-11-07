from fastapi import APIRouter
from fastapi.templating import Jinja2Templates





def create_jobs(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter(prefix="/jobs")
