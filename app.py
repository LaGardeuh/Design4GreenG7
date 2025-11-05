from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    # Affichage index.html
    return render_template("index.html")

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    text = data.get("textToSum", "")

    summary = "Résumé de test pour : " + text[:30]

    return jsonify({
        "summary": summary
    })

if __name__ == "__main__":
    app.run(debug=True)