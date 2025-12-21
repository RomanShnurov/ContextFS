# OpenAI Agent SDK Integration

Пошаговое руководство по интеграции file-knowledge-mcp с OpenAI Agent SDK.

## Обзор

OpenAI Agent SDK не имеет встроенной поддержки протокола MCP, поэтому требуется промежуточный слой для взаимодействия. Существует два основных подхода:

1. **Прямая интеграция через MCP клиент** (рекомендуется) - Python клиент запускает MCP сервер и преобразует его инструменты в OpenAI function calling
2. **REST API wrapper** - Создать HTTP API поверх MCP сервера

---

## Подход 1: Прямая интеграция (рекомендуется)

Этот подход позволяет OpenAI Agent SDK напрямую использовать инструменты MCP сервера.

### Шаг 1: Установка зависимостей

```bash
# Установите MCP сервер
pip install file-knowledge-mcp

# Установите MCP клиентскую библиотеку
pip install mcp

# Установите OpenAI SDK
pip install openai

# Системные зависимости
# Ubuntu/Debian:
sudo apt install ugrep poppler-utils

# macOS:
brew install ugrep poppler
```

### Шаг 2: Создание MCP-OpenAI Bridge

Создайте файл `mcp_openai_bridge.py`:

```python
import asyncio
import json
from typing import Any, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI


class MCPOpenAIBridge:
    """Мост между MCP сервером и OpenAI Agent SDK."""

    def __init__(self, knowledge_root: str, openai_api_key: str):
        self.knowledge_root = knowledge_root
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.mcp_session = None
        self.mcp_tools = []

    async def start(self):
        """Запускает MCP сервер и получает список инструментов."""
        server_params = StdioServerParameters(
            command="file-knowledge-mcp",
            args=["--root", self.knowledge_root]
        )

        # Запускаем MCP сервер
        self.read, self.write = await stdio_client(server_params).__aenter__()
        self.mcp_session = await ClientSession(self.read, self.write).__aenter__()

        # Инициализируем сессию
        await self.mcp_session.initialize()

        # Получаем список инструментов
        tools_list = await self.mcp_session.list_tools()
        self.mcp_tools = [tool for tool in tools_list]

        print(f"MCP сервер запущен. Доступно инструментов: {len(self.mcp_tools)}")

    async def stop(self):
        """Останавливает MCP сервер."""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'read'):
            await self.read.__aexit__(None, None, None)

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """
        Преобразует MCP инструменты в формат OpenAI function calling.

        Returns:
            Список инструментов в формате OpenAI
        """
        openai_tools = []

        for tool in self.mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Вызывает MCP инструмент.

        Args:
            tool_name: Имя инструмента
            arguments: Аргументы для инструмента

        Returns:
            Результат выполнения инструмента
        """
        result = await self.mcp_session.call_tool(tool_name, arguments=arguments)
        return result

    async def chat(self, messages: List[Dict[str, str]], model: str = "gpt-4"):
        """
        Чат с автоматическим вызовом MCP инструментов.

        Args:
            messages: История сообщений
            model: Модель OpenAI для использования

        Returns:
            Ответ ассистента
        """
        # Получаем инструменты в формате OpenAI
        tools = self.get_openai_tools()

        # Создаем запрос к OpenAI
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Если модель хочет вызвать инструменты
        if tool_calls:
            # Добавляем ответ ассистента в историю
            messages.append(response_message)

            # Вызываем каждый инструмент
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"Вызов инструмента: {function_name} с аргументами: {function_args}")

                # Вызываем MCP инструмент
                function_response = await self.call_mcp_tool(
                    function_name,
                    function_args
                )

                # Добавляем результат в историю
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response)
                })

            # Получаем финальный ответ от модели
            second_response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages
            )

            return second_response.choices[0].message

        return response_message


async def main():
    """Пример использования."""

    # Инициализируем мост
    bridge = MCPOpenAIBridge(
        knowledge_root="./documents",  # Путь к вашим документам
        openai_api_key="your-openai-api-key"  # Ваш API ключ OpenAI
    )

    try:
        # Запускаем MCP сервер
        await bridge.start()

        # Создаем диалог
        messages = [
            {
                "role": "user",
                "content": "Найди в моих документах информацию об аутентификации"
            }
        ]

        # Получаем ответ с автоматическим вызовом инструментов
        response = await bridge.chat(messages, model="gpt-4")

        print(f"\nОтвет ассистента: {response.content}")

    finally:
        # Останавливаем MCP сервер
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

### Шаг 3: Настройка конфигурации

Создайте `config.yaml` для MCP сервера:

```yaml
knowledge:
  root: "./documents"  # Путь к вашим документам

