from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiomysql
import logging
from passlib.context import CryptContext

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database configuration without SSL
DB_CONFIG = {
    'host': 'mysql-1fb82b3b-boukhar-d756.e.aivencloud.com',
    'port': 20744,
    'user': 'avnadmin',
    'password': 'AVNS_wWoRjEZRmFF5NgjGCcY',
    'db': 'defaultdb',
    'ssl': None,  # SSL is disabled
    'autocommit': True,
}

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

@app.get("/contacts")
async def get_contacts():
    try:
        # Create a connection pool
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],  # SSL is set to None
            autocommit=DB_CONFIG['autocommit']
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql_select = 'SELECT * FROM contacts'
                await cursor.execute(sql_select)
                results = await cursor.fetchall()
                
                # Column names
                column_names = [desc[0] for desc in cursor.description]
                
                # Convert results to list of dictionaries
                contacts = [dict(zip(column_names, row)) for row in results]
                
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving data from the contacts table: {e}")
    
    return JSONResponse(content={"contacts": contacts})

@app.post("/register")
async def register_user(user: UserCreate):
    try:
        # Create a connection pool
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],  # SSL is set to None
            autocommit=DB_CONFIG['autocommit']
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if the email already exists
                await cursor.execute('SELECT id FROM users WHERE email=%s', (user.email,))
                existing_user = await cursor.fetchone()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already registered")
                
                # Insert the new user
                hashed_password = hash_password(user.password)
                await cursor.execute(
                    'INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                    (user.name, user.email, hashed_password)
                )
                
                # Commit transaction
                await conn.commit()

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while registering the user: {e}")
    
    return JSONResponse(content={"message": "User registered successfully"})

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example health check endpoint
@app.get("/")
async def health_check():
    return {"message": "The health check is successful!"}
