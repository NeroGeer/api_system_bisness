from dotenv import load_dotenv
import os


# Загрузка переменных из .env
load_dotenv()

DB_URL = os.getenv("APP_CONFIG__DB__URL")
if not DB_URL:
    raise ValueError("APP_CONFIG__DB__URL is not set in .env")

REDIS_URL = os.getenv("APP_CONFIG__REDIS_URL")
REDIS_PORT = os.getenv("APP_CONFIG__REDIS_PORT")

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif"
}

STATIC_FOLDER = "/usr/share/nginx/static"
IMAGES_FOLDER = os.path.join(STATIC_FOLDER, "images")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_EXPIRE_MIN = os.getenv("JWT_ACCESS_EXPIRE_MIN")
JWT_REFRESH_EXPIRE_DAYS = os.getenv("JWT_REFRESH_EXPIRE_DAYS")
BASE_USER_ROLE_NAME = os.getenv("BASE_USER_ROLE_NAME")
DEFAULT_ROLE_ID = int(os.getenv("DEFAULT_ROLE_ID"))
