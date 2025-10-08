from parser_dat_file import extract_data_from_vrp, extract_data_from_vrp2
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
                        if carico_corrente + domande[c] < capacita:
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    max_processing_time = 300  # secondi
    dir_path = "Vrp-Set-XML100/instances/"
    pattern = os.path.join(dir_path, "*.vrp")
    all_files = glob.glob(pattern)
    # ordino i file per nome
    all_files.sort()
    result_file = "my-euristich-results-XML100.csv"
    with open(result_file, "w") as f:
        f.write("Method,Instance,N,K,Q,Cost,Optimal_Value,Optimality_Gap(%),Processing_Time(s)\n")
    # Esempio di dati
    for file_data in all_files:
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
        start = time.perf_counter()
        percorsi = my_euristich(clienti, distanze, domande, capacita, veicoli)
        end = time.perf_counter()

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
        logging.debug(f"Optimality flag from solution file: {opt}")
        optimal_gap = round(abs(opt - costo_totale) / opt * 100, 2) if opt != 0 and costo_totale is not None else None
        result = f"{"My-Euristich"},{file_data.split('/')[-1].replace('.vrp', '')},{dati['clienti'] - 1},{veicoli},{capacita},{costo_totale if percorsi else None},{opt},{optimal_gap},{end - start:.6f}\n"
        with open(result_file, "a") as f:
            f.write(f"{result}")
        logging.info(f"Elaborazione del file: {file_data} completata.")
        logging.info(f"Risultato: {result.strip()}")