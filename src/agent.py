import os 
from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from database import engine

load_dotenv()
db = SQLDatabase(engine)
def get_sql_agent():
    """Hàm khởi tạo và trả về SQL Agent"""
    # Khởi tạo mô hình (Gemini sẽ tự động lấy API Key từ môi trường hệ thống vừa load)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    
    agent_executor = create_sql_agent(llm, db=db, verbose=True)
    return agent_executor

