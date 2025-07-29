# 설명

## env

- python 3.11.2

```cmd
pip install pip-chill
pip-chill > requirements.txt

pip freeze > requirements.txt

pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
```

## run server

```cmd
uvicorn djangoApp.asgi:application --host 0.0.0.0 --port 8000 --reload --log-level debug --access-log
```

```cmd
python manage.py runserver 0.0.0.0:8000
```
