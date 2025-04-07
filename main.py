from flask import Flask, jsonify, request
import mysql.connector
import hashlib
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="mh285989-001.eu.clouddb.ovh.net",
        port=35693,
        user="bts",
        password="Harris91270",
        database="MuslimVibe"
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ▶️ INSCRIPTION
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (username, email, hash_password(password)))
        conn.commit()
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Cet email ou ce pseudo existe déjà"}), 400
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Inscription réussie"}), 201

# ▶️ CONNEXION
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, username, email, is_active FROM users
        WHERE email = %s AND password_hash = %s
    """, (email, hash_password(password)))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Identifiants invalides"}), 401

    if not user["is_active"]:
        return jsonify({"error": "Compte inactif"}), 403

    # Mise à jour de la dernière connexion
    cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.now(), user["id"]))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Connexion réussie",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    })
