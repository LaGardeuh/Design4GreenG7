import os

from flask import Flask, request, jsonify, send_from_directory
from modules.generate_summary import generate_summary

# Configuration Flask : sert le build SvelteKit
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "web", "build"),
    static_url_path="/"
)

AVAILABLE_MODELS = {
    "xsum": "./models/pythia70m-french-mlsum-adapted/",
    "mlsum": "./models/pythia70m-xsum-100p-trained"
}


@app.route("/")
def home():
    """Sert le frontend SvelteKit compilé"""
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(404)
def not_found(e):
    """Redirige les routes SvelteKit vers index.html"""
    return send_from_directory(app.static_folder, "index.html")

# === API /summarize ===
@app.route("/summarize", methods=["POST"])
def summarize():
    """Route pour générer un résumé de texte"""
    data = request.json
    text = data.get("textToSum", "")
    optimized = data.get("optimized", True)

    # Validation : vérifier que le texte n'est pas vide
    if not text or len(text.strip()) == 0:
        return jsonify({"error": "Le texte à résumer ne peut pas être vide", "success": False}), 400
    if len(text) > 4000:
        return jsonify({
            "error": "Le texte ne doit pas dépasser 4000 caractères",
            "success": False,
            "received_length": len(text)
        }), 400

    try:
        # Génération du résumé avec le paramètre optimized choisi
        model_folder = AVAILABLE_MODELS["mlsum"]
        result = generate_summary(text, optimized=optimized, model_folder=model_folder)

        # Extraction des résultats (latence déjà en ms)
        summary = result['summary']
        word_count = result['word_count']
        latency = result['latency']  # Déjà en millisecondes
        energy = result['energy_consumed']

        # Retour de la réponse JSON bien formatée
        return jsonify({
            "success": True,
            "mode": "Optimisé" if optimized else "Non-optimisé",
            "results": {
                "summary": summary,
                "word_count": word_count,
                "latency": latency,
                "energy_wh": energy
            },
            "metadata": {
                "input_length": len(text),
                "optimization_enabled": optimized
            }
        }), 200  # Code HTTP 200 : Success

    except Exception as e:
        # Gestion des erreurs pendant la génération
        return jsonify({
            "error": f"Erreur lors de la génération du résumé : {str(e)}",
            "success": False
        }), 500  # Code HTTP 500 : Internal Server Error


@app.route("/compare", methods=["POST"])
def compare():
    """
    Route pour comparer les deux versions (optimisée vs non-optimisée).
    Retourne aussi les deux latences brutes en millisecondes.
    """

    data = request.json
    text = data.get("textToSum", "")

    # Validation
    if not text or len(text.strip()) == 0:
        return jsonify({
            "error": "Le texte à résumer ne peut pas être vide",
            "success": False
        }), 400

    if len(text) > 4000:
        return jsonify({
            "error": "Le texte ne doit pas dépasser 4000 caractères",
            "success": False
        }), 400

    try:
        model_folder = AVAILABLE_MODELS["mlsum"]

        # Génération avec version NON OPTIMISÉE
        result_non_opt = generate_summary(text, optimized=False, model_folder=model_folder)

        # Génération avec version OPTIMISÉE
        result_opt = generate_summary(text, optimized=True, model_folder=model_folder)

        # Calcul des gains
        latency_gain = round(
            ((result_non_opt["latency"] - result_opt["latency"]) / result_non_opt["latency"]) * 100,
            2
        )
        energy_gain = round(
            ((result_non_opt["energy_consumed"] - result_opt["energy_consumed"]) /
             result_non_opt["energy_consumed"]) * 100,
            2
        ) if result_non_opt["energy_consumed"] > 0 else 0

        # === 🆕 Ajout explicite des deux latences dans la réponse ===
        latency_non_opt = result_non_opt["latency"]
        latency_opt = result_opt["latency"]

        return jsonify({
            "success": True,
            "comparison": {
                "non_optimized": {
                    "summary": result_non_opt["summary"],
                    "word_count": result_non_opt["word_count"],
                    "latency": latency_non_opt,
                    "energy_wh": result_non_opt["energy_consumed"]
                },
                "optimized": {
                    "summary": result_opt["summary"],
                    "word_count": result_opt["word_count"],
                    "latency": latency_opt,
                    "energy_wh": result_opt["energy_consumed"]
                },
                "performance_gains": {
                    "latency_reduction_percent": latency_gain,
                    "energy_reduction_percent": energy_gain,
                    "latency_saved_ms": round(latency_non_opt - latency_opt, 2),
                    "energy_saved_wh": round(
                        result_non_opt["energy_consumed"] - result_opt["energy_consumed"], 6
                    ),
                    "latency_non_optimized_ms": latency_non_opt,  # 🆕 ajouté
                    "latency_optimized_ms": latency_opt           # 🆕 ajouté
                }
            },
            "metadata": {"input_length": len(text)}
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Erreur lors de la comparaison : {str(e)}",
            "success": False
        }), 500


if __name__ == "__main__":
    # Lancement du serveur Flask en mode debug
    # debug=True permet le rechargement automatique et affiche les erreurs détaillées
    app.run(debug=True, host="0.0.0.0", port=1312)