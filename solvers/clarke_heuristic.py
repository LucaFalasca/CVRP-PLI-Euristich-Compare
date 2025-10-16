import glob
import logging
import os
from utils.parser_dat_file import extract_data_from_vrp, extract_data_from_vrp2
import time

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
    logging.debug("Savings calcolati (in ordine decrescente):")
    for s in savings:
        logging.debug(f"  Coppia ({s[0]}, {s[1]}) con saving {s[2]:.2f}")

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
                logging.debug(f"Uniti i percorsi di {i} e {j} con saving {saving:.2f}")

    costo_totale = 0
    for path in percorsi:
        costo_path = 0
        for k in range(len(path)-1):
            if path[k] < path[k+1]:
                costo_path += distanze[path[k], path[k+1]]
            else:
                costo_path += distanze[path[k+1], path[k]]
        costo_totale += costo_path
        logging.debug(f"Percorso: {path} con costo {costo_path:.2f} e domanda {capacity(path, domande)}")

    if len(percorsi) > veicoli and veicoli != 0:
        logging.debug(f"Numero di percorsi ({len(percorsi)}) superiore al numero di veicoli ({veicoli})")
        return None, None  # Non è possibile soddisfare il vincolo sui veicoli
    else:
        return percorsi, costo_totale

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    max_processing_time = 300  # secondi
    num_experiment = 3
    dir_path = "benchmarks/Vrp-Set-XML100/instances/"
    pattern = os.path.join(dir_path, "*.vrp")
    all_files = glob.glob(pattern)
    # ordino i file per nome
    all_files.sort()
    result_file = "results/clarke-results-XML100.csv"
    with open(result_file, "w") as f:
        f.write("Method,Instance,N,Optimal_K,Euristich_K,Q,Cost,Optimal_Value,Optimality_Gap(%),Optimality_K_Gap(%),Processing_Time(s)\n")
    # Esempio di dati
    for file_data in all_files:
        logging.info(f"Elaborazione del file: {file_data} in corso...")

        dati = extract_data_from_vrp2(file_data)

        distanze = {(i, j): round(((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5, 0)
                    for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

        clienti = list(dati["domande"].keys())[1:]  # Escludo il deposito (nodo 1)

        domande = dati["domande"]
        capacita = dati["capacita"]
        veicoli = int(dati["veicoli"])
        sum_time = 0
        for _ in range(num_experiment):
            start = time.perf_counter()
            percorsi, costo_totale = clarke_wright_alg(clienti, distanze, domande, capacita, veicoli)
            end = time.perf_counter()
            sum_time += end - start
        avg_time = sum_time / num_experiment
        solution_file = file_data.replace('.vrp', '.sol').replace('instances', 'solutions')
        with open(solution_file, "r") as f:
            lines = f.readlines()
            opt = float(lines[-1].strip().split()[-1])  # Ultima riga, ultima parola
            opt_k = len(lines) - 1
        euristich_k = len(percorsi)
        optimal_k_gap = round(abs(opt_k - euristich_k) / opt_k * 100, 2) if opt_k != 0 and euristich_k is not None else None
        logging.debug(f"Optimality flag from solution file: {opt}")
        optimal_gap = round(abs(opt - costo_totale) / opt * 100, 2) if opt != 0 and costo_totale is not None else None
        result = f"{"Clarke-Wright"},{file_data.split('/')[-1].replace('.vrp', '')},{dati['clienti'] - 1},{opt_k},{euristich_k},{capacita},{costo_totale if percorsi else None},{opt},{optimal_gap},{optimal_k_gap},{avg_time:.6f}\n"
        with open(result_file, "a") as f:
            f.write(f"{result}")
        logging.info(f"Elaborazione del file: {file_data} completata.")
        logging.info(f"Risultato: {result.strip()}")