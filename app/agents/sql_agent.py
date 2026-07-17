import os 
from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.database import engine

load_dotenv()
db = SQLDatabase(engine)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0
)
agent = create_sql_agent(
    llm=llm,
    db=db,
    verbose=True
)



