TEST_EXECUTION = True
import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from fastapi_todoapp.main import app  
from sqlmodel import Session, SQLModel, create_engine, select
from fastapi_todoapp.main import Todo
from fastapi_todoapp.settings import TEST_DATABASE_URL

# Setup a test database 
connection_string = str(TEST_DATABASE_URL).replace(
        "postgresql", "postgresql+psycopg"
    )
# TEST_DATABASE_URL = "postgresql://waniashah019:qDXbZjHo2Q3V@ep-summer-unit-485132.ap-southeast-1.aws.neon.tech/testing-DB?sslmode=require"
test_engine =  create_engine(
    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)


# Fixture to setup the test database and session
@pytest.fixture(name="test_db_session", scope="function")
async def fixture_test_db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with Session(test_engine) as session:
        yield session

    # async with Session(test_engine) as session:
    #     print("session created is ------------------",session)
    #     yield session


    # # Create a test client using the FastAPI app
    # async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
    #     yield client

# Test Root - GET
@pytest.mark.asyncio
async def test_read_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}


# Test Read all todos - GET
@pytest.mark.asyncio
async def test_read_todos():
    # async with test_db_session() as session:
    with Session(test_engine) as session:
    # Create a todo to read
        todo = Todo(content="Read Todo")
        session.add(todo)
        session.commit()
        session.refresh(todo)

    # Use the AsyncClient to make the request
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/todos/")
        assert response.status_code == 200
        # todos = response.json()
        # assert len(todos) == 1
        # assert todos[0]["content"] == "Read Todo"


# Create Todo - POST
@pytest.mark.asyncio
async def test_create_todo():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a session using the test database engine
        with Session(test_engine) as session:
            # Make the post request within the session context
            response = await ac.post("/todos/", json={"content": "Post Todo 1"})
            assert response.status_code == 200
            assert response.json()["content"] == "Post Todo 1"
            
            # Query the database to ensure the new todo has been added
            new_todo = session.exec(select(Todo).order_by(Todo.id.desc())).first()
            assert new_todo is not None
            assert new_todo.content == "Post Todo 1"


#Update Todo - PUT
@pytest.mark.asyncio
async def test_update_todo():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a todo first to update it
        response = await ac.post("/todos/", json={"content": "Old Content"})
        todo_id = response.json()["id"]
    
        # Update the todo
        update_response = await ac.put(f"/todos/{todo_id}", json={"content": "New Content"})
        assert update_response.status_code == 200
        updated_todo = update_response.json()
        assert updated_todo["content"] == "New Content"
        

#Delete Todo - DELETE
@pytest.mark.asyncio
async def test_delete_todo():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a todo first to delete it
        response = await ac.post("/todos/", json={"content": "Delete Me"})
        todo_id = response.json()["id"]
    
        # Delete the todo
        delete_response = await ac.delete(f"/todos/{todo_id}")
        assert delete_response.status_code == 200
        message = delete_response.json()
        assert message == {"message": "Todo successfully deleted"}

        # Verify deletion
        get_response = await ac.get(f"/todos/{todo_id}")
        assert get_response.status_code == 405