
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/contacts")
def get_contacts():
    return {
        "contacts": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890"
            }
        ]
    }
