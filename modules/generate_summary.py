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
            - latency: temps d'exécution en secondes
            - energy_consumed: énergie consommée en Wh
    """

    # Initialisation du tracker d'émissions pour mesurer la consommation énergétique
    tracker = EmissionsTracker(
        project_name="text_summarization",
        measure_power_secs=1,  # Mesure chaque seconde
        save_to_file=False,  # Ne sauvegarde pas dans un fichier
        log_level="error"  # Réduit les logs pour ne pas polluer la sortie
    )

    # Démarrage du chronomètre pour mesurer la latence
    start_time = time.time()

    # Démarrage du tracker d'émissions
    tracker.start()

    try:
        # Chargement du modèle et du tokenizer
        model_name = "EleutherAI/pythia-70m-deduped"

        if optimized:
            # VERSION OPTIMISÉE
            # Chargement du tokenizer (léger, pas besoin d'optimisation)
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Chargement du modèle en half precision (float16) pour réduire la mémoire et accélérer
            # torch_dtype=torch.float16 divise par 2 la taille du modèle en mémoire
            model = GPTNeoXForCausalLM.from_pretrained(
                model_name,
                dtype=torch.float16,  # Utilise 16 bits au lieu de 32
                low_cpu_mem_usage=True  # Optimise le chargement en mémoire
            )

            # Détection et utilisation du GPU si disponible
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)

            # Mode évaluation : désactive dropout et batch normalization
            # Réduit les calculs inutiles pendant l'inférence
            model.eval()

            # Tronquer le texte si trop long (garde les 3800 premiers caractères)
            # Laisse de la marge pour le prompt
            text = text[:3800]

            # Création d'un prompt optimisé pour guider le modèle
            # On utilise des exemples (few-shot learning) pour lui montrer le format attendu
            prompt = f"""Summarize in exactly 10-15 words:

Text: The research team discovered a new species of deep-sea fish with bioluminescent properties off the coast of Japan.
Summary: Research team finds new bioluminescent deep-sea fish species near Japan.

Text: {text}
Summary:"""

            # Tokenization du prompt
            # return_tensors="pt" retourne des tenseurs PyTorch
            # truncation=True coupe si trop long
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=900)

            # Déplace les inputs sur le même device que le modèle (GPU ou CPU)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Génération avec le modèle en mode optimisé
            with torch.no_grad():  # Désactive le calcul des gradients (pas d'entraînement)
                # torch.inference_mode() est plus optimisé que no_grad() pour l'inférence
                with torch.inference_mode():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=20,  # Maximum 20 nouveaux tokens (≈15 mots)
                        min_new_tokens=8,  # Minimum 8 tokens (≈10 mots)
                        do_sample=False,  # Génération déterministe (greedy)
                        num_beams=1,  # Pas de beam search (trop coûteux)
                        temperature=1.0,  # Pas de température car do_sample=False
                        pad_token_id=tokenizer.eos_token_id,  # Token de padding
                        eos_token_id=tokenizer.eos_token_id,  # Token de fin
                        use_cache=True  # Utilise le KV cache pour accélérer
                    )

        else:
            # VERSION NON-OPTIMISÉE (baseline)
            # Chargement standard sans optimisations
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Chargement en float32 (précision complète, plus lent et plus lourd)
            model = GPTNeoXForCausalLM.from_pretrained(model_name)

            # Reste sur CPU même si GPU disponible
            device = "cpu"
            model = model.to(device)

            # Pas de mode eval explicite

            # Texte complet sans troncature
            text = text[:4000]

            # Prompt simple sans exemples
            prompt = f"""Summarize in exactly 10-15 words:

Text: The research team discovered a new species of deep-sea fish with bioluminescent properties off the coast of Japan.
Summary: Research team finds new bioluminescent deep-sea fish species near Japan.

