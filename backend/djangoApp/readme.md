# 설명

## 실행

```cmd
pip freeze > requirements.txt

pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
```

```cmd
uvicorn djangoApp.asgi:application --host 0.0.0.0 --port 8000 --reload --log-level debug --access-log
```

```cmd
python manage.py runserver 0.0.0.0:8000
```
