from contextlib import asynccontextmanager
from typing import Optional
from fastapi_todoapp.settings import DATABASE_URL, TEST_DATABASE_URL
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from tests.test_todo import TEST_EXECUTION

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)


# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
# connection_string = str(settings.DATABASE_URL).replace(
#     "postgresql", "postgresql+psycopg"
# )
    


# Determine which database URL to use based on the environment
if TEST_EXECUTION:
    connection_string = str(TEST_DATABASE_URL).replace(
        "postgresql", "postgresql+psycopg"
    )
else:
    connection_string = str(DATABASE_URL).replace(
        "postgresql", "postgresql+psycopg"
    )

# recycle connections after 5 minutes
# to correspond with the compute scale down
engine = create_engine(
    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)



def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



# The first part of the function, before the yield, will
# be executed before the application starts

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield



app = FastAPI(lifespan=lifespan)



@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/todos/")
def read_todos():
    with Session(engine) as session:
        todos = session.exec(select(Todo)).all()
        return todos
    
@app.post("/todos/")
def create_todo(todo: Todo):
    with Session(engine) as session:
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, updated_todo: Todo):
    with Session(engine) as session:
        # Fetch existing todo from DB
        existing_todo = session.get(Todo, todo_id)

        # If the todo does not exist - raise an HTTPException 
        if existing_todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")

        # Update the content
        existing_todo.content = updated_todo.content
        session.commit()
        session.refresh(existing_todo)
        return existing_todo


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    with Session(engine) as session:
        #Fetch existing todo from DB
        existing_todo = session.get(Todo, todo_id)

        if existing_todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")

        # Delete the todo from DB
        session.delete(existing_todo)
        session.commit()
        return {"message": "Todo successfully deleted"}