search:
  context_lines: 5
  max_results: 50
  timeout_seconds: 30

security:
  enable_shell_filters: true
  filter_mode: whitelist
  allow_symlinks: false

exclude:
  patterns:
    - ".git/*"
    - "*.bak"
    - "*.tmp"
```

### Шаг 4: Использование в вашем боте

```python
import asyncio
import os
from mcp_openai_bridge import MCPOpenAIBridge


async def run_knowledge_bot():
    """Запуск бота с доступом к локальным документам."""

    # Создаем мост
    bridge = MCPOpenAIBridge(
        knowledge_root="/path/to/your/documents",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    try:
        # Запускаем MCP сервер
        await bridge.start()

        print("Бот запущен! Доступные инструменты:")
        for tool in bridge.mcp_tools:
            print(f"  - {tool.name}: {tool.description}")

        # Интерактивный режим
        while True:
            user_input = input("\nВы: ")
            if user_input.lower() in ["exit", "quit", "выход"]:
                break

            messages = [{"role": "user", "content": user_input}]
            response = await bridge.chat(messages, model="gpt-4")

            print(f"Бот: {response.content}")

    finally:
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(run_knowledge_bot())
```

### Шаг 5: Запуск

```bash
# Установите переменную окружения с API ключом
export OPENAI_API_KEY=your-openai-api-key

# Запустите бота
python your_bot.py
```

---

## Подход 2: REST API Wrapper

Если вам нужен HTTP интерфейс для интеграции с другими системами.

### Шаг 1: Создание REST API

Создайте `mcp_rest_server.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager


# Глобальные переменные для MCP сессии
mcp_session = None
mcp_read = None
mcp_write = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    global mcp_session, mcp_read, mcp_write

    # Запуск MCP сервера
    server_params = StdioServerParameters(
        command="file-knowledge-mcp",
        args=["--root", "./documents"]
    )

    mcp_read, mcp_write = await stdio_client(server_params).__aenter__()
    mcp_session = await ClientSession(mcp_read, mcp_write).__aenter__()
    await mcp_session.initialize()

    print("MCP сервер запущен")

    yield

    # Остановка MCP сервера
    if mcp_session:
        await mcp_session.__aexit__(None, None, None)
    if mcp_read:
        await mcp_read.__aexit__(None, None, None)

    print("MCP сервер остановлен")


app = FastAPI(title="File Knowledge MCP REST API", lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    collection: Optional[str] = None
    document: Optional[str] = None
    max_results: int = 20


class ReadRequest(BaseModel):
    path: str
    start_page: Optional[int] = None
    end_page: Optional[int] = None


@app.get("/")
async def root():
    """Информация об API."""
    return {
        "name": "File Knowledge MCP REST API",
        "version": "1.0.0",
        "endpoints": [
            "/search - Поиск по документам",
            "/collections - Список коллекций",
            "/read - Чтение документа",
            "/tools - Список доступных инструментов"
        ]
    }


@app.get("/tools")
async def list_tools():
    """Получить список всех доступных MCP инструментов."""
    tools = await mcp_session.list_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
            for tool in tools
        ]
    }


