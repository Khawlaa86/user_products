from fastapi import FastAPI, HTTPException
import redis
import asyncpg
import json
import logging
import subprocess
import os
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuration Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6380

# Configuration PostgreSQL
DATABASE_URL = "postgresql://postgres:khoukha@localhost/users_db"

# Initialisation du client Redis
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    redis_client.ping()  # Test de connexion
    logger.info("Connected to Redis successfully")
    USE_REDIS = True
except Exception as e:
    logger.warning(f"Could not connect to Redis: {str(e)}. Using fallback mode.")
    USE_REDIS = False

async def get_db_connection():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

async def get_products_from_redis(user_id: int):
    if not USE_REDIS:
        # Fallback: récupérer les produits directement depuis PostgreSQL
        try:
            conn = await get_db_connection()
            products = await conn.fetch("SELECT * FROM products WHERE user_id = $1", user_id)
            await conn.close()
            return [dict(p) for p in products]
        except Exception as e:
            logger.error(f"Error fetching products directly: {str(e)}")
            return []
    
    try:
        # Attendre un maximum de 5 secondes pour la réponse
        response = redis_client.brpop(f"user:{user_id}:products", timeout=5)
        if response:
            return json.loads(response[1])
        logger.warning(f"Timeout waiting for products for user {user_id}")
        return []
    except Exception as e:
        logger.error(f"Redis error: {str(e)}")
        return []

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Users service is running"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    logger.info(f"Fetching user with ID: {user_id}")
    
    # Récupérer l'utilisateur depuis PostgreSQL
    try:
        conn = await get_db_connection()
        logger.info(f"Connected to database, fetching user with ID: {user_id}")
        
        # Vérifier si l'utilisateur existe
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        logger.info(f"Database query result: {user}")
        
        await conn.close()
        
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convertir l'utilisateur en dictionnaire
        user_dict = dict(user)
        logger.info(f"User data: {user_dict}")
        
        if USE_REDIS:
            # Publier une demande de produits dans Redis
            redis_client.lpush("product_requests", json.dumps({"user_id": user_id}))
            logger.info(f"Published product request for user ID: {user_id}")
        
        # Attendre la réponse des produits
        products = await get_products_from_redis(user_id)
        logger.info(f"Products for user {user_id}: {products}")
        
        return {"id": user_dict["id"], "name": user_dict["name"], "email": user_dict.get("email", ""), "products": products}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 