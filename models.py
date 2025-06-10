from sqlalchemy import JSON

from __init__ import db, UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    markers = db.relationship('Marker', backref='user', lazy=True)
    routes = db.relationship('Route', backref='user', lazy=True)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    waypoints = db.Column(JSON, nullable=False)  # JSON string

class MarkerBase(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

class Marker(MarkerBase):
    __tablename__ = 'marker'
    name = db.Column(db.String(100), nullable=False)

class AvalancheMarker(MarkerBase):
    __tablename__ = 'avalanche_marker'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='avalanche_markers')