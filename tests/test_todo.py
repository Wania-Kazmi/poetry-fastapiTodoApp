# TEST_EXECUTION = True
import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlmodel import Session, SQLModel, create_engine, select
from fastapi_todoapp.main import Todo
from fastapi_todoapp.settings import TEST_DATABASE_URL
from fastapi_todoapp.main import app, get_session
from fastapi.testclient import TestClient

# Setup a test database 
connection_string = str(TEST_DATABASE_URL).replace(
        "postgresql", "postgresql+psycopg"
    )
test_engine =  create_engine(
    "postgresql://waniashah019:qDXbZjHo2Q3V@ep-summer-unit-485132.ap-southeast-1.aws.neon.tech/testing-DB?sslmode=require", connect_args={"sslmode": "require"}, pool_recycle=300
)


# Fixture to setup the test database and session
@pytest.fixture(name="session")
def fixture_test_db_session():
        test_engine =  create_engine(
        connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
        )

        SQLModel.metadata.create_all(test_engine)
        
        with Session(test_engine) as session:
            yield session

@pytest.fixture(name="client", scope="function")  
def client_fixture(session: Session):  
    def get_session_override():  
        print("Overriding client session")
        return session

    app.dependency_overrides[get_session] = get_session_override   

    client = TestClient(app)  
    print("Successfully override it ------", client)
    yield client  
    app.dependency_overrides.clear()


# Test Root - GET
@pytest.mark.asyncio
async def test_read_root(client:TestClient):
    # async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


# Test Read all todos - GET
@pytest.mark.asyncio
async def test_read_todos(session: Session, client: TestClient):

    # Create a todo to read
    todo = Todo(content="Read New Todo 112")
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.get("/todos/") #response coming from production database - why ??????
    print("Response of get todo is -------", response.json())
    # app.dependency_overrides.clear()
    assert response.status_code == 200
    todos = response.json() 
    # print(todos)
    assert todos[-1]["content"] == "Read New Todo 112"



    
# # Test Read all todos - GET
# @pytest.mark.asyncio
# async def test_read_todos(session: Session):
#     def get_session_override():
#         return session  

#     app.dependency_overrides[get_session] = get_session_override

#     client = TestClient(app)
#     # async with test_db_session() as session:
#     # with Session(test_engine) as session:
#     # Create a todo to read
#     todo = Todo(content="Read Todo")
#     session.add(todo)
#     session.commit()
#     session.refresh(todo)

#     # Use the AsyncClient to make the request
#     # async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#     response = client.get("/todos/")
#     app.dependency_overrides.clear()
#     assert response.status_code == 200
#     todos = response.json()
#     assert todos[0]["content"] == "Read Todo"


# Create Todo - POST
# @pytest.mark.asyncio
# async def test_create_todo(session:Session, client:TestClient):
#     # async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         # Create a session using the test database engine
#         # with Session(test_engine) as session:
#             # Make the post request within the session context
#             response = client.post("/todos/", json={"content": "Post New Todo 1"})
#             assert response.status_code == 200
#             assert response.json()["content"] == "Post New Todo 1"
            
#             # Query the database to ensure the new todo has been added
#             # new_todo = session.exec(select(Todo).order_by(Todo.id.desc())).first()
#             # assert new_todo is not None
#             # assert new_todo.content == "Post Todo 1"



# # Create Todo - POST
# @pytest.mark.asyncio
# async def test_create_todo():
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         # Create a session using the test database engine
#         with Session(test_engine) as session:
#             # Make the post request within the session context
#             response = await ac.post("/todos/", json={"content": "Post Todo 1"})
#             assert response.status_code == 200
#             assert response.json()["content"] == "Post Todo 1"
            
#             # Query the database to ensure the new todo has been added
#             new_todo = session.exec(select(Todo).order_by(Todo.id.desc())).first()
#             assert new_todo is not None
#             assert new_todo.content == "Post Todo 1"


# #Update Todo - PUT
# @pytest.mark.asyncio
# async def test_update_todo():
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         # Create a todo first to update it
#         response = await ac.post("/todos/", json={"content": "Old Content"})
#         todo_id = response.json()["id"]
    
#         # Update the todo
#         update_response = await ac.put(f"/todos/{todo_id}", json={"content": "New Content"})
#         assert update_response.status_code == 200
#         updated_todo = update_response.json()
#         assert updated_todo["content"] == "New Content"
        

# #Delete Todo - DELETE
# @pytest.mark.asyncio
# async def test_delete_todo():
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         # Create a todo first to delete it
#         response = await ac.post("/todos/", json={"content": "Delete Me"})
#         todo_id = response.json()["id"]
    
#         # Delete the todo
#         delete_response = await ac.delete(f"/todos/{todo_id}")
#         assert delete_response.status_code == 200
#         message = delete_response.json()
#         assert message == {"message": "Todo successfully deleted"}

#         # Verify deletion
#         get_response = await ac.get(f"/todos/{todo_id}")
#         assert get_response.status_code == 405