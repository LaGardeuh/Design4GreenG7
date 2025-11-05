import os
import torch
from safetensors.torch import load_file, save_file


def unsplit_model(split_folder_paths, cache_dir=None):
    """
    Reconstruit un modèle à partir de fichiers safetensors partiels et le sauvegarde dans le cache.

    Args:
        split_folder_paths (list[str]): Liste de chemins vers les dossiers contenant les splits.
        cache_dir (str, optional): Dossier où sauvegarder le modèle reconstruit.
                                   Par défaut ~/.cache/unsplit_models/

    Returns:
        str: Chemin du dossier contenant le modèle reconstruit.
    """
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/unsplit_models/")

    os.makedirs(cache_dir, exist_ok=True)
    model_file = os.path.join(cache_dir, "model.safetensors")

    # Si le modèle complet existe déjà, on renvoie simplement le cache
    if os.path.exists(model_file):
        return cache_dir

    # Cherche tous les fichiers splits
    split_files = []
    for folder in split_folder_paths:
        for i in range(1, 100):  # Supporte jusqu'à 99 splits
            part_path = os.path.join(folder, f"model_part{i}.safetensors")
            if os.path.exists(part_path):
                split_files.append(part_path)
            else:
                if i == 1:
                    raise FileNotFoundError(f"Split manquant : {part_path}")
                break

    if not split_files:
        raise FileNotFoundError("Aucun split trouvé dans les dossiers spécifiés.")

    # Charge tous les splits
    weights_list = [load_file(f) for f in split_files]

    # Concatène les splits pour chaque clé
    full_weights = {k: torch.cat([w[k] for w in weights_list], dim=0) for k in weights_list[0].keys()}

    # Sauvegarde dans le cache
    save_file(full_weights, model_file)
    print(f"Modèle reconstruit et sauvegardé dans : {model_file}")

    return cache_dir
