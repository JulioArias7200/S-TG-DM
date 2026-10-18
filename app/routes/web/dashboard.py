# -*- coding: utf-8 -*-
"""
Controlador de vistas web para el dashboard de analítica y telemetría.
"""
from flask import render_template
from app.routes.web import web_bp

@web_bp.route("/")
@web_bp.route("/dashboard")
def dashboard_view():
    """
    Renderiza el monitor ejecutivo de sentimiento y conversaciones.
    Usa el layout y distribución aprobados de template.html con soporte Dark/Light.
    """
    return render_template("dashboard/index.html")
