from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from datetime import datetime

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Ordine(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tavolo = db.Column(db.String, nullable=False)
    cognome = db.Column(db.String, nullable=False)
    dettagli = db.Column(db.Text, nullable=False)
    stato = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Portata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    disponibile = db.Column(db.Boolean, default=True)

@app.route("/", methods=["GET"])
def index():
    portate = Portata.query.filter_by(disponibile=True).all()
    return render_template("index.html", menu=[p.nome for p in portate], conferma=False)

@app.route("/invia_ordine", methods=["POST"])
def invia_ordine():
    portate = Portata.query.filter_by(disponibile=True).all()
    menu = [p.nome for p in portate]
    tavolo = request.form.get("tavolo")
    cognome = request.form.get("cognome")
    dettagli = []
    for i in range(len(menu)):
        q = int(request.form.get(f"quantita_{i}", 0))
        if q > 0:
            dettagli.append(f"{menu[i]} x {q}")
    if tavolo and cognome and dettagli:
        ordine = Ordine(tavolo=tavolo, cognome=cognome, dettagli=", ".join(dettagli), stato="inserito")
        db.session.add(ordine)
        db.session.commit()
    return render_template("index.html", menu=menu, conferma=True)

@app.route("/cassa")
def cassa():
    ordini = Ordine.query.filter_by(stato="inserito").order_by(Ordine.timestamp.desc()).all()
    return render_template("cassa.html", ordini=ordini)

@app.route("/paga_stampa", methods=["POST"])
def paga_stampa():
    ordine_id = request.form.get("id")
    ordine = Ordine.query.get(ordine_id)
    if ordine:
        ordine.stato = "stampato"
        db.session.commit()
    return redirect("/cassa")

@app.route("/api/ordini-da-stampare")
def api_ordini_da_stampare():
    ordini = Ordine.query.filter_by(stato="stampato").all()
    return jsonify([{
        "id": o.id,
        "tavolo": o.tavolo,
        "cognome": o.cognome,
        "dettagli": o.dettagli,
        "stato": o.stato
    } for o in ordini])

@app.route("/api/conferma-stampa", methods=["POST"])
def api_conferma_stampa():
    data = request.get_json()
    ordine = Ordine.query.get(data["id"])
    if ordine:
        ordine.stato = "stampati-localmente"
        db.session.commit()
    return jsonify({"success": True})

@app.route("/menu", methods=["GET", "POST"])
def menu():
    if request.method == "POST":
        nome = request.form.get("nome")
        if nome:
            nuova = Portata(nome=nome)
            db.session.add(nuova)
            db.session.commit()
        return redirect("/menu")
    portate = Portata.query.all()
    return render_template("menu.html", portate=portate)

@app.route("/elimina_portata", methods=["POST"])
def elimina_portata():
    pid = request.form.get("id")
    portata = Portata.query.get(pid)
    if portata:
        db.session.delete(portata)
        db.session.commit()
    return redirect("/menu")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)