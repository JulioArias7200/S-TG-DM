# -*- coding: utf-8 -*-
"""
Punto de entrada de ejecución local de la aplicación Flask.
Ejecutar con: python run.py
"""
import os
from app import create_app

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=(env == "development"))
