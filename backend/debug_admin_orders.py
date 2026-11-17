import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
app = create_app()
with app.app_context():
    from services import admin_service
    from flask import Flask
    with app.test_request_context():
        try:
            items, pag = admin_service.list_orders_admin({"status": ""}, page=1, per_page=10)
            print("OK", len(items))
        except Exception:
            traceback.print_exc()
