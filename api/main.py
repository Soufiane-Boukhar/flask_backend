from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import aiomysql

app = FastAPI()

DB_CONFIG = {
    'host': 'mysql-1fb82b3b-boukhar-d756.e.aivencloud.com',
    'port': 20744,
    'user': 'avnadmin',
    'password': 'AVNS_wWoRjEZRmFF5NgjGCcY',
    'db': 'defaultdb',
    'ssl': True,
}

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
            autocommit=True
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql_select = 'SELECT * FROM contacts'
                await cursor.execute(sql_select)
                results = await cursor.fetchall()
                
                column_names = [desc[0] for desc in cursor.description]
                
                contacts = [dict(zip(column_names, row)) for row in results]
                
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving data from the contacts table.")
    
    return JSONResponse(content={"contacts": contacts})

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
