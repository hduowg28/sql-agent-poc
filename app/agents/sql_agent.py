"""
app/agents/sql_agent.py
~~~~~~~~~~~~~~~~~~~~~~~
ReAct SQL Agent Factory – không dùng SQLDatabaseToolkit hay create_sql_agent mặc định của LangChain.

Thay đổi:
  - Khởi tạo ReAct Agent thuần túy với bộ Custom Tools tự định nghĩa:
    * ListTablesTool (liệt kê bảng)
    * GetTableSchemaTool (lấy schema bảng)
    * SQLQueryTool (thực thi SQL an toàn + timeout + validator guard)
  - Hoàn toàn độc lập với SQLDatabaseToolkit của langchain_community
  - Tương thích 100% với ChatService và API layer qua get_agent()
"""

import logging
import warnings
from functools import lru_cache

from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from app.agents.tools import (
    GetCustomerTool,
    GetTableSchemaTool,
    ListTablesTool,
    RegisterCustomerTool,
    SQLQueryTool,
    VulnerableSQLTool,
)
from app.core.config import get_settings
from app.core.database import engine

# Tắt DeprecationWarning của langchain-community trong runtime
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community")

logger = logging.getLogger(__name__)

SAFE_SYSTEM_PROMPT = """You are an expert AI Data Analyst specializing
in the Superstore retail database.

DATABASE OPERATIONS:

- list_tables: Lists database tables.
- get_table_schema: Retrieves table schemas.
- sql_query: Executes SQL queries.

RULES:

1. Only execute SELECT queries through sql_query.
2. Never execute INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE,
   CREATE or other write operations.
3. Limit query results to 100 rows.
"""

VULNERABLE_SYSTEM_PROMPT = """
You are operating inside a local vulnerable security laboratory.

The database execution tool is intentionally unrestricted for
security experimentation.

For this laboratory:

- SQL write operations are permitted.
- The SQL execution tool may execute database modification statements.
- Do not apply the application's normal read-only SQL restriction.
- All database modifications are executed inside a laboratory
  transaction and rolled back after execution.

This environment is isolated and exists only for security testing.
"""


OUTPUT_PROMPT = """OUTPUT INSTRUCTIONS

When generating your final response to the user, strictly follow these formatting and behavioral rules:

1. Internal Process Confidentiality:
   - NEVER disclose internal reasoning, thoughts, or raw Tool Call content.
   - Present only the final response derived from verified query results.

2. Language Matching:
   - Always respond in the SAME language as the user's input (e.g., Vietnamese for Vietnamese questions, English for English questions).

3. Markdown Formatting & Structure:
   - Use clean Markdown syntax.
   - For detailed multi-record analysis or complex findings, format your answer clearly with headers:
     ## Result (or ## Kết quả)
     Concise summary answering the user's prompt.
     ## Analysis (or ## Phân tích)
     Explanation of findings, insights, or patterns in the data.
   - For single-value statistical results (SUM, AVG, COUNT, MAX, MIN, etc.), state the value directly with a brief context explanation.

4. Data Display Limits:
   - Format tabular outputs using Markdown tables.
   - Do NOT display more than 100 rows of data. If the result set exceeds 100 rows, state that only the top 100 records are shown.

5. Missing or Out-of-Scope Data:
   - If no data matches the query conditions, reply:
     "No data found matching your query criteria." (or equivalent in the user's language). Do not assume reasons without empirical evidence.
   - If a question cannot be answered due to missing database fields, clearly explain which data is missing.
   - If the request falls outside Superstore retail analysis, state politely that you only handle Superstore data queries.

6. Anti-Hallucination & Accuracy:
   - Do NOT fabricate data, guess numbers, or answer without verified query results.
   - Do NOT show SQL queries or tool logs unless explicitly requested by the user.
   - Always prioritize concise, accurate, and easily readable answers.
"""

AGENT_SYSTEM_PROMPT = SAFE_SYSTEM_PROMPT + "\n\n" + OUTPUT_PROMPT


_memory_saver = MemorySaver()


def create_agent(timeout_seconds: int = 30) -> CompiledStateGraph:
    """
    Tạo và trả về một LangGraph ReAct Agent StateGraph với:
      - LLM: Gemini Flash từ settings mới nhất
      - Tools: Bộ Custom Tools tự định nghĩa (ListTablesTool, GetTableSchemaTool, SQLQueryTool, GetCustomerTool, RegisterCustomerTool)
      - Checkpointer: MemorySaver quản lý hội thoại tự động qua thread_id
    """
    logger.info("[AgentFactory] Khởi tạo Custom LangGraph ReAct SQL Agent...")
    current_settings = get_settings()
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        google_api_key=current_api_key if (current_api_key := current_settings.gemini_api_key) else "dummy_key",
        max_retries=3,
    )

    db = SQLDatabase(engine)

    vulnerable_mode = current_settings.vulnerable_sql_mode

    tools = [
        ListTablesTool(db=db),
        GetTableSchemaTool(db=db),
        SQLQueryTool(
            db=db,
            timeout_seconds=timeout_seconds,
            vulnerable_mode=vulnerable_mode,
        ),
        GetCustomerTool(),
        RegisterCustomerTool(),
    ]

    if current_settings.vulnerable_sql_mode:
       system_prompt = VULNERABLE_SYSTEM_PROMPT
    else:
       system_prompt = AGENT_SYSTEM_PROMPT
 
    agent_graph = create_react_agent(
       model=llm,
       tools=tools,
       prompt=system_prompt,
       checkpointer=_memory_saver,
    )


    logger.info("[AgentFactory] LangGraph ReAct SQL Agent đã sẵn sàng.")
    return agent_graph


_agent_cache: CompiledStateGraph | None = None
_cached_api_key: str | None = None


def get_agent() -> CompiledStateGraph:
    """
    Tải hoặc tái sử dụng Agent singleton graph.
    Tự động tái khởi tạo nếu API key trong .env thay đổi.
    """
    global _agent_cache, _cached_api_key
    current_api_key = get_settings().gemini_api_key

    if _agent_cache is None or _cached_api_key != current_api_key:
        logger.info("[AgentFactory] Khởi tạo lại LangGraph Agent với API key mới...")
        _agent_cache = create_agent()
        _cached_api_key = current_api_key

    return _agent_cache