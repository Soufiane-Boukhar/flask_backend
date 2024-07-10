from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import aiomysql
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database configuration
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
        # Create a connection pool
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
                
                # Column names
                column_names = [desc[0] for desc in cursor.description]
                
                # Convert results to list of dictionaries
                contacts = [dict(zip(column_names, row)) for row in results]
                
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving data from the contacts table: {e}")
    
    return JSONResponse(content={"contacts": contacts})

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
