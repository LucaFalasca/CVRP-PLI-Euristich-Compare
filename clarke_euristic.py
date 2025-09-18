
from parser_dat_file import extract_data_from_vrp


def capacity(path, domande):
    return sum(domande[node] for node in path if node != 1)

def is_outer_node(node, path):
    path_without_depot = path[1:-1]
    if node == path_without_depot[0] or node == path_without_depot[-1]:
        return True
    else:
        return False

def merge_paths(path1, path2, i, j):
    path1_without_depot = path1[1:-1]
    path2_without_depot = path2[1:-1]
    index1 = path1_without_depot.index(i)
    index2 = path2_without_depot.index(j)
    if index1 > index2:
        path = path2_without_depot + path1_without_depot
    else:
        path = path1_without_depot + path2_without_depot
    return [1] + path + [1]

def find_mergeable_paths(percorsi, i, j):

    path_i = [path for path in percorsi if i in path][0]
    path_j = [path for path in percorsi if j in path][0]

    if  is_outer_node(i, path_i) and \
        is_outer_node(j, path_j) and \
        path_i != path_j:
        return (path_i, path_j)
    else:
        return None
    
def clarke_wright_alg(clienti, distanze, domande, capacita, veicoli):
    # Calcolo il saving per ogni coppia i, j
    savings = []
    for i in clienti:
        for j in clienti:
            if i != j:
                if i < j:  # Evita duplicati (i, j) e (j, i)
                    saving = distanze[1, i] + distanze[1, j] - distanze[i, j]
                else:
                    saving = distanze[1, j] + distanze[1, i] - distanze[j, i]
                if saving > 0:
                    # Aggiungi il saving alla lista
                    savings.append((i, j, saving))

    # Ordina i saving in ordine decrescente
    savings = sorted(savings, key=lambda item: item[2], reverse=True)
    print("Savings calcolati (in ordine decrescente):")
    for s in savings:
        print(f"  Coppia ({s[0]}, {s[1]}) con saving {s[2]:.2f}")

    # Inizializza i percorsi: ogni cliente in un percorso separato
    percorsi = [[1, i, 1] for i in clienti]

    # Cerca di unire i percorsi basandoti sui saving
    for (i, j, saving) in savings:
        path_mergeable = find_mergeable_paths(percorsi, i, j)
        if path_mergeable:
            # Unisco i percorsi
            new_path = merge_paths(path_mergeable[0], path_mergeable[1], i, j)
            if capacity(new_path, domande) <= capacita:
                percorsi.append(new_path)
                percorsi.remove(path_mergeable[0])
                percorsi.remove(path_mergeable[1])
                print(f"Uniti i percorsi di {i} e {j} con saving {saving:.2f}")

    costo_totale = 0
    for path in percorsi:
        costo_path = 0
        for k in range(len(path)-1):
            if path[k] < path[k+1]:
                costo_path += distanze[path[k], path[k+1]]
            else:
                costo_path += distanze[path[k+1], path[k]]
        costo_totale += costo_path
        print(f"Percorso: {path} con costo {costo_path:.2f} e domanda {capacity(path, domande)}")

    if len(percorsi) > veicoli:
        print(f"Numero di percorsi ({len(percorsi)}) superiore al numero di veicoli ({veicoli})")
        return None  # Non è possibile soddisfare il vincolo sui veicoli
    else:
        return percorsi, costo_totale

if __name__ == "__main__":
    # Esempio di dati
    file_data = 'A/A-n39-k5.vrp'

    dati = extract_data_from_vrp(file_data)

    # for k in list(dati["coordinate"].keys())[-20:]:
    #     dati["coordinate"].pop(k)

    distanze = {(i, j): ((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5 
                for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

    clienti = list(dati["domande"].keys())[1:]  # Escludo il deposito (nodo 1)

    domande = dati["domande"]
    capacita = dati["capacita"]
    veicoli = int(dati["veicoli"])
    percorsi, costo_totale = clarke_wright_alg(clienti, distanze, domande, capacita, veicoli)
    print("Percorsi finali:")
    for percorso in percorsi:
        print(percorso)
    print(f"Costo totale: {costo_totale:.2f}")