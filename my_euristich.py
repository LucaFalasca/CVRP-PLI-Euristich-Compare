from parser_dat_file import extract_data_from_vrp
import time


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
                    print("Clienti rimanenti:", clienti_rimanenti)
                    last_client = path[i][-1]
                    # Cliente più vicino
                    clienti_ordered = sorted(clienti_rimanenti, key = lambda c: distanze[c, last_client] if c < last_client else distanze[last_client, c])
                    for c in clienti_ordered:
                        print("min_cliente:", c)
                        print("Distanza dal cliente corrente:", distanze[c, last_client] if c < last_client else distanze[last_client, c])
                        print("Carico corrente:", carico_corrente)
                        if carico_corrente + domande[c] < capacita:
                            path[i].append(c)
                            print("Percorso aggiornato:", path)
                            carico_corrente += domande[c]
                            clienti_rimanenti.remove(c)
                            trovato[i] = True
                            break
            print("Stato trovato:", trovato)
            if not trovato[0] and not trovato[1] or not clienti_rimanenti:
                print("Nessun cliente può essere aggiunto al percorso corrente.")
                path_merged = path[0] + path[1][::-1]
                print("Percorso chiuso:", path_merged)
                print("Carico percorso:", carico_corrente)
                percorsi.append(path_merged)
                path = ([1], [1])
                carico_corrente = 0
                trovato = [True, True]
                break
    if clienti_rimanenti:
        print(f"Soluzione con {veicoli} veicoli non trovata")
        return None
    return percorsi


if __name__ == "__main__":
    # Esempio di dati
    file_data = 'A/A-n80-k10.vrp'

    dati = extract_data_from_vrp(file_data)

    # for k in list(dati["coordinate"].keys())[-20:]:
    #     dati["coordinate"].pop(k)

    distanze = {(i, j): ((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5 
                for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

    clienti = list(dati["domande"].keys())[1:]  # Escludo il deposito (nodo 1)

    domande = dati["domande"]
    capacita = dati["capacita"]
    veicoli = int(dati["veicoli"])
    start = time.time()
    percorsi = my_euristich(clienti, distanze, domande, capacita, veicoli)
    end = time.time()
    print(f"Tempo di esecuzione: {end - start:.2f} secondi")
    costo_totale = 0
    for path in percorsi:
        costo_path = 0
        for k in range(len(path)-1):
            if path[k] < path[k+1]:
                costo_path += distanze[path[k], path[k+1]]
            else:
                costo_path += distanze[path[k+1], path[k]]
        costo_totale += costo_path
        print(f"Percorso: {path} con costo {costo_path:.2f} e domanda {sum(domande[n] for n in path if n != 1)}")
    if not percorsi:
        print("Non è possibile trovare una soluzione con il numero di veicoli disponibile.")
    else:
        print("Percorsi finali:")
        for percorso in percorsi:
            print(percorso)
        print(f"Costo totale: {costo_totale:.2f}")