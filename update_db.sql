-- Connexion à la base de données users_db
\c users_db

-- Ajout de la colonne email à la table users
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(100) UNIQUE;

-- Mise à jour des utilisateurs de test
INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Johnson', 'bob@example.com')
ON CONFLICT DO NOTHING;

-- Connexion à la base de données products_db
\c products_db

-- Ajout des colonnes manquantes à la table products
ALTER TABLE products ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS description TEXT;

-- Mise à jour des produits de test
INSERT INTO products (user_id, name, price, description) VALUES
    (1, 'Laptop', 999.99, 'High-performance laptop'),
    (1, 'Smartphone', 699.99, 'Latest smartphone model'),
    (2, 'Tablet', 499.99, '10-inch tablet'),
    (2, 'Headphones', 199.99, 'Wireless noise-cancelling headphones'),
    (3, 'Smartwatch', 299.99, 'Fitness tracking smartwatch')
ON CONFLICT DO NOTHING; 