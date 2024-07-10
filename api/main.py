from fastapi import FastAPI, File, UploadFile, HTTPException
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
import pandas as pd
import io

app = FastAPI()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    representant: Optional[str] = None
    nom: Optional[str] = None
    mode_retour: Optional[str] = None
    activite: Optional[str] = None
    contact: Optional[str] = None
    type_bien: Optional[str] = None
    action: Optional[str] = None
    budget: Optional[float] = None
    superficie: Optional[float] = None
    zone: Optional[str] = None
    type_accompagnement: Optional[str] = None
    prix_alloue: Optional[float] = None
    services_clotures: Optional[str] = None
    services_a_cloturer: Optional[str] = None
    ok_nok: Optional[str] = None
    annexes: Optional[str] = None
    ca_previsionnel: Optional[float] = None
    ca_realise: Optional[float] = None
    total_ca: Optional[float] = None
    status: Optional[str] = None
    created_date: Optional[str] = None
    update_date: Optional[str] = None

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
                    '''
                    INSERT INTO project_tracking (
                        representant, nom, mode_retour, activite, contact, type_bien, action, 
                        budget, superficie, zone, type_accompagnement, prix_alloue, services_clotures, 
                        services_a_cloturer, ok_nok, annexes, ca_previsionnel, ca_realise, 
                        total_ca, status, created_date, update_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        suiver.representant, suiver.nom, suiver.mode_retour, suiver.activite, suiver.contact,
                        suiver.type_bien, suiver.action, suiver.budget, suiver.superficie, suiver.zone,
                        suiver.type_accompagnement, suiver.prix_alloue, suiver.services_clotures,
                        suiver.services_a_cloturer, suiver.ok_nok, suiver.annexes, suiver.ca_previsionnel,
                        suiver.ca_realise, suiver.total_ca, suiver.status, suiver.created_date, suiver.update_date
                    )
                )

                await conn.commit()

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while registering the project: {e}")

    return JSONResponse(content={"message": "Project registered successfully"})


@app.post('/import-excel')
async def import_excel(file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="File is required")

        # Read the file into a Pandas DataFrame
        file_content = await file.read()  # Read file content asynchronously
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')

        # Normalize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        # Replace NaN values with None
        df = df.applymap(lambda x: None if pd.isna(x) else x)

        # Convert DataFrame to JSON
        data_json = df.to_dict(orient='records')

        # Debug information
        debug_info = {
            "null_counts": df.isnull().sum().to_dict(),
            "data_sample": df.head().to_dict(orient='records')
        }

        # Example: Log data being inserted
        logging.debug(f"Data to be inserted: {data_json}")

        # Simulate database insertion to help diagnose issues
        pool = await aiomysql.create_pool(
            host='localhost',
            port=3306,
            user='user',
            password='password',
            db='database',
            ssl=None,
            autocommit=True
        )

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for row in df.itertuples(index=False):
                    # Prepare the data
                    suiver_data = {
                        "representant": getattr(row, "representant", None),
                        "nom": getattr(row, "nom", None),
                        "mode_retour": getattr(row, "mode_retour", None),
                        "activite": getattr(row, "activite", None),
                        "contact": getattr(row, "contact", None),
                        "type_bien": getattr(row, "type_bien", None),
                        "action": getattr(row, "action", None),
                        "budget": getattr(row, "budget", None),
                        "superficie": getattr(row, "superficie", None),
                        "zone": getattr(row, "zone", None),
                        "type_accompagnement": getattr(row, "type_accompagnement", None),
                        "prix_alloue": getattr(row, "prix_alloue", None),
                        "services_clotures": getattr(row, "services_clotures", None),
                        "services_a_cloturer": getattr(row, "services_a_cloturer", None),
                        "ok_nok": getattr(row, "ok_nok", None),
                        "annexes": getattr(row, "annexes", None),
                        "ca_previsionnel": getattr(row, "ca_previsionnel", None),
                        "ca_realise": getattr(row, "ca_realise", None),
                        "total_ca": getattr(row, "total_ca", None),
                        "status": getattr(row, "status", None),
                        "created_date": getattr(row, "created_date", None),
                        "update_date": getattr(row, "update_date", None),
                    }

                    # Log prepared data for debugging
                    logging.debug(f"Prepared data for insertion: {suiver_data}")

                    try:
                        # Check for any remaining NaN values in prepared data
                        if any(value is pd.NaT or pd.isna(value) for value in suiver_data.values()):
                            raise ValueError("Prepared data contains NaN or NaT values.")

                        # Insert the data into the database
                        await cursor.execute(
                            '''
                            INSERT INTO project_tracking (
                                representant, nom, mode_retour, activite, contact, type_bien, action, 
                                budget, superficie, zone, type_accompagnement, prix_alloue, services_clotures, 
                                services_a_cloturer, ok_nok, annexes, ca_previsionnel, ca_realise, 
                                total_ca, status, created_date, update_date
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''',
                            (
                                suiver_data.get("representant"), suiver_data.get("nom"), suiver_data.get("mode_retour"), suiver_data.get("activite"), suiver_data.get("contact"),
                                suiver_data.get("type_bien"), suiver_data.get("action"), suiver_data.get("budget"), suiver_data.get("superficie"), suiver_data.get("zone"),
                                suiver_data.get("type_accompagnement"), suiver_data.get("prix_alloue"), suiver_data.get("services_clotures"),
                                suiver_data.get("services_a_cloturer"), suiver_data.get("ok_nok"), suiver_data.get("annexes"), suiver_data.get("ca_previsionnel"),
                                suiver_data.get("ca_realise"), suiver_data.get("total_ca"), suiver_data.get("status"), suiver_data.get("created_date"), suiver_data.get("update_date")
                            )
                        )
                    except ValueError as ve:
                        logging.error(f"Data validation error occurred: {ve}")
                        raise HTTPException(status_code=400, detail=f"Data validation error: {ve}")
                    except Exception as db_err:
                        logging.error(f"Database error occurred: {db_err}")
                        raise HTTPException(status_code=500, detail=f"An error occurred while inserting data into the database: {db_err}")

                await conn.commit()

    except Exception as e:
        # Log general errors
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while importing the Excel file: {e}")

    return JSONResponse(content={
        "message": "Excel file imported successfully",
        "data": data_json,
        "debug_info": debug_info
    })

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