Text: {text}
Summary:"""

            # Tokenization standard
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1000)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Génération sans optimisations
            outputs = model.generate(
                **inputs,
                max_new_tokens=25,  # Plus de tokens autorisés
                min_new_tokens=5,  # Moins de contrainte sur le minimum
                do_sample=True,  # Échantillonnage (non déterministe)
                num_beams=2,  # Beam search (plus lent mais parfois meilleur)
                temperature=0.7,  # Contrôle la créativité
                top_p=0.9,  # Nucleus sampling
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # Décodage de la sortie du modèle en texte
        # skip_special_tokens=True enlève les tokens spéciaux comme <eos>
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extraction du résumé après "Summary:"
        # On cherche le texte après le dernier "Summary:" dans la sortie
        if "Summary:" in generated_text:
            summary = generated_text.split("Summary:")[-1].strip()
        else:
            # Si pas de "Summary:" trouvé, on prend tout après le prompt
            summary = generated_text[len(prompt):].strip()

        # Nettoyage du résumé
        # Enlève les sauts de ligne et espaces multiples
        summary = re.sub(r'\s+', ' ', summary).strip()

        # Prend seulement la première phrase si plusieurs
        summary = summary.split('.')[0]

        # Limite à environ 15 mots maximum en coupant après le 15ème mot
        words = summary.split()
        if len(words) > 15:
            summary = ' '.join(words[:15])

        # Si le résumé est trop court, on ajoute des mots du texte original
        if len(words) < 10:
            # Prend les premiers mots du texte original comme fallback
            original_words = text.split()[:15]
            summary = ' '.join(original_words[:12]) + "..."

        # Compte le nombre de mots dans le résumé final
        word_count = len(summary.split())

    finally:
        # Arrêt du tracker et récupération des métriques
        # finally garantit l'exécution même en cas d'erreur
        emissions_data = tracker.stop()

        # Calcul de la latence totale en mili-secondes arrondi a 2 chiffre apres la virgule
        latency = round((time.time() - start_time)* 1000, 2)

        # Conversion des émissions en Wh
        # emissions_data contient l'énergie en kWh, on convertit en Wh
        if emissions_data:
            energy_consumed = emissions_data * 1000  # kWh -> Wh
        else:
            energy_consumed = 0.0

    # Retour du dictionnaire avec tous les résultats
    return {
        "summary": summary,
        "word_count": word_count,
        "latency": latency,
        "energy_consumed": round(energy_consumed, 6)  # Arrondi à 6 décimales
    }


# Fonction de test pour valider le fonctionnement
def test_summary():
    """Fonction de test avec un exemple"""

    test_text = """
    Climate change is one of the most pressing issues facing our planet today. 
    Rising global temperatures are causing ice caps to melt, sea levels to rise, 
    and weather patterns to become more extreme. Scientists warn that without 
    immediate action to reduce greenhouse gas emissions, the consequences could 
    be catastrophic for future generations. Governments and organizations worldwide 
    are working to implement sustainable practices and transition to renewable 
    energy sources to combat this global crisis.
    """
    test_text2 = """The ocean, covering more than seventy percent of Earth’s surface, has long been both a source of wonder and a foundation for human civilization. From the earliest sailors navigating by the stars to modern scientists tracking climate change, humanity’s relationship with the sea has shaped our evolution, our economy, and our imagination. Yet the ocean is not merely a vast expanse of water; it is a dynamic, interconnected system that regulates weather, absorbs carbon dioxide, and supports life on a scale unmatched by any other environment. Within its depths reside the smallest plankton and the largest mammals, creatures that have evolved intricate adaptations to thrive under crushing pressure, freezing darkness, and the endless cycle of tides.

Marine ecosystems are, however, increasingly under threat. Rising temperatures disrupt coral reefs, causing bleaching events that destroy entire habitats. Plastic pollution, once a distant concern, now pervades even the most remote regions of the sea. Microscopic fragments of synthetic material have been found in fish, seabirds, and even human bloodstreams, a grim reminder of the deep connections between our consumer habits and the planet’s health. Overfishing has further destabilized the delicate balance of oceanic food webs, with many species teetering on the brink of collapse.

Despite this, hope remains anchored in innovation and cooperation. International agreements aim to reduce carbon emissions and protect marine biodiversity. Technologies such as satellite monitoring, underwater drones, and machine learning algorithms allow scientists to map ecosystems and track illegal fishing in real time. Renewable energy projects harness tides and waves to generate clean power, transforming the sea from a victim of exploitation into a partner in sustainability.

But the challenge extends beyond technology. Preserving the ocean requires a shift in consciousness — an acknowledgment that what happens below the waves affects every breath we take. The phytoplankton drifting invisibly in the water produce much of the oxygen in our atmosphere. The circulation of ocean currents redistributes heat and stabilizes global climate patterns. Every drop of rain, every gust of wind, and every fertile field is linked, in some way, to the pulse of the sea.

The ocean teaches humility. It reminds us of forces older and greater than human ambition. When a storm swells over the horizon, no amount of wealth or technology can command it to stop. Yet the same waters that destroy can also heal. They inspire art, sustain livelihoods, and offer a sense of continuity in a world increasingly fragmented by change.

As the twenty-first century unfolds, the question is not whether we will explore and exploit the ocean further — that is inevitable — but whether we will learn to do so wisely. Future generations will judge us by the clarity of the waters we leave behind, by the resilience of the reefs, and by the songs of the whales that still echo through the deep. The ocean’s story is inseparable from our own, and its fate is a mirror reflecting our collective choices. To safeguard it is not an act of charity but of survival, a recognition that protecting the sea is, in essence, protecting ourselves."""

    print("Test avec version NON-OPTIMISÉE:")
    result_non_opt = generate_summary(test_text, optimized=False)
    print(f"Résumé: {result_non_opt['summary']}")
    print(f"Nombre de mots: {result_non_opt['word_count']}")
    print(f"Latence: {result_non_opt['latency']}s")
    print(f"Énergie: {result_non_opt['energy_consumed']} Wh")
    print("\n" + "=" * 50 + "\n")

    print("Test avec version OPTIMISÉE:")
    result_opt = generate_summary(test_text, optimized=True)
    print(f"Résumé: {result_opt['summary']}")
    print(f"Nombre de mots: {result_opt['word_count']}")
    print(f"Latence: {result_opt['latency']}s")
    print(f"Énergie: {result_opt['energy_consumed']} Wh")

# Décommenter pour tester
#if __name__ == "__main__":
#   test_summary()