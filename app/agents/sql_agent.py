"""
app/agents/sql_agent.py
~~~~~~~~~~~~~~~~~~~~~~~
ReAct SQL Agent Factory – không dùng SQLDatabaseToolkit hay create_sql_agent mặc định của LangChain.

Thay đổi:
  - Khởi tạo ReAct Agent thuần túy với bộ Custom Tools tự định nghĩa:
    * ListTablesTool (liệt kê bảng)
    * GetTableSchemaTool (lấy schema bảng)
    * SafeSQLQueryTool (thực thi SQL an toàn + timeout + validator guard)
  - Hoàn toàn độc lập với SQLDatabaseToolkit của langchain_community
  - Tương thích 100% với ChatService và API layer qua get_agent()
"""

import logging
import warnings
from functools import lru_cache

try:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain.agents import AgentExecutor, create_tool_calling_agent

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.tools import GetTableSchemaTool, ListTablesTool, SafeSQLQueryTool
from app.core.config import get_settings
from app.core.database import engine

# Tắt DeprecationWarning của langchain-community trong runtime
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community")

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI Data Analyst specializing in the Superstore retail database.
You operate using the ReAct (Reasoning + Acting) framework with the following exclusive tools:

AVAILABLE TOOLS:
- `list_tables`: Lists all available tables in the database.
- `get_table_schema`: Retrieves table structures (DDL) and sample rows.
- `sql_query`: Executes a single, read-only SQL SELECT query.

MANDATORY EXECUTION RULES:
1. Database Schema Exploration:
   - Use `list_tables` or `get_table_schema` whenever you need to verify table names or column structures before constructing queries.
2. Read-Only SQL Operations:
   - ONLY execute SELECT queries. NEVER write or attempt INSERT, UPDATE, DELETE, DROP, or ALTER queries.
   - Always limit query results using LIMIT (maximum 100 rows) unless specifically instructed otherwise.
3. Out-of-Scope Handling:
   - If a question is unrelated to the Superstore database or cannot be answered using the available data, politely explain your limitations without attempting to execute queries.

REFERENCE SCHEMA:
- customers(customer_id, customer_name, segment, country, city, state, postal_code, region)
- products(product_id, category, sub_category, product_name)
- orders(row_id, order_id, order_date, ship_date, ship_mode, customer_id, product_id, sales, quantity, discount, profit)
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

AGENT_SYSTEM_PROMPT = SYSTEM_PROMPT + "\n\n" + OUTPUT_PROMPT


def create_agent(timeout_seconds: int = 30) -> AgentExecutor:
    """
    Tạo và trả về một ReAct AgentExecutor thuần túy với:
      - LLM: Gemini Flash từ settings mới nhất
      - Tools: Bộ Custom Tools tự định nghĩa (ListTablesTool, GetTableSchemaTool, SafeSQLQueryTool)
      - Không sử dụng SQLDatabaseToolkit hay create_sql_agent của LangChain
      - SafeSQLQueryTool bọc guard sql_validator & timeout
    """
    logger.info("[AgentFactory] Khởi tạo Custom ReAct SQL Agent...")
    current_settings = get_settings()

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        google_api_key=current_settings.gemini_api_key,
        max_retries=3,
    )

    db = SQLDatabase(engine)

    tools = [
        ListTablesTool(db=db),
        GetTableSchemaTool(db=db),
        SafeSQLQueryTool(db=db, timeout_seconds=timeout_seconds),
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=current_settings.debug,
        max_iterations=10,
        max_execution_time=float(timeout_seconds),
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    logger.info("[AgentFactory] Custom ReAct SQL Agent đã sẵn sàng.")
    return agent_executor


_agent_cache: AgentExecutor | None = None
_cached_api_key: str | None = None


def get_agent() -> AgentExecutor:
    """
    Tải hoặc tái sử dụng Agent singleton.
    Tự động tái khởi tạo nếu API key trong .env thay đổi.
    """
    global _agent_cache, _cached_api_key
    current_api_key = get_settings().gemini_api_key

    if _agent_cache is None or _cached_api_key != current_api_key:
        logger.info("[AgentFactory] Khởi tạo lại Agent với API key mới...")
        _agent_cache = create_agent()
        _cached_api_key = current_api_key

    return _agent_cache