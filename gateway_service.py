from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import logging
import redis
import subprocess
import os
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Démarrer Redis s'il n'est pas déjà en cours d'exécution
def ensure_redis_running():
    try:
        # Vérifier si Redis est déjà en cours d'exécution
        redis_client = redis.Redis(host='localhost', port=6380)
        redis_client.ping()
        logger.info("Redis is already running")
        return True
    except:
        logger.info("Redis is not running, starting it...")
        try:
            # Démarrer Redis en arrière-plan avec le fichier de configuration
            redis_path = r"C:\Program Files\Redis\redis-server.exe"
            config_path = os.path.join(os.getcwd(), "redis.windows.conf")
            
            if os.path.exists(redis_path):
                subprocess.Popen([redis_path, config_path], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
                # Attendre que Redis démarre
                time.sleep(2)
                return True
            else:
                logger.error(f"Redis executable not found at {redis_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to start Redis: {str(e)}")
            return False

# S'assurer que Redis est en cours d'exécution
ensure_redis_running()

# Configuration Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6380
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    redis_client.ping()  # Test de connexion
    logger.info("Connected to Redis successfully")
    USE_REDIS = True
except Exception as e:
    logger.warning(f"Could not connect to Redis: {str(e)}. Using fallback mode.")
    USE_REDIS = False

# Configuration des services
USERS_SERVICE_URL = "http://localhost:8002"
PRODUCTS_SERVICE_URL = "http://localhost:8000"

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Gateway service is running"}

@app.get("/api/users/{user_id}")
async def get_user_data(user_id: int):
    logger.info(f"Fetching data for user ID: {user_id}")
    try:
        async with httpx.AsyncClient() as client:
            # Récupérer les données utilisateur
            logger.info(f"Requesting user data from {USERS_SERVICE_URL}/users/{user_id}")
            try:
                user_response = await client.get(f"{USERS_SERVICE_URL}/users/{user_id}", timeout=10.0)
                logger.info(f"User service response status: {user_response.status_code}")
                
                if user_response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_data = user_response.json()
                        error_detail = error_data.get("detail", "Unknown error")
                    except:
                        error_detail = user_response.text
                    
                    logger.error(f"Error from users service: {user_response.status_code} - {error_detail}")
                    raise HTTPException(status_code=user_response.status_code, detail=error_detail)
                
                user_data = user_response.json()
                logger.info(f"User data received: {user_data}")

                # Extraire les produits de la réponse du service users
                products = user_data.get("products", [])
                
                # Créer la réponse finale
                return {
                    "user": {
                        "id": user_data["id"],
                        "name": user_data["name"],
                        "email": user_data.get("email", "")
                    },
                    "products": products
                }
            except httpx.ConnectError as e:
                logger.error(f"Could not connect to users service at {USERS_SERVICE_URL}: {str(e)}")
                raise HTTPException(status_code=503, detail="Users service unavailable")
            except httpx.TimeoutException:
                logger.error(f"Timeout while connecting to users service at {USERS_SERVICE_URL}")
                raise HTTPException(status_code=504, detail="Users service timeout")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def get_home():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>User Products Management</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                    color: #2c3e50;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                .btn-primary {
                    background-color: #3498db;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                }
                .btn-primary:hover {
                    background-color: #2980b9;
                }
                .product-card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: #fff;
                    transition: transform 0.2s;
                }
                .product-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }
                .product-price {
                    color: #2ecc71;
                    font-weight: bold;
                    font-size: 1.2em;
                }
                .loading {
                    text-align: center;
                    padding: 20px;
                    display: none;
                }
                .error-message {
                    color: #e74c3c;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    background-color: #fadbd8;
                    display: none;
                }
                .user-info {
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }
                .api-docs {
                    margin-top: 40px;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>User Products Management</h1>
                    <p class="lead">Manage and view user products information</p>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label for="userId" class="form-label">User ID:</label>
                            <input type="number" id="userId" class="form-control" min="1" value="2">
                        </div>
                        <button class="btn btn-primary" onclick="fetchUserData()">Get User Data</button>
                    </div>
                </div>

                <div class="loading" id="loading">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>Loading user data...</p>
                </div>

                <div class="error-message" id="error"></div>

                <div id="result">
                    <div class="user-info" id="userInfo" style="display: none;">
                        <h2>User Information</h2>
                        <p><strong>ID:</strong> <span id="userIdDisplay"></span></p>
                        <p><strong>Name:</strong> <span id="userName"></span></p>
                        <p><strong>Email:</strong> <span id="userEmail"></span></p>
                    </div>

                    <div id="productsList">
                        <h2>Products</h2>
                        <div id="products"></div>
                    </div>
                </div>

                <div class="api-docs">
                    <h3>API Documentation</h3>
                    <p>You can also use these endpoints directly:</p>
                    <ul>
                        <li><strong>GET /api/users/{id}</strong> - Get user and products information</li>
                        <li><strong>GET /api/health</strong> - Check service health</li>
                    </ul>
                    <p>Example with Postman:</p>
                    <pre>
GET http://localhost:8003/api/users/2
Headers:
  Content-Type: application/json
                    </pre>
                </div>
            </div>

            <script>
                async function fetchUserData() {
                    const userId = document.getElementById('userId').value;
                    const resultDiv = document.getElementById('result');
                    const loadingDiv = document.getElementById('loading');
                    const errorDiv = document.getElementById('error');
                    const userInfoDiv = document.getElementById('userInfo');
                    const productsDiv = document.getElementById('products');

                    // Reset display
                    loadingDiv.style.display = 'block';
                    errorDiv.style.display = 'none';
                    userInfoDiv.style.display = 'none';
                    productsDiv.innerHTML = '';
                    
                    try {
                        const response = await fetch(`/api/users/${userId}`);
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        const data = await response.json();
                        
                        // Display user information
                        document.getElementById('userIdDisplay').textContent = data.user.id;
                        document.getElementById('userName').textContent = data.user.name;
                        document.getElementById('userEmail').textContent = data.user.email || 'No email';
                        userInfoDiv.style.display = 'block';
                        
                        // Display products
                        if (data.products.length > 0) {
                            data.products.forEach(product => {
                                const productCard = document.createElement('div');
                                productCard.className = 'product-card';
                                productCard.innerHTML = `
                                    <h3>${product.name}</h3>
                                    <p><strong>ID:</strong> ${product.id}</p>
                                    <p><strong>Price:</strong> <span class="product-price">$${product.price || 'N/A'}</span></p>
                                    <p><strong>Description:</strong> ${product.description || 'No description'}</p>
                                `;
                                productsDiv.appendChild(productCard);
                            });
                        } else {
                            productsDiv.innerHTML = '<p class="text-muted">No products found for this user.</p>';
                        }
                    } catch (error) {
                        errorDiv.style.display = 'block';
                        errorDiv.textContent = `Error: ${error.message}`;
                    } finally {
                        loadingDiv.style.display = 'none';
                    }
                }
            </script>
        </body>
    </html>
    """ 