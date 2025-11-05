# summarizer.py
# Version stable avec mesure d’énergie CodeCarbon (Wh)
# Compatible avec le modèle EleutherAI/pythia-70m-deduped

import time
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from codecarbon import EmissionsTracker


MODEL_ID = "EleutherAI/pythia-70m-deduped"

print("Chargement du modèle...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
model.eval()
device = torch.device("cpu")
model.to(device)
print("Modèle chargé.")


def summarize_text(text: str, optimized: bool = False):
    """
    Génère un résumé (10–15 mots) du texte fourni.
    Mesure la latence et la consommation énergétique (Wh).
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Texte vide ou invalide.")

    # Mode optimisé = quantization dynamique INT8
    model_use = model
    if optimized:
        from torch.ao.quantization import quantize_dynamic
        model_use = quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)

    # Prompt bilingue pour que le modèle anglais comprenne la structure
    prompt = (
        "Example:\n"
        "Text: The ocean covers most of our planet and regulates temperature.\n"
        "Summary: Ocean regulates Earth's climate.\n\n"
        f"Text: {text}\n"
        "Résumé:"
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    tracker = EmissionsTracker(
        project_name="design4green_summarizer",
        measure_power_secs=1,
        tracking_mode="process",
        save_to_file=False,
        log_level="error",
    )

    tracker.start()
    start = time.perf_counter()

    with torch.inference_mode():
        output = model_use.generate(
            **inputs,
            max_new_tokens=40,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    end = time.perf_counter()
    emissions = tracker.stop()

    # Décodage du texte généré
    text_out = tokenizer.decode(output[0], skip_special_tokens=True)

    if "Résumé:" in text_out:
        summary = text_out.split("Résumé:", 1)[1].strip()
    else:
        summary = text_out.strip()

    # Nettoyage simple
    summary = re.sub(r"\s+", " ", summary)
    words = re.findall(r"\b[\wÀ-ÖØ-öø-ÿ'-]+\b", summary)
    count = len(words)

    # Coupe à 15 mots max
    if count > 15:
        summary = " ".join(words[:15]) + "."
    elif count < 10:
        summary += "."

    # Conversion kgCO2eq -> Wh si dispo
    energy_Wh = 0.0
    try:
        data = tracker.final_emissions_data
        if data and getattr(data, "energy_consumed", None) is not None:
            energy_Wh = round(float(data.energy_consumed) * 1000, 6)
    except Exception:
        pass

    result = {
        "summary": summary,
        "words": count,
        "latency_ms": round((end - start) * 1000, 2),
        "energy_Wh": energy_Wh,
        "optimized": optimized,
    }

    return result
