

from solvers.clarke_heuristic import capacity
from parser_dat_file import extract_data_from_solution, extract_data_from_vrp

file_data = 'A/A-n33-k5.vrp'

dati = extract_data_from_vrp(file_data)

distanze = {(i, j): ((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5 
            for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

domande = dati["domande"]   

file_sol = 'A/A-n33-k5.sol'

dati_sol = extract_data_from_solution(file_sol)

tours = dati_sol["tours"]
costo_totale = dati_sol["costo_totale"]

# aggiungo 1 ad ogni elemento dei tours
tours = [[nodo + 1 for nodo in tour] for tour in tours]

print("Costo dichiarato:", costo_totale)

# Calcolo domande e capacità per ogni veicolo
cost = 0
for idx, path in enumerate(tours):
    capacity_used = capacity(path, dati["domande"])
    path_list = [1] + path + [1]
    route_cost = 0
    for i in range(len(path_list) - 1):
        route_cost += round(distanze[path_list[i], path_list[i + 1]] if path_list[i] < path_list[i + 1] else distanze[path_list[i + 1], path_list[i]], 0)
    cost += int(route_cost)
    print(f"  Veicolo {idx + 1}: {path} (Capacità usata: {capacity_used}/{dati['capacita']}) (Costo percorso: {route_cost:.2f})") 
print(f"Costo totale calcolato dei percorsi: {cost:.2f}")
