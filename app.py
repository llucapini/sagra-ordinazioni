
from flask import Flask, render_template, request, redirect
import csv
import os

app = Flask(__name__)
menu = ["Lasagne", "Polenta", "Salsiccia", "Patatine", "Acqua", "Vino", "Birra"]
csv_file = "ordini.csv"

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", menu=menu, conferma=False)

@app.route("/invia_ordine", methods=["POST"])
def invia_ordine():
    tavolo = request.form.get("tavolo")
    cognome = request.form.get("cognome")
    quantita = []
    for i in range(len(menu)):
        q = int(request.form.get(f"quantita_{i}", 0))
        if q > 0:
            quantita.append(f"{menu[i]} x {q}")
    if tavolo and cognome and quantita:
        nuovo_ordine = {
            "id": genera_id(),
            "tavolo": tavolo,
            "cognome": cognome,
            "dettagli": ", ".join(quantita),
            "stato": "inserito"
        }
        scrivi_ordine(nuovo_ordine)
    return render_template("index.html", menu=menu, conferma=True)

@app.route("/cassa", methods=["GET"])
def cassa():
    ordini = [o for o in leggi_ordini() if o["stato"] == "inserito"]
    return render_template("cassa.html", ordini=ordini)

@app.route("/paga_stampa", methods=["POST"])
def paga_stampa():
    ordine_id = request.form.get("id")
    ordini = leggi_ordini()
    for ordine in ordini:
        if ordine["id"] == ordine_id:
            ordine["stato"] = "stampato"
            stampa_ordine(ordine)
            break
    salva_tutti_gli_ordini(ordini)
    return redirect("/cassa")

def leggi_ordini():
    ordini = []
    if os.path.exists(csv_file):
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ordini.append(row)
    return ordini

def scrivi_ordine(ordine):
    file_esiste = os.path.exists(csv_file)
    with open(csv_file, "a", newline='', encoding='utf-8') as f:
        fieldnames = ["id", "tavolo", "cognome", "dettagli", "stato"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_esiste:
            writer.writeheader()
        writer.writerow(ordine)

def salva_tutti_gli_ordini(ordini):
    with open(csv_file, "w", newline='', encoding='utf-8') as f:
        fieldnames = ["id", "tavolo", "cognome", "dettagli", "stato"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ordine in ordini:
            writer.writerow(ordine)

def genera_id():
    from uuid import uuid4
    return str(uuid4())

def stampa_ordine(ordine):
    with open("ordine_da_stampare.txt", "w", encoding="utf-8") as f:
        f.write(f"Ordine - Tavolo {ordine['tavolo']} - {ordine['cognome']}\n")
        f.write(ordine["dettagli"])
    try:
        import os
        os.startfile("ordine_da_stampare.txt", "print")
    except:
        print("Stampa non riuscita o non supportata su questo sistema.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
