# 🤖 SQL Agent PoC - Superstore Data Analytics Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2%2B-orange.svg)](https://docs.langchain.com/oss/python/langgraph/overview)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg)](https://www.typescriptlang.org/)

**SQL Agent PoC** là hệ thống trợ lý AI phân tích dữ liệu bán lẻ (từ bộ dữ liệu Superstore Retail dataset) dựa trên ngôn ngữ tự nhiên. Hệ thống tự động chuyển đổi câu hỏi tự nhiên của người dùng thành các câu truy vấn SQL an toàn, thực thi trực tiếp trên cơ sở dữ liệu và tổng hợp kết quả phân tích dưới dạng văn bản & bảng biểu trực quan.

---

## 🚀 Hướng Dẫn Chạy Dự Án (Quick Start)

### 1. Chuẩn bị Môi trường Tiền Đề (Prerequisites)

Trước khi khởi chạy dự án, bạn cần chuẩn bị:
1. **Lấy Gemini API Key**:
   - Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Đăng nhập tài khoản Google và bấm **Create API key** để tạo key mới.
   - Lưu lại mã API key để dán vào biến `GEMINI_API_KEY` trong file `.env`.
2. **Cài đặt & Khởi động PostgreSQL Database**:
   - Đảm bảo PostgreSQL đã được cài đặt và service PostgreSQL đang chạy trên máy (mặc định port `5432`).
   - Tạo một database mới tên là `sales_db` (hoặc tên tùy chọn):
     - **Qua Command Line (`psql`)**:
       ```bash
       psql -U postgres -c "CREATE DATABASE sales_db;"
       ```
     - **Qua GUI Tool (pgAdmin / DBeaver / DataGrip)**: Kết nối vào PostgreSQL Server -> Chuột phải vào `Databases` -> Chọn `Create` -> `Database...` -> Đặt tên `sales_db`.

---

### 2. Thiết lập Môi trường Python & Cấu hình `.env`

- **Tạo và kích hoạt môi trường ảo Python**:
  ```bash
  # Mở Terminal tại thư mục gốc sql-agent-poc
  python -m venv venv

  # Trên Windows (PowerShell / CMD):
  .\venv\Scripts\activate

  # Trên Linux / macOS:
  source venv/bin/activate
  ```

- **Cài đặt thư viện phụ thuộc Python**:
  ```bash
  pip install -r requirements.txt
  ```

- **Tạo file cấu hình `.env`**:
  Tạo file `.env` tại thư mục gốc dự án (`sql-agent-poc/.env`) (hoặc copy từ file mẫu `.env.example`):
  ```bash
  # Trên Linux/macOS hoặc Git Bash:
  cp .env.example .env

  # Trên Windows PowerShell:
  Copy-Item .env.example .env
  ```
  Nội dung file `.env`:
  ```env
  APP_ENV=development
  DEBUG=true
  GEMINI_API_KEY=your_gemini_api_key_here
  DATABASE_URL=postgresql://postgres:123456@localhost:5432/sales_db
  ```
  > [!IMPORTANT]
  > - **`GEMINI_API_KEY`**: Thay `your_gemini_api_key_here` bằng Gemini API Key thu được ở Bước 1.
  > - **`DATABASE_URL`**: Đảm bảo đúng định dạng `postgresql://<username>:<password>@<host>:<port>/<dbname>`. Thay `postgres`, `123456`, `5432`, `sales_db` tương ứng với thông tin tài khoản, mật khẩu, port và tên database PostgreSQL của bạn.

---

### 3. Tải Dữ liệu Mẫu vào Database (ETL Data Import)

Trước khi chạy server lần đầu tiên, hãy thực hiện ETL Pipeline để tự động tạo bảng (`customers`, `products`, `orders`) và import dữ liệu từ file `data/Sample - Superstore.csv` vào PostgreSQL:

```bash
python -m app.core.db_uploader
```
*Kết quả thông báo `ETL Pipeline hoàn thành thành công.` tức là dữ liệu đã được nạp đầy đủ vào database.*

---

### 4. Khởi chạy Backend Server (FastAPI)

