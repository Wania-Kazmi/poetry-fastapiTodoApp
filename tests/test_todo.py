import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi_todoapp.main import Todo
from fastapi_todoapp.settings import TEST_DATABASE_URL
from fastapi_todoapp.main import app, get_session
from fastapi.testclient import TestClient

# Setup a test database 
connection_string = str(TEST_DATABASE_URL).replace(
        "postgresql", "postgresql+psycopg"
    )
engine = create_engine(
        connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
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
        # print("Overriding client session")
        return session

    app.dependency_overrides[get_session] = get_session_override   

    client = TestClient(app=app)  
    # print("Successfully override it ------", client)

    yield client  
    app.dependency_overrides.clear()


# Test Root - GET
# @pytest.mark.asyncio
def test_read_root(client:TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

#general test 
# @pytest.mark.asyncio
def test_write_main(client:TestClient):
        todo_content = "buy bread"

        response = client.post("/todos/",
            json={"content": todo_content}
        )

        data = response.json()

        assert response.status_code == 200
        assert data["content"] == todo_content


# Test Read all todos - GET
# @pytest.mark.asyncio
def test_read_todos(session: Session, client: TestClient):
    # Create a todo to read
    todo = Todo(content="Read New Todo 112")
    session.add(todo)
    session.commit()
    session.refresh(todo)

    response = client.get("/todos/")
    print("Response of get todo is -------", response.json())
    # app.dependency_overrides.clear()
    assert response.status_code == 200
    todos = response.json() 
    # print(todos)
    assert todos[-1]["content"] == "Read New Todo 112"



# Create Todo - POST
# @pytest.mark.asyncio
def test_create_todo(client:TestClient):
        # Make the post request within the session context
        response = client.post("/todos/", json={"content": "Post New Todo 1"})
        assert response.status_code == 200
        assert response.json()["content"] == "Post New Todo 1"


#Update Todo - PUT
# @pytest.mark.asyncio
def test_update_todo(client:TestClient):
        # Create a todo first to update it
        response = client.post("/todos/", json={"content": "Old Content"})
        todo_id = response.json()["id"]
    
        # Update the todo
        update_response = client.put(f"/todos/{todo_id}", json={"content": "New Content"})
        assert update_response.status_code == 200
        updated_todo = update_response.json()
        assert updated_todo["content"] == "New Content"
        

# #Delete Todo - DELETE
# @pytest.mark.asyncio
def test_delete_todo(client:TestClient):
        # Create a todo first to delete it
        response = client.post("/todos/", json={"content": "Delete Me"})
        todo_id = response.json()["id"]
    
        # Delete the todo
        delete_response = client.delete(f"/todos/{todo_id}")
        assert delete_response.status_code == 200
        message = delete_response.json()
        assert message == {"message": "Todo successfully deleted"}

        # Verify deletion
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 405