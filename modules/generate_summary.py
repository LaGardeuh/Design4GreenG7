from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time

model_name = "EleutherAI/pythia-70m-deduped"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model_fp32 = AutoModelForCausalLM.from_pretrained(model_name)

# version quantized (préparée une fois)
model_int8 = torch.quantization.quantize_dynamic(
    model_fp32, {torch.nn.Linear}, dtype=torch.qint8
)

def generate_summary(text: str, optimized: bool = False):
    """Génère un résumé de 10–15 mots avec ou sans optimisation CPU"""
    if not text or len(text.strip()) == 0:
        return {"error": "Texte vide."}

    model = model_int8 if optimized else model_fp32

    prompt = f"Summarize the following text : {text}"
    inputs = tokenizer(prompt, return_tensors="pt")

    start_time = time.perf_counter()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=40,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )
    end_time = time.perf_counter()

    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    words = summary.split()
    # Forcer 10–15 mots max
    if len(words) > 15:
        summary = " ".join(words[:15])

    latency_ms = round((end_time - start_time) * 1000, 2)
    return {
        "summary": summary,
        "latency_ms": latency_ms,
        "optimized": optimized
    }