Chạy máy chủ API Backend với lệnh:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Địa chỉ Backend API**: `http://localhost:8000`
- **Tài liệu Swagger UI interactive docs**: `http://localhost:8000/docs`
- **Tài liệu ReDoc**: `http://localhost:8000/redoc`

---

### 5. Khởi chạy Frontend Web App (React + Vite)

Mở một cửa sổ Terminal thứ hai và thực hiện các lệnh sau:

```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt các gói npm (chỉ cần chạy lần đầu)
npm install

# Chạy server phát triển Frontend
npm run dev
```

- **Địa chỉ Giao diện Web**: `http://localhost:5173`

---

### 6. Chạy Kiểm Thử (Test Suite)

Dự án đi kèm các bộ test tự động để kiểm tra Pydantic schemas và LangGraph agent:

```bash
# Kiểm tra Pydantic Models & Response Envelopes
python test_schemas.py

# Kiểm tra LangGraph Agent & Memory History đa lượt
python test_langgraph_agent.py
```

---

## 🌟 Tính năng nổi bật

- **Trợ lý ReAct SQL dựa trên LangGraph**: Xây dựng trên kiến trúc state machine của **LangGraph**, tích hợp `MemorySaver` checkpointer giúp ghi nhớ và duy trì lịch sử đối thoại đa lượt (multi-turn conversation) theo `session_id`.
- **Bộ Custom Tools tối ưu**:
  - `list_tables`: Liệt kê các bảng hiện có trong cơ sở dữ liệu.
  - `get_table_schema`: Trích xuất DDL schema và dữ liệu mẫu của các bảng.
  - `safe_sql_query`: Thực thi câu truy vấn SQL read-only có tích hợp guardrail bảo mật và timeout.
- **Bảo mật & SQL Execution Guardrail (`sql_validator.py`)**:
  - Bắt buộc chỉ thực thi lệnh `SELECT`.
  - Ngăn chặn hoàn toàn các câu lệnh nguy hiểm (DML/DDL: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, v.v.).
  - Giới hạn số dòng tối đa (LIMIT 100) và áp dụng timeout (30s) chống treo query.
- **Giao diện người dùng hiện đại (Frontend)**:
  - Giao diện Chatbot mượt mà xây dựng bằng **React 19 + TypeScript + Vite**.
  - Tích hợp **SQL Drawer** xem câu lệnh SQL được AI khởi tạo và thực thi cho từng câu hỏi.
  - Hỗ trợ Markdown rendering, gợi ý câu hỏi mẫu (Suggested Prompts), trạng thái loading & xử lý lỗi thân thiện.
- **Thiết kế Backend chuẩn Clean Architecture**:
  - Phân tách rõ ràng giữa API Routers, Business Services, Agent Engine, Data Models (SQLAlchemy) và Pydantic Schemas.
  - Quản lý lifespan fail-fast (kiểm tra DB connection & pre-warm LLM Agent khi khởi động).

---

## 🛠️ Công nghệ sử dụng

### **Backend**
- **Language & Framework**: Python 3.12, FastAPI, Uvicorn
- **AI / Agent Framework**: LangGraph v1.2+, LangChain, Google Gemini API (`gemini-3.1-flash-lite`)
- **Database & ORM**: PostgreSQL, SQLAlchemy, Pydantic v2
- **Utilities**: `python-dotenv`, `pydantic-settings`

### **Frontend**
- **Framework**: React 19, Vite, TypeScript
- **Styling & UI Components**: Modern Vanilla CSS (Glassmorphism design system), Lucide Icons
- **Markdown Rendering**: `react-markdown`, `remark-gfm`

---

## 📂 Cấu trúc thư mục dự án

