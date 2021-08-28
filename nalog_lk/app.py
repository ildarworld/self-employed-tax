from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import logging
import os
import random
import string
from typing import Optional, Type
from types import TracebackType

import aiohttp
import asyncio
import dateutil.parser
import pytz



logging.basicConfig(level=os.getenv("LOG_LEVEL", logging.DEBUG))
logger = logging.getLogger(__name__)


SOURCE_DEVICE_ID_LENGTH = 21
MOSCOW_TIME_ZONE = pytz.timezone("Europe/Moscow")


class SelfEmplyedTax:

    _API_URL = "https://lknpd.nalog.ru/api/v1/"
    TOKEN_GATHER_URL = _API_URL + "auth/lkfl"
    ADD_INCOME_URL = _API_URL + "income"

    HEADERS = {
        'pragma': 'no-cache',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Authorization': '',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        'Origin': 'https://lknpd.nalog.ru',
        'Referer': 'https://lknpd.nalog.ru/auth/login',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
        'Content-Type': 'application/json'
    }


    def __init__(self, user_name: str, password: str):
        self.user_name = user_name
        self.password = password
        self._client = aiohttp.ClientSession(raise_for_status=True)
        self._token: str = None
        self._token_expires_in: datetime = None

    @property
    def token(self):
        return self._token

    async def close(self):
        return await self._client.close()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        await self.close()
        return None

    def _get_source_device_id(self)->str:
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(SOURCE_DEVICE_ID_LENGTH))

    def _get_token_payload(self):
        return {
            "username": self.user_name,
            "password": self.password,
            "deviceInfo": {
                "sourceDeviceId": self._get_source_device_id(),
                "sourceType": "WEB",
                "appVersion": "1.0.0",
                "metaDetails": {
                    "userAgent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                        " (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
                    )
                }
            }
        }
    
    def _get_authorized_header(self):
        headers = self.HEADERS.copy()
        headers["Authorization"] = "Bearer " + self._token
        return headers

    def _get_income_item_payload(self, name: str, amount: Decimal, qty: int, income_date: datetime = None):

        services = list()
        return dict(
            paymentType= 'CASH',
            ignoreMaxTotalIncomeRestriction=False,
            client=dict(contactPhone= None, displayName= None, incomeType= 'FROM_INDIVIDUAL', inn= None ),
            requestTime= datetime.utcnow().astimezone(MOSCOW_TIME_ZONE).isoformat(),
            operationTime=income_date,
            services=[
                dict(
                    name=name, # Предоставление информационных услуг
                    amount=amount,
                    quantity=qty
                ),
            ],
            totalAmount= amount * qty
        )

    async def get_token(self):
        async with self._client.request(
            method="post",
            url=self.TOKEN_GATHER_URL,
            headers=self.HEADERS,
            json=self._get_token_payload()
        ) as resp:
            ret = await resp.json()
            self._token = ret["token"]
            self._token_expires_in = dateutil.parser.isoparse(ret["tokenExpireIn"])
        return self._token

    async def register_income_from_individual(self, name: str, amount: Decimal, qty: int, income_date: datetime = None)->str:
        if not self._token:
            raise ValueError("Token wasn't get")
        if self._token_expires_in < datetime.now(timezone.utc):
            self.get_token()

        income_date = income_date or (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        payload = self._get_income_item_payload(name, amount, qty, income_date)
        try:
            async with self._client.request(
                method="post",
                url=self.ADD_INCOME_URL,
                headers=self._get_authorized_header(),
                json=payload
            ) as resp:
                response = await resp.json()
                return response["approvedReceiptUuid"]
        except KeyError:
            raise KeyError("Item add request exception")
        except aiohttp.ClientResponseError as ex:
            logger.info(str(ex))
            raise ex
