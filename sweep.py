from math import atan2

from parser_dat_file import extract_data_from_vrp
from clarke_euristic import capacity

def sweep_algorithm(clienti, coordinate, distanze, domande, capacita, veicoli):
    # Ordina i clienti in senso orario rispetto al deposito (nodo 1)
    centro = (coordinate[1][0], coordinate[1][1]) 
    angoli = {i: atan2(coordinate[i][1] - centro[1], coordinate[i][0] - centro[0]) for i in clienti}
    clienti_ordinati = sorted(clienti, key=lambda x: angoli[x])

    print("Clienti ordinati in senso orario rispetto al deposito:")
    print(clienti_ordinati)
    print("Angoli associati ai clienti:")
    for cliente, angolo in angoli.items():
        print(f"  Cliente {cliente}: {angolo:.2f} rad")
    
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
        print(f"Percorso: {path} con costo {costo_path:.2f} e domanda {capacity(path, domande)}")
    
    if len(percorsi) <= veicoli:
        return percorsi, costo_totale
    else:
        print(f"Numero di percorsi ({len(percorsi)}) superiore al numero di veicoli ({veicoli})")
        return None, None  # Non è possibile soddisfare il vincolo sui veicoli

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
    coordinate = dati["coordinate"]
    capacita = dati["capacita"]
    veicoli = int(dati["veicoli"])
    percorsi, costo_totale = sweep_algorithm(clienti, coordinate, distanze, domande, capacita, veicoli)
    if percorsi is None:
        print("Non è possibile trovare una soluzione con il numero di veicoli disponibile.")
    else:
        print("Percorsi finali:")
        for percorso in percorsi:
            print(percorso)
        print(f"Costo totale: {costo_totale:.2f}")