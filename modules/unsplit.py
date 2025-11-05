from safetensors.torch import load_file, save_file
import torch

# Chemins des splits
split_paths = [
    "../pythia70m-french-mlsum-adapted/model_part1.safetensors",
    "../pythia70m-french-mlsum-adapted/model_part2.safetensors",
    "../pythia70m-french-mlsum-adapted/model_part3.safetensors"
]

# Charger tous les splits
all_weights = [load_file(p) for p in split_paths]

# Créer dictionnaire final
final_weights = {}

for key in all_weights[0].keys():
    # Concat tous les splits pour cette clé
    final_weights[key] = torch.cat([w[key] for w in all_weights], dim=0)

# Sauvegarde
save_file(final_weights, "../pythia70m-french-mlsum-adapted/model.safetensors")
print("Modèle réassemblé sauvegardé.")