@app.post("/search")
async def search(request: SearchRequest):
    """Поиск по документам."""
    scope = {"type": "global"}

    if request.document:
        scope = {"type": "document", "path": request.document}
    elif request.collection:
        scope = {"type": "collection", "path": request.collection}

    try:
        result = await mcp_session.call_tool(
            "search_documents",
            arguments={
                "query": request.query,
                "scope": scope,
                "max_results": request.max_results
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections")
async def list_collections(path: str = ""):
    """Список коллекций (папок)."""
    try:
        result = await mcp_session.call_tool(
            "list_collections",
            arguments={"path": path}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/read")
async def read_document(request: ReadRequest):
    """Чтение документа."""
    try:
        args = {"path": request.path}
        if request.start_page is not None:
            args["start_page"] = request.start_page
        if request.end_page is not None:
            args["end_page"] = request.end_page

        result = await mcp_session.call_tool(
            "read_document",
            arguments=args
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Шаг 2: Установка зависимостей

```bash
pip install fastapi uvicorn file-knowledge-mcp mcp
```

### Шаг 3: Запуск REST сервера

```bash
# Запустите сервер
python mcp_rest_server.py

# Сервер будет доступен на http://localhost:8000
```

### Шаг 4: Использование в OpenAI Agent

```python
import openai
import requests
import json


def search_knowledge(query: str, collection: str = None) -> str:
    """Функция для поиска в базе знаний через REST API."""
    response = requests.post(
        "http://localhost:8000/search",
        json={
            "query": query,
            "collection": collection,
            "max_results": 10
        }
    )
    return json.dumps(response.json())


def read_document(path: str) -> str:
    """Функция для чтения документа через REST API."""
    response = requests.post(
        "http://localhost:8000/read",
        json={"path": path}
    )
    return json.dumps(response.json())


# Определяем инструменты для OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Поиск в базе знаний по запросу",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос"
                    },
                    "collection": {
                        "type": "string",
                        "description": "Ограничить поиск коллекцией (опционально)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Прочитать содержимое документа",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к документу"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

# Используем в чате
client = openai.OpenAI()

messages = [
    {"role": "user", "content": "Найди информацию об API в моих документах"}
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# Обработка вызовов функций
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "search_knowledge":
            args = json.loads(tool_call.function.arguments)
            result = search_knowledge(**args)
            print(f"Результат поиска: {result}")
```

---

## Сравнение подходов

| Критерий | Прямая интеграция | REST API |
|----------|-------------------|----------|
| Производительность | ⚡ Быстрее (нет HTTP overhead) | 🐌 Медленнее (HTTP запросы) |
| Простота развертывания | ✅ Один процесс | ❌ Два процесса (API + бот) |
| Масштабируемость | ❌ Один бот | ✅ Много клиентов |
| Отладка | ❌ Сложнее | ✅ Проще (можно тестировать curl) |
| Универсальность | ❌ Только Python | ✅ Любой язык |

---

## Рекомендации

### Для разработки и простых случаев
Используйте **Прямую интеграцию** - проще в настройке, меньше зависимостей.

### Для production и нескольких ботов
Используйте **REST API** - проще масштабировать и мониторить.

---

## Дополнительные возможности

### Docker compose для production

```yaml
version: "3.8"

services:
  mcp-rest-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./documents:/knowledge:ro
    environment:
      - FKM_KNOWLEDGE__ROOT=/knowledge
      - FKM_SECURITY__FILTER_MODE=whitelist
    restart: unless-stopped

  openai-bot:
    build: ./bot
    depends_on:
      - mcp-rest-api
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_API_URL=http://mcp-rest-api:8000
    restart: unless-stopped
```

### Мониторинг и логирование

```python
import logging

# Настройте логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# В вашем боте
logger.info(f"MCP tool called: {tool_name}")
logger.info(f"Search query: {query}")
```

---

## Устранение проблем

### MCP сервер не запускается
```bash
# Проверьте установку
which file-knowledge-mcp

# Проверьте системные зависимости
which ugrep
which pdftotext
```

### Timeout ошибки
Увеличьте таймауты в конфигурации:
```yaml
search:
  timeout_seconds: 60

security:
  filter_timeout: 45
```

### Permission denied
```bash
# Убедитесь, что документы доступны для чтения
chmod -R +r /path/to/documents
```

---

## Полезные ссылки

- [MCP Documentation](https://modelcontextprotocol.io/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [file-knowledge-mcp Configuration](configuration.md)
- [file-knowledge-mcp Tools Reference](tools.md)
