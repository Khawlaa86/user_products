import asyncpg
import asyncio
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des bases de données
USERS_DB_URL = "postgresql://postgres:khawla@localhost/users_db"
PRODUCTS_DB_URL = "postgresql://postgres:khawla@localhost/products_db"

async def init_users_db():
    try:
        # Connexion à la base de données users
        conn = await asyncpg.connect(USERS_DB_URL)
        
        # Création de la table users si elle n'existe pas
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            )
        ''')
        
        # Insertion des utilisateurs de test
        await conn.execute('''
            INSERT INTO users (name, email) VALUES
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Bob Johnson', 'bob@example.com')
            ON CONFLICT (email) DO NOTHING
        ''')
        
        logger.info("Users database initialized successfully")
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error initializing users database: {str(e)}")
        raise

async def init_products_db():
    try:
        # Connexion à la base de données products
        conn = await asyncpg.connect(PRODUCTS_DB_URL)
        
        # Création de la table products si elle n'existe pas
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                description TEXT
            )
        ''')
        
        # Insertion des produits de test
        await conn.execute('''
            INSERT INTO products (user_id, name, price, description) VALUES
            (1, 'Laptop', 999.99, 'High-performance laptop'),
            (1, 'Smartphone', 699.99, 'Latest smartphone model'),
            (2, 'Tablet', 499.99, '10-inch tablet'),
            (2, 'Headphones', 199.99, 'Wireless noise-cancelling headphones'),
            (3, 'Smartwatch', 299.99, 'Fitness tracking smartwatch')
            ON CONFLICT DO NOTHING
        ''')
        
        logger.info("Products database initialized successfully")
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error initializing products database: {str(e)}")
        raise

async def main():
    logger.info("Starting database initialization...")
    await init_users_db()
    await init_products_db()
    logger.info("Database initialization completed")

if __name__ == "__main__":
    asyncio.run(main()) 