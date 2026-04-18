from passlib.context import CryptContext

from src.logger.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
       Hashes a plain text password using bcrypt algorithm.

       Args:
           password (str): The plain text password to hash.

       Returns:
           str: A securely hashed password.
       """
    logger.debug("Hashing password")
    hashed_password = pwd_context.hash(password)
    logger.debug("Password successfully hashed")
    return hashed_password


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a plain text password against a hashed password.

    Args:
        password (str): The plain text password to verify.
        hashed (str): The hashed password stored in the database.

    Returns:
        bool: True if the password matches the hash, otherwise False.
    """
    logger.debug("Verifying password against stored hash")
    try:
        result = pwd_context.verify(password, hashed)
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False
