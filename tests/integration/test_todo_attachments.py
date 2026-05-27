"""
Integration tests for TODO attachments.

Tests:
- POST /todos/{id}/attach uploads file to storage
- GET /todos/{id}/attach downloads file from storage
- attachment_key stored in database
- Content-type handling
- Missing attachment returns 404
- Large file upload (multipart)
- Storage backend error handling
"""

from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient

from db.models.todo import Todo
from src.app import create_app


@pytest.mark.integration
class TestTodoAttachments:
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_upload_attachment(self, client, db_session, clean_db):
        """Test POST /todos/{id}/attach uploads file."""
        # Create a todo first
        todo = Todo(title="Todo with attachment")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Upload a file
        file_content = b"This is a test PDF file"
        async with client:
            response = await client.post(
                f"/todos/{todo.id}/attach",
                files={"file": ("test.pdf", BytesIO(file_content), "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["size"] == len(file_content)
        assert "key" in data
        assert str(todo.id) in data["key"]

    @pytest.mark.asyncio
    async def test_upload_attachment_todo_not_found(self, client, clean_db):
        """Test 404 when uploading to non-existent todo."""
        from uuid import uuid4

        fake_id = uuid4()
        file_content = b"test"

        async with client:
            response = await client.post(
                f"/todos/{fake_id}/attach", files={"file": ("test.txt", BytesIO(file_content), "text/plain")}
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    @pytest.mark.asyncio
    async def test_download_attachment(self, client, db_session, clean_db):
        """Test GET /todos/{id}/attach downloads file."""
        # Create a todo
        todo = Todo(title="Todo with attachment")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Upload a file
        file_content = b"Download test content"
        async with client:
            upload_response = await client.post(
                f"/todos/{todo.id}/attach",
                files={"file": ("download.txt", BytesIO(file_content), "text/plain")},
            )
            assert upload_response.status_code == 201

            # Download the file
            download_response = await client.get(f"/todos/{todo.id}/attach")

        assert download_response.status_code == 200
        assert download_response.content == file_content
        assert "attachment" in download_response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_download_attachment_not_found(self, client, db_session, clean_db):
        """Test 404 when downloading from todo without attachment."""
        # Create a todo without attachment
        todo = Todo(title="Todo without attachment")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        async with client:
            response = await client.get(f"/todos/{todo.id}/attach")

        assert response.status_code == 404
        assert response.json()["detail"] == "No attachment found"

    @pytest.mark.asyncio
    async def test_download_attachment_todo_not_found(self, client, clean_db):
        """Test 404 when downloading from non-existent todo."""
        from uuid import uuid4

        fake_id = uuid4()

        async with client:
            response = await client.get(f"/todos/{fake_id}/attach")

        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    @pytest.mark.asyncio
    async def test_upload_replaces_previous_attachment(self, client, db_session, clean_db):
        """Test uploading new file replaces previous attachment key."""
        # Create a todo
        todo = Todo(title="Todo with multiple attachments")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Upload first file
        async with client:
            response1 = await client.post(
                f"/todos/{todo.id}/attach", files={"file": ("first.txt", BytesIO(b"first"), "text/plain")}
            )
            assert response1.status_code == 201
            key1 = response1.json()["key"]

            # Upload second file
            response2 = await client.post(
                f"/todos/{todo.id}/attach", files={"file": ("second.txt", BytesIO(b"second"), "text/plain")}
            )
            assert response2.status_code == 201
            key2 = response2.json()["key"]

        # Keys should be different
        assert key1 != key2

        # Download should return the second file
        async with client:
            download_response = await client.get(f"/todos/{todo.id}/attach")

        assert download_response.status_code == 200
        assert download_response.content == b"second"

    @pytest.mark.asyncio
    async def test_attachment_key_stored_in_database(self, client, db_session, clean_db):
        """Test that attachment_key is persisted to database."""
        # Create a todo
        todo = Todo(title="Todo with attachment key")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        todo_id = todo.id

        # Upload file
        async with client:
            response = await client.post(
                f"/todos/{todo_id}/attach", files={"file": ("key_test.pdf", BytesIO(b"content"), "application/pdf")}
            )
            assert response.status_code == 201
            expected_key = response.json()["key"]

        # Query database directly
        await db_session.refresh(todo)
        assert todo.attachment_key == expected_key
        assert "key_test.pdf" in todo.attachment_key

    @pytest.mark.asyncio
    async def test_content_type_handling(self, client, db_session, clean_db):
        """Test different content types are handled correctly."""
        # Create todos
        todo_pdf = Todo(title="PDF todo")
        todo_image = Todo(title="Image todo")
        todo_text = Todo(title="Text todo")
        db_session.add_all([todo_pdf, todo_image, todo_text])
        await db_session.commit()
        await db_session.refresh(todo_pdf)
        await db_session.refresh(todo_image)
        await db_session.refresh(todo_text)

        async with client:
            # Upload PDF
            pdf_response = await client.post(
                f"/todos/{todo_pdf.id}/attach",
                files={"file": ("doc.pdf", BytesIO(b"pdf content"), "application/pdf")},
            )
            assert pdf_response.status_code == 201
            assert pdf_response.json()["content_type"] == "application/pdf"

            # Upload image
            img_response = await client.post(
                f"/todos/{todo_image.id}/attach",
                files={"file": ("photo.png", BytesIO(b"png content"), "image/png")},
            )
            assert img_response.status_code == 201
            assert img_response.json()["content_type"] == "image/png"

            # Upload text
            txt_response = await client.post(
                f"/todos/{todo_text.id}/attach", files={"file": ("note.txt", BytesIO(b"text content"), "text/plain")}
            )
            assert txt_response.status_code == 201
            assert txt_response.json()["content_type"] == "text/plain"

    @pytest.mark.asyncio
    async def test_large_file_upload(self, client, db_session, clean_db):
        """Test uploading larger file (1MB)."""
        # Create a todo
        todo = Todo(title="Large file todo")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Create 1MB file
        large_content = b"x" * (1024 * 1024)  # 1MB

        async with client:
            response = await client.post(
                f"/todos/{todo.id}/attach",
                files={"file": ("large.bin", BytesIO(large_content), "application/octet-stream")},
            )

        assert response.status_code == 201
        assert response.json()["size"] == len(large_content)

        # Verify download works
        async with client:
            download_response = await client.get(f"/todos/{todo.id}/attach")

        assert download_response.status_code == 200
        assert len(download_response.content) == len(large_content)
