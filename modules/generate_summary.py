import torch
import time
import re
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "EleutherAI/pythia-70m-deduped"
tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
model_fp32 = AutoModelForCausalLM.from_pretrained(model_name)
model_int8 = torch.quantization.quantize_dynamic(model_fp32, {torch.nn.Linear}, dtype=torch.qint8)

_WORD_RE = re.compile(r"\b[\w'-]+\b")

def count_words(s: str) -> int:
    return len(_WORD_RE.findall(s))

def generate_summary(text: str, optimized: bool = False):
    #Generate a 10–15 word summary using token length control instead of truncation.
    if not text or not text.strip():
        return {"error": "Empty text."}

    model = model_int8 if optimized else model_fp32
    model.eval()

    prompt = (
        "You are a helpful assistant that summarizes text concisely.\n"
        "Summarize the following text in 10 to 15 words. Output one sentence.\n\n"
        f"Text:\n{text}\n\nSummary:"
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=768)

    # Target: 10–15 words ≈ 20–30 tokens
    min_toks = 10
    max_toks = 18

    t0 = time.perf_counter()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            min_new_tokens=min_toks,       # ne s'arrête pas avant 10 tokens
            max_new_tokens=max_toks,       # s'arrête après environ 15 mots
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.4,
            no_repeat_ngram_size=3,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
    t1 = time.perf_counter()

    full = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # garde seulement le texte après "Summary:"
    summary = full.split("Summary:")[-1].strip() if "Summary:" in full else full.strip()
    summary = re.sub(r"\s+", " ", summary).strip()

    return {
        "summary": summary,
        "words": count_words(summary),
        "latency_ms": round((t1 - t0) * 1000, 2),
        "optimized": optimized,
    }
