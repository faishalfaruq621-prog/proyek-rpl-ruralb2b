"""Ekstensi Flask yang dipakai bersama agar tidak terjadi circular import."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
