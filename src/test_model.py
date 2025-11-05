from modules.generate_summary import summarize_text

test_text = "Les océans couvrent plus de soixante-dix pour cent de la surface de la Terre et jouent un rôle essentiel dans la régulation du climat mondial. Ils absorbent une partie considérable du dioxyde de carbone émis par les activités humaines, réduisant ainsi l’impact immédiat du réchauffement atmosphérique. Cependant, cette capacité d’absorption n’est pas illimitée, et l’acidification des mers menace gravement les écosystèmes marins. Les coraux, véritables poumons des océans, abritent une biodiversité exceptionnelle mais sont aujourd’hui en péril. Le blanchissement des récifs, provoqué par la hausse des températures de l’eau, entraîne la disparition progressive de nombreuses espèces dépendantes de ces habitats complexes. Par ailleurs, la surpêche et la pollution plastique accentuent la dégradation de la vie marine. Chaque année, des millions de tonnes de déchets sont déversés dans les mers, se fragmentant en microplastiques invisibles à l’œil nu mais omniprésents dans la chaîne alimentaire. Les scientifiques ont retrouvé ces particules dans le plancton, les poissons et même dans le sel de table consommé par les humains. Cette contamination généralisée soulève des inquiétudes sanitaires majeures, car les effets à long terme de l’ingestion de microplastiques sur la santé humaine restent encore mal connus. Les zones mortes, où l’oxygène dissous est trop faible pour permettre la survie des organismes aquatiques, s’étendent d’année en année sous l’effet combiné de la pollution et du réchauffement. La fonte des glaces aux pôles, en libérant d’immenses quantités d’eau douce, modifie les courants marins et perturbe les équilibres climatiques planétaires. Les populations côtières, souvent dépendantes de la pêche et du tourisme, subissent déjà les conséquences économiques et sociales de ces bouleversements. Face à ces défis, la communauté internationale tente de réagir. Des accords tels que celui de Paris sur le climat ou les conventions sur la protection de la biodiversité marine visent à réduire les émissions, restaurer les habitats et promouvoir une gestion durable des ressources océaniques. Toutefois, la mise en œuvre reste lente, freinée par les intérêts économiques divergents et le manque de volonté politique. La sensibilisation du grand public joue un rôle crucial : chaque geste compte, du recyclage à la réduction de la consommation de plastique à usage unique. Les innovations technologiques, comme les filets de collecte flottants ou les bioplastiques biodégradables, offrent des pistes prometteuses mais doivent s’inscrire dans une stratégie globale de transformation des modes de production et de consommation. Préserver les océans, c’est préserver notre avenir commun. Si l’humanité parvient à restaurer la santé des mers, elle disposera d’un allié puissant pour atténuer le changement climatique et garantir la survie des générations futures."

result = summarize_text(test_text, optimized=True)

print("\nModele optimisé ? ", result["optimized"])
print("Résumé :", result["summary"])
print("Mots :", result["words"])
print("Latence :", result["latency_ms"], "ms")
print("Énergie :", result["energy_Wh"], "Wh")

result = summarize_text(test_text, optimized=False)

print("\nModele optimisé ? ", result["optimized"])
print("Résumé :", result["summary"])
print("Mots :", result["words"])
print("Latence :", result["latency_ms"], "ms")
print("Énergie :", result["energy_Wh"], "Wh")