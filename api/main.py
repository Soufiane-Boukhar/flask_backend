from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiomysql
import logging
from passlib.context import CryptContext
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)

DB_CONFIG = {
    'host': 'mysql-1fb82b3b-boukhar-d756.e.aivencloud.com',
    'port': 20744,
    'user': 'avnadmin',
    'password': 'AVNS_wWoRjEZRmFF5NgjGCcY',
    'db': 'defaultdb',
    'ssl': None,
    'autocommit': True,
}

SECRET_KEY = secrets.token_hex(32) 
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_hmac_token(data: dict) -> str:
    """Create an HMAC token using the SECRET_KEY."""
    message = str(data).encode()
    return hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create an access token using HMAC."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = create_hmac_token(to_encode)
    return encoded_jwt

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class SuiverCreate(BaseModel):
    name: str
    activity: str
    contact: str
    type_of_property: str
    budget: Optional[float] = None
    area: Optional[float] = None
    zone: Optional[str] = None
    services_provided: Optional[str] = None
    allocated_price: Optional[float] = None
    closed_services: Optional[str] = None
    services_to_close: Optional[str] = None
    status: str
    annexes: Optional[str] = None
    forecast_revenue: Optional[float] = None
    realized_revenue: Optional[float] = None
    total_revenue: Optional[float] = None

@app.get("/contacts")
async def get_contacts():
    try:
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],
            autocommit=DB_CONFIG['autocommit']
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql_select = 'SELECT * FROM contacts'
                await cursor.execute(sql_select)
                results = await cursor.fetchall()

                column_names = [desc[0] for desc in cursor.description]

                contacts = [dict(zip(column_names, row)) for row in results]

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving data from the contacts table: {e}")

    return JSONResponse(content={"contacts": contacts})

@app.post("/register")
async def register_user(user: UserCreate):
    try:
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],
            autocommit=DB_CONFIG['autocommit']
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT id FROM users WHERE email=%s', (user.email,))
                existing_user = await cursor.fetchone()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already registered")

                hashed_password = hash_password(user.password)
                await cursor.execute(
                    'INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                    (user.name, user.email, hashed_password)
                )

                await conn.commit()

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while registering the user: {e}")

    return JSONResponse(content={"message": "User registered successfully"})

@app.post("/login")
async def login(user: UserLogin):
    try:
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],
            autocommit=DB_CONFIG['autocommit']
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT password FROM users WHERE email=%s', (user.email,))
                db_password = await cursor.fetchone()
                if db_password is None or not verify_password(user.password, db_password[0]):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during login: {e}")

    return JSONResponse(content={"access_token": access_token})


@app.post('/SuiverProjet')
async def register_suiver(suiver: SuiverCreate):
    try:
        pool = await aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],
            autocommit=DB_CONFIG['autocommit']
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    'INSERT INTO suiver_projets (name, activity, contact, type_of_property, budget, area, zone, services_provided, allocated_price, closed_services, services_to_close, status, annexes, forecast_revenue, realized_revenue, total_revenue) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (suiver.name, suiver.activity, suiver.contact, suiver.type_of_property, suiver.budget, suiver.area, suiver.zone, suiver.services_provided, suiver.allocated_price, suiver.closed_services, suiver.services_to_close, suiver.status, suiver.annexes, suiver.forecast_revenue, suiver.realized_revenue, suiver.total_revenue)
                )
                await conn.commit()

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while registering the SuiverProjet: {e}")

    return JSONResponse(content={"message": "SuiverProjet registered successfully"})

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"message": "The health check is successful!"}
