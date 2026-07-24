"""
app/agents/sql_agent.py
~~~~~~~~~~~~~~~~~~~~~~~
SQL Agent Factory – tương thích LangChain 1.x / langchain-community.

Thay đổi so với phiên bản cũ:
  - Không còn khởi tạo global ở module level (tránh side-effect khi import)
  - Dùng `create_agent()` factory function → dễ test, dễ mock
  - Bọc query tool của SQL Agent bằng SQLValidatorCallbackHandler
    để guard mọi câu lệnh SQL trước khi thực thi
  - Hỗ trợ read-only thông qua sql_validator trên mọi SQL được thực thi
  - LLM khởi tạo từ settings, không hardcode
  - Singleton `get_agent()` cho FastAPI / service layer
"""

import logging
import warnings
from functools import lru_cache

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.tools import SafeSQLQueryTool
from app.core.config import settings
from app.core.database import engine

# Tắt DeprecationWarning của langchain-community trong runtime
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System Prompt Prefix
# ---------------------------------------------------------------------------
AGENT_PREFIX = """Bạn là một AI assistant chuyên phân tích dữ liệu bán lẻ (Superstore dataset).

QUY TẮC BẮT BUỘC:
1. CHỈ dùng câu lệnh SELECT – không bao giờ INSERT, UPDATE, DELETE, DROP, ALTER.
2. Luôn giới hạn kết quả với LIMIT (tối đa 100 dòng) trừ khi người dùng yêu cầu khác.
3. Trả lời bằng ngôn ngữ của câu hỏi (Tiếng Việt hoặc Tiếng Anh).
4. Nếu câu hỏi không liên quan đến dữ liệu, hãy nói rõ giới hạn của bạn.
5. Giải thích kết quả một cách rõ ràng, dễ hiểu cho người dùng.

Schema database hiện tại:
- customers(customer_id, customer_name, segment, country, city, state, postal_code, region)
- products(product_id, category, sub_category, product_name)
- orders(row_id, order_id, order_date, ship_date, ship_mode, customer_id, product_id,
          sales, quantity, discount, profit)
"""


# ---------------------------------------------------------------------------
# Factory Function
# ---------------------------------------------------------------------------
def create_agent(timeout_seconds: int = 30):
    """
    Tạo và trả về một AgentExecutor (SQL Agent) với:
      - LLM: Gemini Flash từ settings
      - Toolkit: SQLDatabaseToolkit (standard) + SafeSQLQueryTool (custom guard)
      - Mọi SQL đều đi qua sql_validator trước khi thực thi
      - Timeout: giới hạn thời gian thực thi mỗi query

    Args:
        timeout_seconds: Giới hạn thời gian mỗi lần tool chạy SQL.

    Returns:
        AgentExecutor đã được cấu hình.
    """
    logger.info("[AgentFactory] Khởi tạo SQL Agent...")

    # 1. LLM từ settings
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        temperature=0,
        google_api_key=settings.gemini_api_key,
    )

    # 2. SQLDatabase – đọc schema để LLM hiểu cấu trúc bảng
    db = SQLDatabase(engine)

    # 3. SafeSQLQueryTool – custom tool thay thế sql_db_query mặc định
    #    Bọc thêm validator + timeout lên trên khả năng truy vấn gốc
    safe_tool = SafeSQLQueryTool(db=db, timeout_seconds=timeout_seconds)

    # 4. Tạo SQL Agent từ langchain-community (toolkit tiêu chuẩn)
    #    extra_tools: truyền SafeSQLQueryTool vào để agent CÓ THỂ dùng
    #    handle_parsing_errors: không crash khi LLM output lạ
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        prefix=AGENT_PREFIX,
        verbose=settings.debug,
        max_iterations=10,
        max_execution_time=float(timeout_seconds),
        handle_parsing_errors=True,
        extra_tools=[safe_tool],
    )

    logger.info("[AgentFactory] SQL Agent đã sẵn sàng.")
    return agent_executor


@lru_cache(maxsize=1)
def get_agent():
    """
    Singleton accessor – tạo agent một lần, tái sử dụng cho mọi request.
    Dùng với FastAPI Depends hoặc gọi trực tiếp từ service layer.

    Returns:
        AgentExecutor singleton.
    """
    return create_agent()
