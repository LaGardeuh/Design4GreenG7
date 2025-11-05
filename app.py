from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    # Affiche ton index.html
    return render_template("index.html")

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    text = data.get("textToSum", "")

    # Pour le moment on renvoie un faux résumé
    # (tu mettras ton vrai modèle plus tard)
    summary = "Résumé de test pour : " + text[:30]

    return jsonify({
        "summary": summary
    })

if __name__ == "__main__":
    app.run(debug=True)