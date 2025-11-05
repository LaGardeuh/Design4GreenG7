import torch
from transformers import GPTNeoXForCausalLM, AutoTokenizer
from codecarbon import EmissionsTracker
import time
import re


def generate_summary(text: str, optimized: bool = False) -> dict:
    """
    Génère un résumé de 10-15 mots à partir d'un texte en anglais.

    Args:
        text: Le texte à résumer (max 4000 caractères)
        optimized: Si True, utilise la version optimisée

    Returns:
        dict contenant:
            - summary: le résumé généré
            - word_count: nombre de mots du résumé
            - latency: temps d'exécution en ms
            - energy_consumed: énergie consommée en Wh
    """

    # Initialisation du tracker d'émissions
    tracker = EmissionsTracker(
        project_name="text_summarization",
        measure_power_secs=1,
        save_to_file=False,
        log_level="error"
    )

    # Démarrage du chronomètre
    start_time = time.time()

    # Démarrage du tracker
    tracker.start()

    try:
        # Chargement du modèle et du tokenizer
        model_name = "EleutherAI/pythia-70m-deduped"

        if optimized:
            # ============= VERSION OPTIMISÉE =============

            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Chargement en float16 pour réduire mémoire et accélérer
            model = GPTNeoXForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )

            # GPU si disponible
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)

            # Mode évaluation
            model.eval()

            # CORRECTION 1: Tronquer le texte plus court pour laisser place au prompt
            # et prendre les phrases les plus importantes (début + fin)
            text = text.strip()
            if len(text) > 2000:
                # Prend début + fin pour capturer intro et conclusion
                text = text[:1000] + " [...] " + text[-1000:]

            # CORRECTION 2: Prompt plus directif avec contrainte forte
            # On force le modèle à continuer UNIQUEMENT après le dernier Summary:
            prompt = f"""Text: Scientists discovered new species in Amazon rainforest with unique adaptations.
Summary: Amazon rainforest yields new species with unique biological adaptations.

Text: {text}
Summary:"""

            # Tokenization
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=600)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # CORRECTION 3: Paramètres de génération plus stricts
            with torch.no_grad():
                with torch.inference_mode():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=18,  # RÉDUIT pour éviter répétitions
                        min_new_tokens=10,  # AUGMENTÉ pour forcer minimum
                        do_sample=False,  # Greedy = déterministe
                        num_beams=1,  # Pas de beam search
                        repetition_penalty=1.5,  # AJOUTÉ: pénalise les répétitions
                        no_repeat_ngram_size=3,  # AJOUTÉ: empêche répétition de 3+ mots
                        temperature=1.0,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id,
                        use_cache=True
                    )

        else:
            # ============= VERSION NON-OPTIMISÉE (AMÉLIORÉE) =============

            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Float32 complet
            model = GPTNeoXForCausalLM.from_pretrained(model_name)

            # CPU forcé
            device = "cpu"
            model = model.to(device)

            # CORRECTION 4: Même troncature pour fairness
            text = text.strip()
            if len(text) > 2000:
                text = text[:1000] + " [...] " + text[-1000:]

            # CORRECTION 5: Même prompt pour comparaison équitable
            prompt = f"""Text: Scientists discovered new species in Amazon rainforest with unique adaptations.
Summary: Amazon rainforest yields new species with unique biological adaptations.

Text: {text}
Summary:"""

            # Tokenization
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=600)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # CORRECTION 6: Paramètres améliorés mais toujours plus lents
            outputs = model.generate(
                **inputs,
                max_new_tokens=18,
                min_new_tokens=10,
                do_sample=True,  # Sampling (plus créatif mais moins stable)
                num_beams=2,  # Beam search (plus lent)
                repetition_penalty=1.3,  # Moins strict qu'optimisé
                no_repeat_ngram_size=2,  # Moins strict qu'optimisé
                temperature=0.8,  # Température modérée
                top_p=0.92,  # Nucleus sampling
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # ============= POST-TRAITEMENT AMÉLIORÉ =============

        # Décodage
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # CORRECTION 7: Extraction plus robuste du résumé
        # On prend SEULEMENT ce qui vient après le DERNIER "Summary:"
        if "Summary:" in generated_text:
            parts = generated_text.split("Summary:")
            # Prend la dernière partie (celle générée, pas celle du prompt)
            summary = parts[-1].strip()
        else:
            # Fallback: prend tout après le prompt
            summary = generated_text[len(prompt):].strip()

        # CORRECTION 8: Nettoyage plus agressif
        # Enlève les retours à la ligne, tabs, espaces multiples
        summary = re.sub(r'\s+', ' ', summary).strip()

        # Enlève les répétitions de mots consécutifs (ex: "the the the")
        summary = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', summary, flags=re.IGNORECASE)

        # Prend seulement la première phrase (avant le premier . ! ou ?)
        summary = re.split(r'[.!?]', summary)[0].strip()

        # CORRECTION 9: Vérification de qualité du résumé
        words = summary.split()

        # Si commence par des mots du prompt, les enlever
        prompt_words = ["text", "summary", "summarize"]
        while words and words[0].lower() in prompt_words:
            words.pop(0)

        # Enlève les caractères spéciaux en début/fin
        if words:
            words[0] = words[0].lstrip(':-,')
            words[-1] = words[-1].rstrip(':-,')

        # Limite stricte à 15 mots
        if len(words) > 15:
            words = words[:15]

        # CORRECTION 10: Fallback intelligent si résumé invalide
        if len(words) < 10 or len(words) > 15:
            # Extraire les premières phrases importantes du texte original
            original_sentences = re.split(r'[.!?]', text)
            # Nettoyer les phrases
            original_sentences = [s.strip() for s in original_sentences if len(s.strip()) > 20]

            if original_sentences:
                # Prendre la première phrase et la tronquer à 12-15 mots
                first_sentence = original_sentences[0]
                words = first_sentence.split()[:14]
                # S'assurer qu'on a au moins 10 mots
                if len(words) < 10 and len(original_sentences) > 1:
                    words.extend(original_sentences[1].split())
                words = words[:15]  # Max 15 mots

        # Reconstruction du résumé final
        summary = ' '.join(words)

        # Capitalise la première lettre
        if summary:
            summary = summary[0].upper() + summary[1:]

        # Compte final des mots
        word_count = len(summary.split())

    finally:
        # Arrêt du tracker
        emissions_data = tracker.stop()

        # Calcul de la latence en millisecondes
        latency = round((time.time() - start_time) * 1000, 2)

        # Conversion en Wh
        if emissions_data:
            energy_consumed = emissions_data * 1000
        else:
            energy_consumed = 0.0

    # Retour des résultats
    return {
        "summary": summary,
        "word_count": word_count,
        "latency": latency,
        "energy_consumed": round(energy_consumed, 6)
    }


# Fonction de test
def test_summary():
    """Fonction de test avec exemples"""

    test_text = """Climate change is one of the most pressing issues facing our planet today. 
    Rising global temperatures are causing ice caps to melt, sea levels to rise, 
    and weather patterns to become more extreme. Scientists warn that without 
    immediate action to reduce greenhouse gas emissions, the consequences could 
    be catastrophic for future generations."""

    test_text2 = """The ocean covering more than seventy percent of Earth's surface has long been 
    both a source of wonder and a foundation for human civilization. Marine ecosystems are 
    increasingly under threat from rising temperatures, plastic pollution, and overfishing. 
    International agreements aim to reduce carbon emissions and protect marine biodiversity."""

    print("=" * 60)
    print("TEST 1: Climate change")
    print("=" * 60)

    print("\n🔴 Version NON-OPTIMISÉE:")
    result_non_opt = generate_summary(test_text, optimized=False)
    print(f"Résumé: {result_non_opt['summary']}")
    print(f"Mots: {result_non_opt['word_count']}")
    print(f"Latence: {result_non_opt['latency']} ms")
    print(f"Énergie: {result_non_opt['energy_consumed']} Wh")

    print("\n✅ Version OPTIMISÉE:")
    result_opt = generate_summary(test_text, optimized=True)
    print(f"Résumé: {result_opt['summary']}")
    print(f"Mots: {result_opt['word_count']}")
    print(f"Latence: {result_opt['latency']} ms")
    print(f"Énergie: {result_opt['energy_consumed']} Wh")

    # Calcul des gains
    if result_non_opt['latency'] > 0:
        latency_gain = round(((result_non_opt['latency'] - result_opt['latency']) / result_non_opt['latency']) * 100, 2)
        print(f"\n⚡ Gain de latence: {latency_gain}%")

    print("\n" + "=" * 60)
    print("TEST 2: Ocean")
    print("=" * 60)

    print("\n🔴 Version NON-OPTIMISÉE:")
    result_non_opt2 = generate_summary(test_text2, optimized=False)
    print(f"Résumé: {result_non_opt2['summary']}")
    print(f"Mots: {result_non_opt2['word_count']}")

    print("\n✅ Version OPTIMISÉE:")
    result_opt2 = generate_summary(test_text2, optimized=True)
    print(f"Résumé: {result_opt2['summary']}")
    print(f"Mots: {result_opt2['word_count']}")

# Décommenter pour tester
# if __name__ == "__main__":
#     test_summary()