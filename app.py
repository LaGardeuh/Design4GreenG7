from flask import Flask, send_from_directory, request, jsonify
import os
from modules.generate_summary import generate_summary

# Configuration Flask : sert le build SvelteKit
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "web", "build"),
    static_url_path="/"
)

# === FRONTEND ===
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

    if not text or len(text.strip()) == 0:
        return jsonify({"error": "Le texte à résumer ne peut pas être vide", "success": False}), 400
    if len(text) > 4000:
        return jsonify({
            "error": "Le texte ne doit pas dépasser 4000 caractères",
            "success": False,
            "received_length": len(text)
        }), 400

    try:
        result = generate_summary(text, optimized=optimized)
        summary = result["summary"]
        word_count = result["word_count"]
        latency = result["latency"]      # renvoyé directement (en ms)
        energy = result["energy_consumed"]

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
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur : {str(e)}", "success": False}), 500

# === API /compare ===
@app.route("/compare", methods=["POST"])
def compare():
    """Compare la version optimisée et non optimisée."""
    data = request.json
    text = data.get("textToSum", "")

    if not text or len(text.strip()) == 0:
        return jsonify({"error": "Le texte à résumer ne peut pas être vide", "success": False}), 400
    if len(text) > 4000:
        return jsonify({"error": "Le texte ne doit pas dépasser 4000 caractères", "success": False}), 400

    try:
        result_non_opt = generate_summary(text, optimized=False)
        result_opt = generate_summary(text, optimized=True)

        latency_gain = round(
            ((result_non_opt["latency"] - result_opt["latency"]) / result_non_opt["latency"]) * 100, 2
        )
        energy_gain = round(
            ((result_non_opt["energy_consumed"] - result_opt["energy_consumed"]) /
             result_non_opt["energy_consumed"]) * 100, 2
        ) if result_non_opt["energy_consumed"] > 0 else 0

        return jsonify({
            "success": True,
            "comparison": {
                "non_optimized": result_non_opt,
                "optimized": result_opt,
                "performance_gains": {
                    "latency_reduction_percent": latency_gain,
                    "energy_reduction_percent": energy_gain,
                    "latency_saved_ms": round(result_non_opt["latency"] - result_opt["latency"], 2),
                    "energy_saved_wh": round(
                        result_non_opt["energy_consumed"] - result_opt["energy_consumed"], 6)
                }
            },
            "metadata": {"input_length": len(text)}
        }), 200

    except Exception as e:
        return jsonify({"error": f"Erreur : {str(e)}", "success": False}), 500

# === Lancement ===
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1312)
