import math
import os
from safetensors.torch import load_file, save_file

def split_tensor(tensor, n):
    size = math.ceil(tensor.shape[0] / n)
    return [tensor[i * size:(i + 1) * size] for i in range(n)]

# Fichier original
original_path = "../models/pythia70m-xsum-100p-trained/model.safetensors"

# Charger les poids
weights = load_file(original_path)
N = 3  # nombre de splits

parts = [{} for _ in range(N)]

# Split des poids
for key, tensor in weights.items():
    chunks = split_tensor(tensor, N)
    for i in range(N):
        parts[i][key] = chunks[i]

# Sauvegarde des parties
for i, part in enumerate(parts):
    save_file(part, f"../models/pythia70m-xsum-100p-trained/model_part{i + 1}.safetensors")

print("Split en 3 parties terminé.")

# Suppression du fichier original
if os.path.exists(original_path):
    os.remove(original_path)
    print("Fichier original supprimé :", original_path)
else:
    print("Fichier original introuvable :", original_path)