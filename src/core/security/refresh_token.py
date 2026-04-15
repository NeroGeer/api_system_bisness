import uuid


def create_refresh_token():
    return str(uuid.uuid4())
