# Добавление дохода самозанятого в сервсие налоговой

| Author   | version |
|----------|-------------------|
|ildarworld|0.1.0 |

Позволяет добавлять доход на проессиональную деятельность самозанятых.

## Установка зависимостей

```bash
    poetry install --no-dev
```

## Использование

### Запуск

```bash
    poetry run nalog_lk/app.py
```

### Пример использования

```Python

    se = SelfEmplyedTax(
        user_name=os.getenv("NALOG_USER_NAME"),
        password=os.getenv("NALOG_PASSWORD")
    )
    
    token = await se.get_token()
    print("Token", token)
    income_uuid = await se.register_income_from_individual(
        name="Консультация",
        amount=100.00,
        qty=1,
    )
    print("Income UUID", income_uuid)

```
