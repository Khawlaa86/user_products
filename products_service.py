from fastapi import FastAPI, HTTPException
import redis
import asyncpg
import json
import asyncio
import logging
import subprocess
import os
import time
from contextlib import asynccontextmanager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6380

# Configuration PostgreSQL
DATABASE_URL = "postgresql://postgres:khoukha@localhost/products_db"

# Variable globale pour stocker la tâche de traitement
process_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrer la boucle de traitement Redis au démarrage
    global process_task
    process_task = asyncio.create_task(process_requests())
    yield
    # Arrêter la boucle de traitement Redis à l'arrêt
    if process_task:
        process_task.cancel()
        try:
            await process_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

# Initialisation du client Redis
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    redis_client.ping()  # Test de connexion
    logger.info("Connected to Redis successfully")
    USE_REDIS = True
except Exception as e:
    logger.warning(f"Could not connect to Redis: {str(e)}. Using fallback mode.")
    USE_REDIS = False

# Configuration PostgreSQL
DATABASE_URL = "postgresql://postgres:khoukha@localhost/products_db"

async def get_db_connection():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Products service is running"}

@app.get("/products/{user_id}")
async def get_products(user_id: int):
    logger.info(f"Fetching products for user ID: {user_id}")
    try:
        conn = await get_db_connection()
        products = await conn.fetch("SELECT * FROM products WHERE user_id = $1", user_id)
        await conn.close()
        return [dict(p) for p in products]
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_requests():
    logger.info("Products service started and waiting for requests")
    while True:
        try:
            if USE_REDIS:
                # Attendre une demande de produits
                request = redis_client.blpop("product_requests", timeout=1)
                if request:
                    request_data = json.loads(request[1])
                    user_id = request_data.get("user_id")
                    logger.info(f"Processing product request for user ID: {user_id}")
                    
                    try:
                        # Récupérer les produits depuis PostgreSQL
                        conn = await get_db_connection()
                        products = await conn.fetch("SELECT * FROM products WHERE user_id = $1", user_id)
                        await conn.close()
                        
                        # Convertir les produits en format JSON avec conversion des décimales
                        products_json = []
                        for product in products:
                            product_dict = {}
                            for key, value in dict(product).items():
                                # Convertir les valeurs décimales en float
                                if hasattr(value, 'to_eng_string'):  # Vérifie si c'est un Decimal
                                    try:
                                        product_dict[key] = float(value)
                                    except:
                                        product_dict[key] = str(value)
                                elif value is None:
                                    product_dict[key] = None
                                else:
                                    product_dict[key] = value
                            products_json.append(product_dict)
                        
                        logger.info(f"Found {len(products_json)} products for user {user_id}")
                        logger.info(f"Products data: {products_json}")
                        
                        # Publier la réponse dans Redis
                        redis_client.lpush(f"user:{user_id}:products", json.dumps(products_json))
                        logger.info(f"Sent products to Redis for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error processing products for user {user_id}: {str(e)}")
                        # En cas d'erreur, envoyer une liste vide
                        redis_client.lpush(f"user:{user_id}:products", json.dumps([]))
            
            # Petite pause pour éviter de surcharger le CPU
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in process_requests: {str(e)}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    logger.info("Starting products service...")
    asyncio.run(process_requests()) 