```text
sql-agent-poc/
├── app/                        # Source code Backend (FastAPI + LangGraph)
│   ├── agents/                 # Định nghĩa LangGraph Agent & Tools
│   │   ├── sql_agent.py        # ReAct Agent Factory với LangGraph & MemorySaver
│   │   ├── tools.py            # Custom LangChain Tools (SafeSQLQueryTool, v.v.)
│   │   └── sql_validator.py    # Guardrail kiểm tra an toàn câu lệnh SQL
│   ├── api/                    # Endpoint API handlers (RESTful routes)
│   │   └── chat.py             # Route /api/v1/chat
│   ├── core/                   # Cấu hình hệ thống, Database Session & Exceptions
│   │   ├── config.py           # Quản lý môi trường qua Pydantic Settings
│   │   ├── database.py         # Kết nối PostgreSQL Engine
│   │   ├── db_uploader.py      # ETL Pipeline import dữ liệu Superstore CSV -> DB
│   │   └── exceptions.py       # Custom Exception types
│   ├── handlers/               # Global Exception Handler
│   ├── models/                 # SQLAlchemy ORM Models (Customer, Order, Product)
│   ├── schemas/                # Pydantic Response/Request validation schemas
│   ├── services/               # Business Logic Layer (ChatService)
│   └── main.py                 # Entry point ứng dụng FastAPI
├── data/                       # Dữ liệu mẫu (Superstore CSV)
├── frontend/                   # Single Page Application (React + Vite + TypeScript)
│   ├── src/
│   │   ├── components/         # ChatInput, ChatMessage, SqlDrawer, Header, v.v.
│   │   ├── services/           # API Client giao tiếp Backend
│   │   ├── types/              # TypeScript interface definitions
│   │   └── App.tsx             # Main Layout Component
│   ├── package.json
│   └── vite.config.ts
├── requirements.txt            # Thư viện Python phụ thuộc
├── test_schemas.py             # Script test Pydantic Schemas
├── test_langgraph_agent.py     # Script test LangGraph Agent & Multi-turn History
├── task.md                     # Danh sách nhiệm vụ dự án
└── README.md                   # Tài liệu hướng dẫn sử dụng
```

---

## 🛰️ Chi tiết API Specs

### **Endpoint chính**: `POST /api/v1/chat`

- **Request Body** (`ChatRequest`):
  ```json
  {
    "question": "Cho tôi biết tổng doanh thu của từng danh mục sản phẩm trong năm 2023?",
    "session_id": "session_user_001",
    "include_sql": true
  }
  ```

- **Response Body** (`ChatResponse`):
  ```json
  {
    "success": true,
    "answer": "## Kết quả\nTổng doanh thu theo danh mục sản phẩm năm 2023 như sau:\n\n| Danh mục | Tổng doanh thu |\n| :--- | :--- |\n| Technology | $245,300.50 |\n| Furniture | $210,150.20 |\n| Office Supplies | $189,400.00 |\n\n## Phân tích\nDanh mục Technology chiếm tỷ trọng cao nhất...",
    "generated_sql": "SELECT p.category, SUM(o.sales) AS total_sales FROM orders o JOIN products p ON o.product_id = p.product_id WHERE EXTRACT(YEAR FROM o.order_date) = 2023 GROUP BY p.category ORDER BY total_sales DESC LIMIT 100;",
    "execution_meta": {
      "execution_time_ms": 1845.2,
      "model_name": "gemini-3.1-flash-lite",
      "sql_executed": true
    }
  }
  ```

---

## 🛡️ Cơ chế Bảo mật & SQL Guardrail

Mọi câu lệnh SQL trước khi gửi tới Database bắt buộc phải đi qua layer `validate_sql()` trong [sql_validator.py](file:///c:/learning/3rd%20year/3%20semerter/sql-agent-poc/app/agents/sql_validator.py):
1. **Chỉ cho phép `SELECT`**: Bắt đầu bằng từ khóa `SELECT` hoặc `WITH` (CTE).
2. **Blacklist từ khóa nguy hiểm**: Chặn các lệnh sửa đổi dữ liệu hoặc cấu trúc DB (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `EXEC`, `GRANT`, `REVOKE`).
3. **Thực thi với Timeout**: Đảm bảo query không gây khóa bảng hoặc quá thời gian xử lý cho phép.

---

## 📜 Giấy phép & Đóng góp

Dự án được phát triển cho mục đích thử nghiệm khái niệm (Proof of Concept - PoC) phân tích dữ liệu ứng dụng Agentic AI.
