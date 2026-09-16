#!/usr/bin/env python
"""
Автоматическое обновление auth-токена my.itmo.ru через Keycloak.

Как пользоваться:
1. Один раз получите свежий refresh_token из браузера (DevTools -> Application ->
   Cookies -> auth._refresh_token.itmoId, значение без "Bearer%20" и без URL-кодирования).
2. Запустите:  python itmo_auth.py bootstrap "ВАШ_REFRESH_TOKEN"
   Это создаст файл ~/.itmo_tokens.json и сразу проверит, что обмен токена работает.
3. Дальше просто импортируйте ItmoAuth в своих скриптах — access_token будет
   обновляться сам, когда истекает срок его действия.

Токены хранятся ЛОКАЛЬНО в файле с правами 600, а не в самом скрипте — это важно,
если вы когда-нибудь выложите код в git: то, что было в вашем исходном файле
(access_token + refresh_token в открытом виде), стоит считать скомпрометированным
и один раз перелогиниться в браузере, чтобы старая пара токенов перестала работать.
"""

import json
import sys
import time
from pathlib import Path

import requests

from constants import (
    TOKEN_URL,
    CLIENT_ID,
    TOKEN_FILE,
    SAFETY_MARGIN_SEC
)

class ItmoAuth:
    def __init__(self, token_file: Path = TOKEN_FILE):
        self.token_file = token_file
        self.data = self._load()

    def _load(self) -> dict:
        if not self.token_file.exists():
            raise RuntimeError(
                f"Файл с токенами не найден: {self.token_file}\n"
                "Выполните один раз: python itmo_auth.py bootstrap <refresh_token>"
            )
        return json.loads(self.token_file.read_text())

    def _save(self) -> None:
        self.token_file.write_text(json.dumps(self.data, indent=2))
        try:
            self.token_file.chmod(0o600)
        except OSError:
            pass

    def _exchange(self, grant: dict) -> None:
        resp = requests.post(TOKEN_URL, data=grant, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Keycloak отказал в обновлении токена ({resp.status_code}): {resp.text}\n"
                "Скорее всего refresh_token истёк — сделайте bootstrap заново со свежим "
                "токеном из браузера."
            )
        payload = resp.json()
        now = time.time()
        self.data = {
            "access_token": payload["access_token"],
            "refresh_token": payload["refresh_token"],
            "access_expires_at": now + payload["expires_in"] - SAFETY_MARGIN_SEC,
            "refresh_expires_at": now + payload["refresh_expires_in"] - SAFETY_MARGIN_SEC,
        }
        self._save()

    def _refresh(self) -> None:
        self._exchange({
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": self.data["refresh_token"],
        })

    def get_access_token(self) -> str:
        """Возвращает валидный access_token, обновляя его при необходимости."""
        if time.time() >= self.data.get("access_expires_at", 0):
            self._refresh()
        return self.data["access_token"]

    @classmethod
    def bootstrap(cls, refresh_token: str, token_file: Path = TOKEN_FILE) -> "ItmoAuth":
        auth = cls.__new__(cls)
        auth.token_file = token_file
        auth.data = {
            "refresh_token": refresh_token,
            "access_expires_at": 0,
            "refresh_expires_at": 0,
        }
        auth._refresh()
        return auth

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "bootstrap":
        auth = ItmoAuth.bootstrap(sys.argv[2])
        print(f"Токены сохранены в {auth.token_file}, access_token получен успешно.")
    else:
        print("Использование: python itmo_auth.py bootstrap <refresh_token>")
