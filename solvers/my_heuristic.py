from utils.parser_dat_file import extract_data_from_vrp, extract_data_from_vrp2
import time
import logging
import os
import glob

def my_euristich(clienti, distanze, domande, capacita, veicoli):
    percorsi = []  # Lista dei percorsi

    path = ([1], [1])  # Inizio con il deposito
    carico_corrente = 0  # Carico attuale del veicolo

    clienti_rimanenti = set(clienti)  # Clienti ancora da servire

    trovato = [True, True]  # Flag per indicare se un cliente è stato aggiunto a un percorso

    for k in range(veicoli):
        
        while clienti_rimanenti:
            for i in range(2):
                if trovato[i]:
                    trovato[i] = False
                    logging.debug("Clienti rimanenti:", clienti_rimanenti)
                    last_client = path[i][-1]
                    # Cliente più vicino
                    clienti_ordered = sorted(clienti_rimanenti, key = lambda c: distanze[c, last_client] if c < last_client else distanze[last_client, c])
                    for c in clienti_ordered:
                        logging.debug("min_cliente:", c)
                        logging.debug("Distanza dal cliente corrente:", distanze[c, last_client] if c < last_client else distanze[last_client, c])
                        logging.debug("Carico corrente:", carico_corrente)
                        if carico_corrente + domande[c] <= capacita:
                            path[i].append(c)
                            logging.debug("Percorso aggiornato:", path)
                            carico_corrente += domande[c]
                            clienti_rimanenti.remove(c)
                            trovato[i] = True
                            break
            logging.debug("Stato trovato:", trovato)
            if not trovato[0] and not trovato[1] or not clienti_rimanenti:
                logging.debug("Nessun cliente può essere aggiunto al percorso corrente.")
                path_merged = path[0] + path[1][::-1]
                logging.debug("Percorso chiuso:", path_merged)
                logging.debug("Carico percorso:", carico_corrente)
                percorsi.append(path_merged)
                path = ([1], [1])
                carico_corrente = 0
                trovato = [True, True]
                break
            
    if clienti_rimanenti:
        logging.debug(f"Soluzione con {veicoli} veicoli non trovata")
        return None
    return percorsi


def my_euristich_without_k(clienti, distanze, domande, capacita, veicoli):
    percorsi = []  # Lista dei percorsi

    path = ([1], [1])  # Inizio con il deposito
    carico_corrente = 0  # Carico attuale del veicolo

    clienti_rimanenti = set(clienti)  # Clienti ancora da servire

    trovato = [True, True]  # Flag per indicare se un cliente è stato aggiunto a un percorso

    while clienti_rimanenti:
        len_clienti_iniziali = len(clienti_rimanenti)
        while clienti_rimanenti:
            for i in range(2):
                if trovato[i]:
                    trovato[i] = False
                    logging.debug(f"Clienti rimanenti: {clienti_rimanenti}")
                    last_client = path[i][-1]
                    # Cliente più vicino
                    clienti_ordered = sorted(clienti_rimanenti, key = lambda c: distanze[c, last_client] if c < last_client else distanze[last_client, c])
                    for c in clienti_ordered:
                        logging.debug(f"min_cliente: {c}")
                        logging.debug(f"Distanza dal cliente corrente: {distanze[c, last_client] if c < last_client else distanze[last_client, c]}")
                        logging.debug(f"Carico corrente: {carico_corrente}")
                        if carico_corrente + domande[c] <= capacita:
                            path[i].append(c)
                            logging.debug(f"Percorso aggiornato: {path}")
                            carico_corrente += domande[c]
                            clienti_rimanenti.remove(c)
                            trovato[i] = True
                            break
            logging.debug(f"Stato trovato: {trovato}")
            if not trovato[0] and not trovato[1] or not clienti_rimanenti:
                logging.debug("Nessun cliente può essere aggiunto al percorso corrente.")
                path_merged = path[0] + path[1][::-1]
                logging.debug(f"Percorso chiuso: {path_merged}")
                logging.debug(f"Carico percorso: {carico_corrente}")
                percorsi.append(path_merged)
                path = ([1], [1])
                carico_corrente = 0
                trovato = [True, True]
                break
        if len(clienti_rimanenti) == len_clienti_iniziali:
            logging.debug("Non è possibile servire tutti i clienti con i veicoli disponibili.")
            return None
        
    return percorsi

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    num_experiments = 1
    max_processing_time = 300  # secondi
    dir_path = "benchmarks/Vrp-Set-XML100/instances/"
    pattern = os.path.join(dir_path, "*.vrp")
    all_files = glob.glob(pattern)
    logging.debug(f"Found {len(all_files)} files matching the pattern.")
    # ordino i file per nome
    all_files.sort()
    result_file = "results/my-heuristic-results-XML100.csv"
    with open(result_file, "w") as f:
        f.write("Method,Instance,N,Optimal_K,Euristich_K,Q,Cost,Optimal_Value,Optimality_Gap(%),Optimality_K_Gap(%),Processing_Time(s)\n")
    # Esempio di dati
    for file_data in all_files[:]:
        logging.info(f"Elaborazione del file: {file_data} in corso...")

        dati = extract_data_from_vrp2(file_data)
    

        # for k in list(dati["coordinate"].keys())[-20:]:
        #     dati["coordinate"].pop(k)

        distanze = {(i, j): round(((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5, 0)
                    for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

        clienti = list(dati["domande"].keys())[1:]  # Escludo il deposito (nodo 1)

        domande = dati["domande"]
        capacita = dati["capacita"]
        veicoli = int(dati["veicoli"])
        sum_time = 0
        for _ in range(num_experiments):
            start = time.perf_counter()
            percorsi = my_euristich_without_k(clienti, distanze, domande, capacita, veicoli)
            end = time.perf_counter()
            sum_time += end - start
        avg_time = sum_time / num_experiments

        costo_totale = 0
        for path in percorsi if percorsi else []:
            costo_path = 0
            for k in range(len(path)-1):
                if path[k] < path[k+1]:
                    costo_path += distanze[path[k], path[k+1]]
                else:
                    costo_path += distanze[path[k+1], path[k]]
            costo_totale += costo_path
            logging.debug(f"Percorso: {path} con costo {costo_path:.2f} e domanda {sum(domande[n] for n in path)}")
        solution_file = file_data.replace('.vrp', '.sol').replace('instances', 'solutions')
        with open(solution_file, "r") as f:
            lines = f.readlines()
            opt = float(lines[-1].strip().split()[-1])  # Ultima riga, ultima parola
            # estraggo il k ottimo dal numero di righe della soluzione
            opt_k = len(lines) - 1
        logging.debug(f"Optimality flag from solution file: {opt}")
        optimal_gap = round(abs(opt - costo_totale) / opt * 100, 2) if opt != 0 and costo_totale is not None and costo_totale != 0 else None
        euristich_k = len(percorsi) if percorsi else None
        optimal_k_gap = round(abs(opt_k - euristich_k) / opt_k * 100, 2) if opt_k != 0 and euristich_k is not None else None
        result = f"{"My-Euristich"},{file_data.split('/')[-1].replace('.vrp', '')},{dati['clienti'] - 1},{opt_k},{euristich_k},{capacita},{costo_totale if percorsi else None},{opt},{optimal_gap},{optimal_k_gap},{avg_time:.6f}\n"
        with open(result_file, "a") as f:
            f.write(f"{result}")
        logging.info(f"Elaborazione del file: {file_data} completata.")
        logging.info(f"Risultato: {result.strip()}")