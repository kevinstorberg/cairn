"""Todo CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from assets.backends import get_storage_backend
from assets.base import StorageBackend
from cache.backends import get_cache_backend
from cache.base import CacheBackend
from db.connection import get_session
from memory.backends import get_backend as get_memory_backend
from memory.base import MemoryBackend
from src.models.todo import TodoCreate, TodoResponse, TodoUpdate
from src.repositories.todo import TodoRepository
from src.services.embeddings import EmbeddingsService
from src.services.todo_embeddings import TodoEmbeddingsService

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todo_repository(
    session: AsyncSession = Depends(get_session), cache: CacheBackend = Depends(get_cache_backend)
) -> TodoRepository:
    """Dependency to get todo repository with caching."""
    return TodoRepository(session, cache=cache)


def get_todo_embeddings_service() -> TodoEmbeddingsService:
    """Dependency to get todo embeddings service."""
    embeddings = EmbeddingsService()
    memory = get_memory_backend()
    return TodoEmbeddingsService(embeddings, memory)


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    repo: TodoRepository = Depends(get_todo_repository),
    embeddings_service: TodoEmbeddingsService = Depends(get_todo_embeddings_service),
) -> TodoResponse:
    """Create a new todo."""
    todo = await repo.create(todo_data)

    # Generate and store embedding
    await embeddings_service.embed_todo(todo.id, todo.title, todo.description)

    # Broadcast WebSocket event
    from src.websockets.todo_events import broadcast_todo_created

    response = TodoResponse.model_validate(todo)
    await broadcast_todo_created(response.model_dump())

    return response


@router.get("", response_model=list[TodoResponse])
async def list_todos(
    skip: int = 0, limit: int = 100, repo: TodoRepository = Depends(get_todo_repository)
) -> list[TodoResponse]:
    """List all todos with pagination."""
    todos = await repo.get_all(skip=skip, limit=limit)
    return [TodoResponse.model_validate(todo) for todo in todos]


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: UUID, repo: TodoRepository = Depends(get_todo_repository)) -> TodoResponse:
    """Get a specific todo by ID."""
    todo = await repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.model_validate(todo)


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID, todo_data: TodoUpdate, repo: TodoRepository = Depends(get_todo_repository)
) -> TodoResponse:
    """Update a todo."""
    todo = await repo.update(todo_id, todo_data)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Broadcast WebSocket event
    from src.websockets.todo_events import broadcast_todo_updated

    response = TodoResponse.model_validate(todo)
    await broadcast_todo_updated(response.model_dump())

    return response


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: UUID,
    repo: TodoRepository = Depends(get_todo_repository),
    embeddings_service: TodoEmbeddingsService = Depends(get_todo_embeddings_service),
) -> None:
    """Delete a todo."""
    deleted = await repo.delete(todo_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Delete embedding
    await embeddings_service.delete_todo_embedding(todo_id)

    # Broadcast WebSocket event
    from src.websockets.todo_events import broadcast_todo_deleted

    await broadcast_todo_deleted(str(todo_id))


@router.post("/{todo_id}/attach", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    todo_id: UUID,
    file: UploadFile = File(...),
    repo: TodoRepository = Depends(get_todo_repository),
    storage: StorageBackend = Depends(get_storage_backend),
) -> dict:
    """Upload an attachment for a todo."""
    # Verify todo exists
    todo = await repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Read file content
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    # Generate storage key
    key = f"todos/{todo_id}/{file.filename}"

    # Upload to storage
    await storage.upload(key, content, content_type)

    # Update todo with attachment key
    from src.models.todo import TodoUpdate

    await repo.update(todo_id, TodoUpdate(attachment_key=key))

    return {"key": key, "filename": file.filename, "content_type": content_type, "size": len(content)}


@router.get("/{todo_id}/attach")
async def download_attachment(
    todo_id: UUID,
    repo: TodoRepository = Depends(get_todo_repository),
    storage: StorageBackend = Depends(get_storage_backend),
) -> Response:
    """Download an attachment for a todo."""
    # Verify todo exists and has attachment
    todo = await repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    if not todo.attachment_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No attachment found")

    # Download from storage
    try:
        content = await storage.download(todo.attachment_key)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found in storage")

    # Infer content type from filename
    filename = todo.attachment_key.split("/")[-1]
    content_type = "application/octet-stream"
    if filename.endswith(".pdf"):
        content_type = "application/pdf"
    elif filename.endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    elif filename.endswith(".png"):
        content_type = "image/png"
    elif filename.endswith(".txt"):
        content_type = "text/plain"

    return Response(content=content, media_type=content_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.post("/search", response_model=list[dict])
async def search_todos(
    query: str,
    limit: int = 10,
    embeddings_service: TodoEmbeddingsService = Depends(get_todo_embeddings_service),
    repo: TodoRepository = Depends(get_todo_repository),
) -> list[dict]:
    """Semantic search for todos."""
    # Search embeddings
    results = await embeddings_service.search_todos(query, limit=limit)

    # Enrich with full todo data
    enriched = []
    for result in results:
        todo_id = UUID(result["id"])
        todo = await repo.get_by_id(todo_id)
        if todo:
            enriched.append(
                {"todo": TodoResponse.model_validate(todo).model_dump(), "score": result["score"], "matched_text": result["text"]}
            )

    return enriched


@router.post("/{todo_id}/breakdown", response_model=dict)
async def breakdown_todo(
    todo_id: UUID,
    repo: TodoRepository = Depends(get_todo_repository),
) -> dict:
    """Break down a todo into subtasks using AI."""
    from langchain_core.messages import HumanMessage

    from src.graphs.breakdown import build_breakdown_graph

    # Verify todo exists
    todo = await repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Build graph
    graph = build_breakdown_graph()

    # Create initial state
    initial_state = {
        "messages": [
            HumanMessage(
                content=f"""Break down this todo into 3-5 actionable subtasks.

