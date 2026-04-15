from fastapi import Response


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 дней
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="refresh_token")

