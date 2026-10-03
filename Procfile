web: python akaza.py
web: gunicorn akaza:server --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
