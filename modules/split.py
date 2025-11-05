# import math
# from safetensors.torch import load_file, save_file
#
# def split_tensor(tensor, n):
#     size = math.ceil(tensor.shape[0] / n)
#     return [ tensor[i*size:(i+1)*size] for i in range(n) ]
#
# weights = load_file("../pythia70m-french-mlsum-adapted/model.safetensors")
# N = 3 # nombre de splits
#
# parts = [ {} for _ in range(N) ]
#
# for key, tensor in weights.items():
#     chunks = split_tensor(tensor, N)
#     for i in range(N):
#         parts[i][key] = chunks[i]
#
# # Sauvegarde
# for i, part in enumerate(parts):
#     save_file(part, f"../pythia70m-french-mlsum-adapted/model_part{i+1}.safetensors")
#
# print("Split en 3 parties terminé")