Todo Title: {todo.title}
Todo Description: {todo.description or 'No description provided'}

For each subtask:
1. Use the get_todo tool to fetch the current todo details
2. Use the create_subtask tool to create each subtask with a clear, actionable title and description

Make subtasks specific and actionable. Each should be completable independently."""
            )
        ],
        "todo_id": str(todo_id),
        "todo_title": todo.title,
        "todo_description": todo.description or "",
        "subtasks_created": [],
    }

    # Run graph
    final_state = graph.invoke(initial_state)

    # Extract subtasks from messages
    subtasks = []
    for message in final_state.get("messages", []):
        if hasattr(message, "tool_calls"):
            for tool_call in message.tool_calls:
                if tool_call.get("name") == "create_subtask":
                    subtasks.append(tool_call.get("args", {}))

    return {"todo_id": str(todo_id), "subtasks_created": len(subtasks), "subtasks": subtasks}


@router.post("/{todo_id}/categorize", response_model=dict)
async def categorize_todo(
    todo_id: UUID,
    repo: TodoRepository = Depends(get_todo_repository),
) -> dict:
    """Categorize a todo using AI with caching."""
    from langchain_core.messages import HumanMessage

    from src.graphs.categorize import build_categorize_graph

    # Verify todo exists
    todo = await repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Build graph
    graph = build_categorize_graph()

    # Create initial state
    todo_text = f"{todo.title}\n{todo.description or ''}"
    initial_state = {
        "messages": [
            HumanMessage(
                content=f"""Categorize this todo into one of these categories:
- development (coding, programming, technical work)
- design (UI/UX, mockups, visual design)
- documentation (writing docs, README, guides)
- testing (QA, writing tests, bug fixing)
- deployment (CI/CD, infrastructure, releases)
- research (investigation, learning, exploration)
- meeting (calls, discussions, planning)
- other (anything else)

Todo: {todo_text}

Use the get_todo tool to fetch the todo, then use update_todo to set its category field to one of the categories above.
Return only the category name."""
            )
        ],
        "todo_id": str(todo_id),
        "todo_text": todo_text,
        "category": None,
    }

    # Run graph
    final_state = graph.invoke(initial_state)

    # Extract category
    category = final_state.get("category")

    return {"todo_id": str(todo_id), "category": category, "cached": False}
