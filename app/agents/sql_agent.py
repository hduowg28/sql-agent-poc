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


# ---------------------------------------------------------------------------
# System Prompt Prefix
# ---------------------------------------------------------------------------
AGENT_SYSTEM_PROMPT = """Bạn là một AI assistant chuyên phân tích dữ liệu bán lẻ (Superstore dataset).
Bạn hoạt động theo cơ chế ReAct (Reasoning + Acting) chỉ sử dụng các công cụ tự định nghĩa:

QUY TẮC BẮT BUỘC:
1. Bạn có các công cụ:
   - `list_tables`: Liệt kê tất cả các bảng trong DB.
   - `get_table_schema`: Lấy cấu trúc DDL và vài dòng mẫu của bảng.
   - `sql_query`: Thực thi câu lệnh SQL SELECT duy nhất.
2. Quy trình làm việc:
   - Nếu cần tìm hiểu cấu trúc cơ sở dữ liệu, hãy dùng `list_tables` hoặc `get_table_schema`.
   - Khi viết SQL, CHỈ dùng câu lệnh SELECT – không bao giờ INSERT, UPDATE, DELETE, DROP, ALTER.
   - Luôn giới hạn kết quả bằng LIMIT (tối đa 100 dòng) trừ khi có yêu cầu khác.
3. Trả lời bằng ngôn ngữ của câu hỏi (Tiếng Việt hoặc Tiếng Anh).
4. Nếu câu hỏi không liên quan đến dữ liệu, hãy giải thích rõ giới hạn của bạn.
5. Giải thích kết quả một cách rõ ràng, trực quan cho người dùng.

Schema tham khảo:
- customers(customer_id, customer_name, segment, country, city, state, postal_code, region)
- products(product_id, category, sub_category, product_name)
- orders(row_id, order_id, order_date, ship_date, ship_mode, customer_id, product_id, sales, quantity, discount, profit)
"""

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

    # 1. LLM từ settings động
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0,
        google_api_key=current_settings.gemini_api_key,
        max_retries=3,
    )

    # 2. SQLDatabase connection
    db = SQLDatabase(engine)

    # 3. Bộ Custom Tools thuần túy
    tools = [
        ListTablesTool(db=db),
        GetTableSchemaTool(db=db),
        SafeSQLQueryTool(db=db, timeout_seconds=timeout_seconds),
    ]

    # 4. ReAct / Tool Calling Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 5. Khởi tạo Tool Calling ReAct Agent
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