import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de la base de datos
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'gimnasio'),
        'port': int(os.getenv('DB_PORT', 3306))
    }
    
    # Configuración de Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-super-secreta-cambiar-en-produccion')
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # Configuración de la aplicación
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))