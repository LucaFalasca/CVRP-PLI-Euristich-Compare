from math import atan2

from parser_dat_file import extract_data_from_vrp, extract_data_from_vrp2
from clarke_euristic import capacity
import time
import logging
import os
import glob

def sweep_algorithm(clienti, coordinate, distanze, domande, capacita, veicoli):
    # Ordina i clienti in senso orario rispetto al deposito (nodo 1)
    centro = (coordinate[1][0], coordinate[1][1]) 
    angoli = {i: atan2(coordinate[i][1] - centro[1], coordinate[i][0] - centro[0]) for i in clienti}
    clienti_ordinati = sorted(clienti, key=lambda x: angoli[x])

    logging.debug("Clienti ordinati in senso orario rispetto al deposito:")
    logging.debug(clienti_ordinati)
    logging.debug("Angoli associati ai clienti:")
    for cliente, angolo in angoli.items():
        logging.debug(f"  Cliente {cliente}: {angolo:.2f} rad")
    
    percorsi = []
    percorso_corrente = [1]
    carico_corrente = 0
    
    for cliente in clienti_ordinati:
        domanda_cliente = domande[cliente]
        if carico_corrente + domanda_cliente <= capacita or len(percorsi) == veicoli - 1:
            percorso_corrente.append(cliente)
            carico_corrente += domanda_cliente
        else:
            percorso_corrente.append(1)
            percorsi.append(percorso_corrente)
            percorso_corrente = [1, cliente]
            carico_corrente = domanda_cliente
    
    if percorso_corrente:
        percorso_corrente.append(1)
        percorsi.append(percorso_corrente)

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
    
    if len(percorsi) <= veicoli or veicoli == 0:
        return percorsi, costo_totale
    else:
        logging.debug(f"Numero di percorsi ({len(percorsi)}) superiore al numero di veicoli ({veicoli})")
        return None, None  # Non è possibile soddisfare il vincolo sui veicoli

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    max_processing_time = 300  # secondi
    dir_path = "A/"
    pattern = os.path.join(dir_path, "*.vrp")
    all_files = glob.glob(pattern)
    # ordino i file per nome
    all_files.sort()
    result_file = "sweep-results.csv"
    with open(result_file, "w") as f:
        f.write("Method,Instance,N,K,Q,Cost,Optimal_Value,Optimality_Gap(%),Processing_Time(s)\n")
    # Esempio di dati
    for file_data in all_files:
        logging.info(f"Elaborazione del file: {file_data} in corso...")

        dati = extract_data_from_vrp(file_data)
    

        # for k in list(dati["coordinate"].keys())[-20:]:
        #     dati["coordinate"].pop(k)

        distanze = {(i, j): round(((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5, 0)
                    for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

        clienti = list(dati["domande"].keys())[1:]  # Escludo il deposito (nodo 1)

        domande = dati["domande"]
        coordinate = dati["coordinate"]
        capacita = dati["capacita"]
        veicoli = int(dati["veicoli"])
        start = time.perf_counter()
        percorsi, costo_totale = sweep_algorithm(clienti, coordinate, distanze, domande, capacita, veicoli)
        end = time.perf_counter()
        solution_file = file_data.replace('.vrp', '.sol')#.replace('instances', 'solutions')
        with open(solution_file, "r") as f:
            lines = f.readlines()
            opt = float(lines[-1].strip().split()[-1])  # Ultima riga, ultima parola
        logging.debug(f"Optimality flag from solution file: {opt}")
        optimal_gap = round(abs(opt - costo_totale) / opt * 100, 2) if opt != 0 and costo_totale is not None else None
        result = f"{"Sweep"},{file_data.split('/')[-1].replace('.vrp', '')},{dati['clienti'] - 1},{veicoli},{capacita},{costo_totale if percorsi else None},{opt},{optimal_gap},{end - start:.6f}\n"
        with open(result_file, "a") as f:
            f.write(f"{result}")
        logging.info(f"Elaborazione del file: {file_data} completata.")
        logging.info(f"Risultato: {result.strip()}")