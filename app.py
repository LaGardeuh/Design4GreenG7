from flask import Flask, render_template, request, jsonify
from modules.generate_summary import generate_summary

app = Flask(__name__)

AVAILABLE_MODELS = {
    "xsum": "./models/pythia70m-french-mlsum-adapted/",
    "mlsum": "./models/pythia70m-xsum-100p-trained"
}


@app.route("/")
def home():
    """Route principale : affiche la page d'accueil"""
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Route pour générer un résumé de texte.

    Attend un JSON avec :
    - textToSum : le texte à résumer (obligatoire)
    - optimized : True/False pour choisir la version (optionnel, défaut: True)
    """

    # Récupération des données JSON envoyées par le client
    data = request.json

    # Extraction du texte à résumer
    text = data.get("textToSum", "")

    # Extraction du paramètre optimized (par défaut True si non spécifié)
    optimized = data.get("optimized", True)

    # Validation : vérifier que le texte n'est pas vide
    if not text or len(text.strip()) == 0:
        return jsonify({
            "error": "Le texte à résumer ne peut pas être vide",
            "success": False
        }), 400  # Code HTTP 400 : Bad Request

    # Validation : vérifier que le texte ne dépasse pas 4000 caractères
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
        latency_ms = result['latency']  # Déjà en millisecondes
        energy = result['energy_consumed']

        # Retour de la réponse JSON bien formatée
        return jsonify({
            "success": True,
            "mode": "Optimisé" if optimized else "Non-optimisé",
            "results": {
                "summary": summary,
                "word_count": word_count,
                "latency_ms": latency_ms,
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
    Utile pour ton rapport de Design for Green !

    Attend un JSON avec :
    - textToSum : le texte à résumer
    """

    # Récupération du texte
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
        # Génération avec version NON-OPTIMISÉE
        model_folder = AVAILABLE_MODELS["mlsum"]
        result_non_opt = generate_summary(text, optimized=False, model_folder=model_folder)

        # Génération avec version OPTIMISÉE
        result_opt = generate_summary(text, optimized=True, model_folder=model_folder)

        # Calcul des gains de performance
        latency_gain = round(
            ((result_non_opt['latency'] - result_opt['latency']) / result_non_opt['latency']) * 100,
            2
        )
        energy_gain = round(
            ((result_non_opt['energy_consumed'] - result_opt['energy_consumed']) / result_non_opt[
                'energy_consumed']) * 100,
            2
        ) if result_non_opt['energy_consumed'] > 0 else 0

        # Retour de la comparaison complète
        return jsonify({
            "success": True,
            "comparison": {
                "non_optimized": {
                    "summary": result_non_opt['summary'],
                    "word_count": result_non_opt['word_count'],
                    "latency_ms": result_non_opt['latency'],
                    "latency_s": result_non_opt['latency'],
                    "energy_wh": result_non_opt['energy_consumed']
                },
                "optimized": {
                    "summary": result_opt['summary'],
                    "word_count": result_opt['word_count'],
                    "latency_ms": result_opt['latency'] ,
                    "latency_s": result_opt['latency'],
                    "energy_wh": result_opt['energy_consumed']
                },
                "performance_gains": {
                    "latency_reduction_percent": latency_gain,
                    "energy_reduction_percent": energy_gain,
                    "latency_saved_ms": round(result_non_opt['latency'] - result_opt['latency'], 2),
                    "energy_saved_wh": round(result_non_opt['energy_consumed'] - result_opt['energy_consumed'], 6)
                }
            },
            "metadata": {
                "input_length": len(text)
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Erreur lors de la comparaison : {str(e)}",
            "success": False
        }), 500


if __name__ == "__main__":
    # Lancement du serveur Flask en mode debug
    # debug=True permet le rechargement automatique et affiche les erreurs détaillées
    app.run(debug=True, host="0.0.0.0", port=5000)