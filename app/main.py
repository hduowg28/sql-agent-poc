from fastapi import FastAPI
from app.agents.sql_agent import agent
from app.api.chat import router

app = FastAPI()
app.include_router(router)
