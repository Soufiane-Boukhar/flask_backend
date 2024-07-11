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
from typing import Optional, List
import pandas as pd
import io
import re

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

class BasedonneCreate(BaseModel):
    type_bien: Optional[str] = None
    action_commercial: Optional[str] = None
    nom_prenom: Optional[str] = None
    Zone: Optional[str] = None
    adresse: Optional[str] = None
    superficie: Optional[float] = None
    descriptif_composition: Optional[str] = None
    contact: Optional[str] = None
    prix_m2: Optional[float] = None
    prix_vent: Optional[float] = None
    prix_location: Optional[float] = None
    disponabilite: Optional[str] = None
    remarque: Optional[str] = None
    date_premiere_contact: Optional[str] = None
    visite: Optional[str] = None
    Fiche_identification_bien: Optional[str] = None
    Fiche_de_renseignement: Optional[str] = None
    Localisation: Optional[str] = None
    ID_identification: Optional[str] = None
    Id_Renseignement: Optional[str] = None


def convert_date(date_str: str) -> str:
    try:
        # Convert the date from 'DD/MM/YYYY' to 'YYYY/MM/DD'
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%Y/%m/%d')
    except ValueError:
        raise ValueError(f"Incorrect date format: {date_str}")

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




def clean_budget(budget_str: str) -> float:
    # Remove spaces and any non-numeric characters
    cleaned_value = re.sub(r'[^\d.]', '', budget_str)
    try:
        return float(cleaned_value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid budget value: {budget_str}")

@app.post('/basedonneImport')
async def object_import(suivers: list[BasedonneCreate] = Body(...)):
    try:
        # Establish database connection pool
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
                values = []
                for s in suivers:
                    values.append((
                        s.type_bien, s.action_commercial, s.nom_prenom, s.Zone, s.adresse,
                        s.superficie, s.descriptif_composition, s.contact, s.prix_m2, s.prix_vent,
                        s.prix_location, s.disponabilite, s.remarque, s.date_premiere_contact,
                        s.visite, s.Fiche_identification_bien, s.Fiche_de_renseignement, s.Localisation,
                        s.ID_identification, s.Id_Renseignement
                    ))

                # Execute the SQL INSERT statement
                await cursor.executemany(
                    '''
                    INSERT INTO Basedonne (
                        type_bien, action_commercial, nom_prenom, Zone, adresse, superficie, 
                        descriptif_composition, contact, prix_m2, prix_vent, prix_location, 
                        disponabilite, remarque, date_premiere_contact, visite, Fiche_identification_bien, 
                        Fiche_de_renseignement, Localisation, ID_identification, Id_Renseignement
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''',
                    values
                )

                # Commit the transaction to persist changes
                await conn.commit()

    except Exception as e:
        # Rollback transaction on error and raise HTTPException
        if 'conn' in locals():
            await conn.rollback()
            await conn.close()
            pool.close()
            await pool.wait_closed()
        raise HTTPException(status_code=500, detail=f"Error importing objects: {str(e)}")
    finally:
        pool.close()
        await pool.wait_closed()

    return {"message": "Objects imported successfully"}


@app.post('/basedonneImport')
async def object_import(objects: list[BasedonneModel]):
    try:
        # Establish a connection to your MySQL database
        mydb = mysql.connector.connect(
            host="your_host",
            user="your_username",
            password="your_password",
            database="your_database"
        )

        # Create a cursor object to execute SQL queries
        mycursor = mydb.cursor()

        # Construct and execute the SQL INSERT statement in a loop for each object
        for obj in objects:
            sql = """
            INSERT INTO Basedonne (
                type_bien, action_commercial, nom_prenom, Zone, adresse, superficie, 
                descriptif_composition, contact, prix_m2, prix_vent, prix_location, 
                disponabilite, remarque, date_premiere_contact, visite, Fiche_identification_bien, 
                Fiche_de_renseignement, Localisation, ID_identification, Id_Renseignement
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                obj.type_bien, obj.action_commercial, obj.nom_prenom, obj.Zone, obj.adresse,
                obj.superficie, obj.descriptif_composition, obj.contact, obj.prix_m2, obj.prix_vent,
                obj.prix_location, obj.disponabilite, obj.remarque, obj.date_premiere_contact,
                obj.visite, obj.Fiche_identification_bien, obj.Fiche_de_renseignement, obj.Localisation,
                obj.ID_identification, obj.Id_Renseignement
            )

            mycursor.execute(sql, val)

        # Commit the transaction to persist changes
        mydb.commit()

        # Close the cursor and database connection
        mycursor.close()
        mydb.close()

        return {"message": "Objects imported successfully"}

    except Exception as e:
        # Rollback transaction on error and raise HTTPException
        mydb.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing objects: {str(e)}")@app.post('/basedonneImport')
async def object_import(objects: list[BasedonneModel]):
    try:
        # Establish a connection to your MySQL database
        mydb = mysql.connector.connect(
            host="your_host",
            user="your_username",
            password="your_password",
            database="your_database"
        )

        # Create a cursor object to execute SQL queries
        mycursor = mydb.cursor()

        # Construct and execute the SQL INSERT statement in a loop for each object
        for obj in objects:
            sql = """
            INSERT INTO Basedonne (
                type_bien, action_commercial, nom_prenom, Zone, adresse, superficie, 
                descriptif_composition, contact, prix_m2, prix_vent, prix_location, 
                disponabilite, remarque, date_premiere_contact, visite, Fiche_identification_bien, 
                Fiche_de_renseignement, Localisation, ID_identification, Id_Renseignement
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                obj.type_bien, obj.action_commercial, obj.nom_prenom, obj.Zone, obj.adresse,
                obj.superficie, obj.descriptif_composition, obj.contact, obj.prix_m2, obj.prix_vent,
                obj.prix_location, obj.disponabilite, obj.remarque, obj.date_premiere_contact,
                obj.visite, obj.Fiche_identification_bien, obj.Fiche_de_renseignement, obj.Localisation,
                obj.ID_identification, obj.Id_Renseignement
            )

            mycursor.execute(sql, val)

        # Commit the transaction to persist changes
        mydb.commit()

        # Close the cursor and database connection
        mycursor.close()
        mydb.close()

        return {"message": "Objects imported successfully"}

    except Exception as e:
        # Rollback transaction on error and raise HTTPException
        mydb.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing objects: {str(e)}")


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
