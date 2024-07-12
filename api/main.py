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
from typing import Optional, Union, Dict, Any

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

def create_hmac_token(data: Dict[str, Any]) -> str:
    """Create an HMAC token using the SECRET_KEY."""
    message = str(data).encode()
    return hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
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
    Type_de_bien: Optional[str]
    Action_commerciale: Optional[str]
    Nom_et_Prénom: Optional[str]
    Zone: Optional[str]
    Adresse: Optional[str]
    Superficie: Optional[Union[str, int, float]]
    Descriptif_Comp: Optional[str]
    Contact: Optional[str]
    Prix_unitaire_M2: Optional[Union[str, int, float]]
    Prix_de_vente: Optional[Union[str, int, float]]
    Prix_de_location: Optional[Union[str, int, float]]
    Disponibilité: Optional[str]
    Remarque: Optional[str]
    Date_premier_contact: Optional[str]
    Visite: Optional[str]
    Fiche_identification_du_bien: Optional[str]
    Fiche_de_renseignement: Optional[str]
    Localisation: Optional[str]
    ID_identification: Optional[str]
    Id_Renseignement: Optional[str]

    class Config:
        orm_mode = True

def convert_date(date_str: str) -> str:
    try:
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%Y/%m/%d')
    except ValueError:
        raise ValueError(f"Incorrect date format: {date_str}")



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
                user_id = cursor.lastrowid

                default_role_id = 1  # Assuming a default role ID for new users
                await cursor.execute(
                    'INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)',
                    (user_id, default_role_id)
                )

                await conn.commit()

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while registering the user: {e}")
    finally:
        pool.close()
        await pool.wait_closed()

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

                await cursor.execute('''
                    SELECT u.id, u.name, u.email, r.name as role
                    FROM users u
                    JOIN user_roles ur ON u.id = ur.user_id
                    JOIN roles r ON ur.role_id = r.id
                    WHERE u.email = %s
                ''', (user.email,))
                user_data = await cursor.fetchone()

                if user_data is None:
                    raise HTTPException(status_code=404, detail="User not found")

                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(data={"sub": user_data[2], "role": user_data[3]}, expires_delta=access_token_expires)

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during login: {e}")
    finally:
        pool.close()
        await pool.wait_closed()

    return JSONResponse(content={"access_token": access_token, "token_type": "bearer", "user": {"id": user_data[0], "name": user_data[1], "email": user_data[2], "role": user_data[3]}})



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
    cleaned_value = re.sub(r'[^\d.]', '', budget_str)
    try:
        return float(cleaned_value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid budget value: {budget_str}")

@app.post('/objectImport')
async def object_import(suivers: List[SuiverCreate]):
    try:
        async with aiomysql.create_pool(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            ssl=DB_CONFIG['ssl'],
            autocommit=DB_CONFIG['autocommit']
        ) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    values = []
                    for s in suivers:
                        s.contact = str(s.contact) if s.contact is not None else None
                        
                        if s.budget:
                            s.budget = str(s.budget)  
                            s.budget = clean_budget(s.budget) 


                        values.append((
                            s.representant, s.nom, s.mode_retour, s.activite, s.contact,
                            s.type_bien, s.action, s.budget, s.superficie, s.zone,
                            s.type_accompagnement, s.services_clotures,
                            s.services_a_cloturer, s.ok_nok, s.ca_previsionnel,
                            s.ca_realise, s.status,
                            convert_date(s.created_date), convert_date(s.update_date)
                        ))

                    await cursor.executemany(
                        '''
                        INSERT INTO project_tracking (
                            representant, nom, mode_retour, activite, contact, type_bien, action, 
                            budget, superficie, zone, type_accompagnement, services_clotures, 
                            services_a_cloturer, ok_nok, ca_previsionnel, ca_realise, 
                            status, created_date, update_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''',
                        values
                    )
                    await conn.commit()

    except Exception as e:
        logging.error(f"Error during database operation: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while importing the data: {e}")

    return {"message": "Projects registered successfully"}


@app.post('/basedonneImport')
async def basedonne_import(basedonnes: List[BasedonneCreate]):
    try:
        async with aiomysql.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    values = []
                    for index, b in enumerate(basedonnes, start=1):
                        try:
                            if b.Date_premier_contact:
                                b.Date_premier_contact = convert_date(b.Date_premier_contact)
                            else:
                                b.Date_premier_contact = None 
                           
                            superficie = float(b.Superficie) if b.Superficie is not None else None
                            
                            try:
                                prix_m2 = decimal.Decimal(b.Prix_unitaire_M2) if b.Prix_unitaire_M2 is not None else None
                                prix_vent = decimal.Decimal(b.Prix_de_vente) if b.Prix_de_vente is not None else None
                                prix_location = decimal.Decimal(b.Prix_de_location) if b.Prix_de_location is not None else None
                                
                                max_decimal = decimal.Decimal('9999999.99') 
                                prix_m2 = min(prix_m2, max_decimal) if prix_m2 is not None else None
                                prix_vent = min(prix_vent, max_decimal) if prix_vent is not None else None
                                prix_location = min(prix_location, max_decimal) if prix_location is not None else None
                            except decimal.InvalidOperation:
                                logging.warning(f"Invalid numeric value in row {index}. Setting to None.")
                                prix_m2, prix_vent, prix_location = None, None, None

                            values.append((
                                b.Type_de_bien, b.Action_commerciale, b.Nom_et_Prénom, b.Zone, b.Adresse,
                                superficie, b.Descriptif_Comp, b.Contact,
                                prix_m2, prix_vent, prix_location,
                                b.Disponibilité, b.Remarque, b.Date_premier_contact, b.Visite,
                                b.Fiche_identification_du_bien, b.Fiche_de_renseignement,
                                b.Localisation, b.ID_identification, b.Id_Renseignement
                            ))
                        except ValueError as ve:
                            logging.error(f"Error parsing fields in row {index}: {ve}. Skipping entry.")
                            continue
                    if values:
                        await cursor.executemany(
                            '''
                            INSERT INTO Basedonne (
                                type_bien, action_commercial, nom_prenom, zone, adresse, superficie,
                                descriptif_composition, contact, prix_m2, prix_vent, prix_location,
                                disponabilite, remarque, date_premiere_contact, visite,
                                Fiche_identification_bien, Fiche_de_renseignement, Localisation,
                                ID_identification, Id_Renseignement
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''',
                            values
                        )
                        await conn.commit()
    except Exception as e:
        logging.error(f"Error during database operation: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while importing basedonne data: {e}")
    return {"message": "Basedonne data imported successfully"}


@app.post('/basedonneInsert')
async def basedonne_insert_single(basedonne: BasedonneCreate):
    try:
        async with aiomysql.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    try:
                        if basedonne.Date_premier_contact:
                            basedonne.Date_premier_contact = convert_date(basedonne.Date_premier_contact)
                        else:
                            basedonne.Date_premier_contact = None 
                       
                        superficie = float(basedonne.Superficie) if basedonne.Superficie is not None else None
                        
                        try:
                            prix_m2 = decimal.Decimal(basedonne.Prix_unitaire_M2) if basedonne.Prix_unitaire_M2 is not None else None
                            prix_vent = decimal.Decimal(basedonne.Prix_de_vente) if basedonne.Prix_de_vente is not None else None
                            prix_location = decimal.Decimal(basedonne.Prix_de_location) if basedonne.Prix_de_location is not None else None
                            
                            max_decimal = decimal.Decimal('9999999.99') 
                            prix_m2 = min(prix_m2, max_decimal) if prix_m2 is not None else None
                            prix_vent = min(prix_vent, max_decimal) if prix_vent is not None else None
                            prix_location = min(prix_location, max_decimal) if prix_location is not None else None
                        except decimal.InvalidOperation:
                            logging.warning(f"Invalid numeric value. Setting to None.")
                            prix_m2, prix_vent, prix_location = None, None, None

                        await cursor.execute(
                            '''
                            INSERT INTO Basedonne (
                                type_bien, action_commercial, nom_prenom, zone, adresse, superficie,
                                descriptif_composition, contact, prix_m2, prix_vent, prix_location,
                                disponabilite, remarque, date_premiere_contact, visite,
                                Fiche_identification_bien, Fiche_de_renseignement, Localisation,
                                ID_identification, Id_Renseignement
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''',
                            (
                                basedonne.Type_de_bien, basedonne.Action_commerciale, basedonne.Nom_et_Prénom,
                                basedonne.Zone, basedonne.Adresse, superficie, basedonne.Descriptif_Comp,
                                basedonne.Contact, prix_m2, prix_vent, prix_location, basedonne.Disponibilité,
                                basedonne.Remarque, basedonne.Date_premier_contact, basedonne.Visite,
                                basedonne.Fiche_identification_du_bien, basedonne.Fiche_de_renseignement,
                                basedonne.Localisation, basedonne.ID_identification, basedonne.Id_Renseignement
                            )
                        )
                        await conn.commit()
                    except ValueError as ve:
                        logging.error(f"Error parsing fields: {ve}")
                        raise HTTPException(status_code=400, detail=f"Invalid data format: {ve}")
    except Exception as e:
        logging.error(f"Error during database operation: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while inserting basedonne data: {e}")
    return {"message": "Basedonne data inserted successfully"}


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
