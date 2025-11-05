from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = "../pythia70m-french-mlsum-adapted/"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.float32)

text = """Le suspens ne devrait pas vraiment être de mise à l’île de la Cité, siège de la cour d’appel de Paris, lundi 10 novembre pour l’audience de demande de mise en liberté (DML) de Nicolas Sarkozy. Et pourtant… « Dans 95 % des cas où un condamné à cinq ans ferme fait sa première DML, elle est rejetée », soupire une source judiciaire auprès de Blast. « Mais aucun condamné pour association de malfaiteurs n’a les mêmes garanties de représentation qu’un ancien chef d’État… »

Une libération quasi acquise ?
Définitivement condamné dans l’affaire des écoutes – dite Paul Bismuth –, en attente de la décision de la cour de cassation dans le dossier Bygmalion, le multirécidiviste Sarkozy aurait dès lors toutes les chances d’être élargi de sa cellule de la Santé lundi prochain. Et ce malgré sa condamnation à cinq ans de prison ferme dans la procédure libyenne en raison de « l’extraordinaire gravité des faits », selon le jugement du 25 septembre, assortie de l’exécution provisoire, « mesure indispensable pour garantir l’effectivité de la peine au regard de l’importance du trouble à l’ordre public causé par l’infraction » d’après les juges.

Las, ce qui s’applique lors d’un procès ne se reproduit pas forcément pour les demandes de libération. « Les seuls critères sur lesquels se fondent la cour sont la possible réitération des faits, les possibilités de fuir la justice et le danger d’influer sur l’enquête, poursuit la même source. Et il y a peu de chances qu’il commette de nouveaux faits avec Kadhafi, l’enquête est faite et franchement il est difficile de l’imaginer fuir à l’étranger… » Et dans le petit milieu judiciaire, on se demande bien comment le parquet général et la cour pourraient motiver un rejet de la demande de mise en liberté. D’où une libération quasi acquise, assortie bien sûr d’un contrôle judiciaire.


Au parquet général, un seul candidat pour porter l’accusation
Au moins l’audience sera-t-elle l’occasion pour l’ex-président de la République de découvrir le président Olivier Géron, qui dirigera les débats lors du procès en appel, et les deux procureurs qui mèneront l’accusation. Une équipe formée dans la douleur.

Sur les 76 magistrats que compte le parquet général (*) , un seul a ainsi fait acte de candidature pour représenter le ministère public. Spécialiste de la criminalité organisée, auteur d’une somme remarquée sur la question, et expert de l’association de malfaiteurs, Damien Brunet s’avère le seul volontaire à vouloir se plonger dans une affaire hors norme dans l’histoire de la Ve République.

Que les magistrats ne se bousculent pas pour se saisir de l’affaire n’est qu’à moitié étonnant de la part d’une justice qui n’avait mobilisé qu’un enquêteur à temps plein sur la procédure. Une preuve de plus que la perspective de se coltiner l’ancien héraut de la droite, ses soutiens médiatiques et politiques – à commencer par le garde des Sceaux, Gérald Darmanin, qui lui a rendu visite en détention – a largement refroidi la corporation. 

« C’est un drame pour nos corporations, ces gens qui ont peur des audiences : c’est un dossier passionnant dans lequel il ne faut aller parce qu’il y a Sarko, et où il ne faut pas refuser d’aller parce qu’il y a Sarko», peste une magistrate. « C’est un dossier radioactif, regrette un autre procureur. Tout le monde a peur de se retrouver en première ligne et qu’on aille fouiller votre passé à la recherche de la moindre accointance politique, que ce soit à gauche ou à droite. »

"""  # ton texte complet ici

# Prompt pour demander explicitement une phrase entre 10 et 15 mots
prompt = f"Résume le texte suivant en une seule phrase claire de 10 à 15 mots maximum, avec un point final. :\n{text}\nRésumé:"

inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)

outputs = model.generate(
    **inputs,
    max_new_tokens=100,    # suffisant pour une phrase courte
    do_sample=True,
    top_p=0.9,
    temperature=0.7,
    eos_token_id=tokenizer.eos_token_id  # pour que la phrase se termine correctement
)

summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

# Extraire le texte après "Résumé:"
if "Résumé:" in summary:
    summary = summary.split("Résumé:")[-1].strip()

print("Résumé :", summary)
