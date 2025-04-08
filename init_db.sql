-- Connexion à la base de données users_db
\c users_db

-- Création de la table users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Insertion des utilisateurs de test
INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Johnson', 'bob@example.com')
ON CONFLICT (email) DO NOTHING;

-- Connexion à la base de données products_db
\c products_db

-- Création de la table products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT
);

-- Insertion des produits de test
INSERT INTO products (user_id, name, price, description) VALUES
    (1, 'Laptop', 999.99, 'High-performance laptop'),
    (1, 'Smartphone', 699.99, 'Latest smartphone model'),
    (2, 'Tablet', 499.99, '10-inch tablet'),
    (2, 'Headphones', 199.99, 'Wireless noise-cancelling headphones'),
    (3, 'Smartwatch', 299.99, 'Fitness tracking smartwatch')
ON CONFLICT DO NOTHING; 