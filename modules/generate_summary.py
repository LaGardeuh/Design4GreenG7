import torch
from transformers import GPTNeoXForCausalLM, AutoTokenizer
from codecarbon import EmissionsTracker
import time
import re
import torch.quantization as tq



def generate_summary(text: str, optimized: bool = False) -> dict:
    # Génère un résumé de 10-15 mots à partir d'un texte en anglais.

    # Initialisation du tracker de consomation
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
        # Chargement du modèle
        model_name = "EleutherAI/pythia-70m-deduped"

        if optimized:
            # VERSION OPTIMISÉE

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            # Chargement normal (FP32)
            model = GPTNeoXForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )

            # Quantization dynamique INT8 (CPU)
            model = tq.quantize_dynamic(
                model,
                {torch.nn.Linear},  # uniquement sur les couches linéaires
                dtype=torch.qint8
            )

            device = "cpu"
            #on utilise le bon device
            model = model.to(device)
            # Mode évaluation
            model.eval()

            # on tronque le texte pour prendre les phrases les plus importantes (début et fin) pour pas surcharger le modele
            text = text.strip()
            if len(text) > 2000:
                # Prend début + fin pour avoir l'intro et conclusion
                text = text[:1000] + " [...] " + text[-1000:]

            # On donne un exemple de de prompt plus réponse pour montrer a l'ia (few-shot learning)
            prompt = f"""Summarize in exactly 10-15 words:
Text: The research team discovered a new species of deep-sea fish with bioluminescent properties off the coast of Japan.
Summary: Research team finds new bioluminescent deep-sea fish species near Japan.

Text: {text}
Summary:"""

            # Tokenization
            # truncation=True coupe si trop long
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=800)
            # Déplace les inputs sur le meme device que le modele (GPU ou CPU)
            inputs = {k: v.to(device) for k, v in inputs.items()}


            with torch.no_grad(): # Désactive le calcul des gradients (pas d'entrainement)
                with torch.inference_mode():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=18,  # reduit pour éviter répétitions
                        min_new_tokens=10,  # augmenté pour forcer minimum
                        do_sample=False,  # Greedy = déterministe
                        num_beams=1,  # Pas de beam search
                        repetition_penalty=1.5,  # pénalise les répétitions
                        no_repeat_ngram_size=3,  # empêche répétition de 3+ mots
                        temperature=1.0,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id,
                        use_cache=True # Utilise le KV cache pour accélérer
                    )

        else:
            # VERSION NON-OPTIMISÉE

            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Float32 complet (conf de base)
            model = GPTNeoXForCausalLM.from_pretrained(model_name)

            # CPU forcé pas de gpu pour le non opti
            device = "cpu"
            model = model.to(device)

            # on tronque aussi pour garder que l'intro et conclu
            text = text.strip()
            if len(text) > 2000:
                text = text[:1000] + " [...] " + text[-1000:]

            # on prend le meme prompt que pour l'opti
            prompt = f"""Summarize in exactly 10-15 words:
            Text: The research team discovered a new species of deep-sea fish with bioluminescent properties off the coast of Japan.
            Summary: Research team finds new bioluminescent deep-sea fish species near Japan.

            Text: {text}
            Summary:"""

            # Tokenization
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=800)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad(): #on entraine pas non plus
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

        # POST-TRAITEMENT

        # Décodage
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # On prend ce qui vient après le dernier Summary:
        if "Summary:" in generated_text:
            parts = generated_text.split("Summary:")
            # Prend la dernière partie (celle générée, pas celle de l'exemple du prompt)
            summary = parts[-1].strip()
        else:
            # Fallback: prend tout après le prompt
            summary = generated_text[len(prompt):].strip()

        # Enlève les retours à la ligne, tabs, espaces multiples
        summary = re.sub(r'\s+', ' ', summary).strip()

        # Enlève les répétitions de mots consécutifs
        summary = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', summary, flags=re.IGNORECASE)

        # Prend seulement la première phrase
        summary = re.split(r'[.!?]', summary)[0].strip()
        words = summary.split()

        # Si on commence par des mots du prompt, les enlever
        prompt_words = ["text", "summary", "summarize"]
        while words and words[0].lower() in prompt_words:
            words.pop(0)

        # Enlève les caractères spéciaux en début/fin
        if words:
            words[0] = words[0].lstrip(':-,')
            words[-1] = words[-1].rstrip(':-,')

        # Limite stricte à 15 mots max
        if len(words) > 15:
            words = words[:15]

        # Reconstruction du résumé final
        summary = ' '.join(words)

        # Capitalise la première lettre
        if summary:
            summary = summary[0].upper() + summary[1:]

        # Compte final des mots
        word_count = len(summary.split())

    finally:
        # calcul desd metrics
        # Arrêt du tracker
        emissions_data = tracker.stop()

        # Calcul de la latence en millisecondes
        latency = round((time.time() - start_time) * 1000, 2)

        # Conversion en Wh
        if emissions_data:
            energy_consumed = emissions_data * 1000
        else:
            energy_consumed = 0.0

    # Retour des résultats en dictionnaire
    return {
        "summary": summary,
        "word_count": word_count,
        "latency": latency,
        "energy_consumed": round(energy_consumed, 6)
    }
