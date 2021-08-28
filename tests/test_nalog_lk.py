import os
import pytest

from nalog_lk import __version__
from nalog_lk import SelfEmplyedTax


def test_version():
    assert __version__ == "0.1.0"



@pytest.mark.asyncio
async def test_get_token():
     ss = SelfEmplyedTax(user_name=os.getenv("NALOG_USER_NAME"), password=os.getenv("NALOG_PASSWORD"))
     await ss.get_token()
     assert ss._token is not None
     print("TOKEN=", ss._token)@pytest.mark.asyncio
    


@pytest.mark.asyncio
async def test_get_bill_link():
     ss = SelfEmplyedTax(user_name=os.getenv("NALOG_USER_NAME"), password=os.getenv("NALOG_PASSWORD"))
     token = await ss.get_token()
     result = await ss.register_income_from_individual(name="Консультация", amount=100.00, qty=1)
     assert result is not None
     print("INCOME UUID", result)