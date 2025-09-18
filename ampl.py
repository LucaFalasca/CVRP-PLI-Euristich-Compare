import random
import matplotlib.pyplot as plt
from amplpy import AMPL
import networkx as nx
import itertools
import matplotlib.pyplot as plt
import time

from parser_dat_file import extract_data_from_vrp

def show_graph(g):
    plt.clf()
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True, node_color='lightblue', node_size=20, font_size=10, font_color='black', font_weight='bold', edge_color='gray')
    plt.title("Grafo delle soluzioni")
    #plt.show()
    # salvo il grafo con il timestamp
    plt.savefig(f"graph/{time.time()}.png")




def find_violated_gsecs2(x_solution, clienti, domande, capacita):
    violated_tours = set()

    G = nx.Graph()
    for (i, j), val in x_solution.items():
        if val > 0: # Considera solo archi con flusso non nullo
            G.add_edge(i, j, capacity=val)

    show_graph(G)

    components = list(nx.connected_components(G))
    print(f"DEBUG: Numero di componenti connesse: {len(components)}")


    if len(components) == 1:
        print("Tutti i nodi sono connessi. Nessun sottotour trovato.")
        return []

    for S in components:
        print(f"DEBUG: Analizzando componente connessa S = {S}")
        if len(S) < 2:
            continue

        if 1 not in S:
            print("Sottotour non collegato al deposito trovato:", S)
            violated_tours.add(frozenset(S))
    
    return list(violated_tours)



def find_violated_gsecs(x_solution, clienti, domande, capacita):
    """
    Trova i set S che violano i vincoli GSEC.
    Questo è un problema complesso; l'approccio qui usa min-cut.
    """
    violated_sets = []
    
    # Grafo con capacità degli archi pari ai valori di x_solution
    G = nx.Graph()
    for (i, j), val in x_solution.items():
        if val > 1e-6: # Considera solo archi con flusso non nullo
            G.add_edge(i, j, capacity=val)

    deposito = 1 
    clienti_senza_deposito = [c for c in clienti if c != deposito]

    print(f"DEBUG: Numero di clienti (escluso deposito): {len(clienti_senza_deposito)}")
    print(f"Clienti senza deposito: {clienti_senza_deposito}")

    # Itera su ogni cliente e calcola il min-cut rispetto al DEPOSITO
    for j in clienti_senza_deposito:
        
        # Calcola il min-cut tra il deposito e il cliente j
        cut_value, partition = nx.minimum_cut(G, deposito, j)
        print(f"DEBUG: Min-cut tra deposito {deposito} e cliente {j}: cut_value = {cut_value}, partition = {partition}")
        
        # La partizione che NON contiene il deposito è il nostro set S
        # Questo è un dettaglio importante. NetworkX può restituire S in partition[0] o partition[1]
        S_partition = partition[0] if deposito not in partition[0] else partition[1]
            
        print(f"DEBUG: Analizzando set S = {S_partition}")
        # Se il set è vuoto o contiene il deposito, saltalo
        if not S_partition or deposito in S_partition:
            continue

        card_S = len(S_partition)
        if card_S < 2: # Un vincolo GSEC è significativo per |S| >= 2 (o 3 in alcune formulazioni)
            continue
            
        # Il resto della logica per calcolare LHS, RHS e verificare la violazione
        # rimane ESATTAMENTE LO STESSO
        
        
        demand_S = sum(domande[k] for k in S_partition if k in domande)
        sigma_S = (demand_S + capacita - 1) // capacita
        rhs = card_S - sigma_S
        
        lhs = 0
        s_nodes = list(S_partition)
        for u_idx in range(len(s_nodes)):
            for v_idx in range(u_idx + 1, len(s_nodes)):
                u, v = s_nodes[u_idx], s_nodes[v_idx]
                # Assumendo che x_solution usi tuple ordinate o gestisca entrambi i sensi
                edge = tuple(sorted((u, v)))
                if edge in x_solution:
                    lhs += x_solution[edge]

        if lhs > rhs + 1e-6:
            violated_sets.append(frozenset(S_partition))

    # Rimuovi duplicati e restituisci
    return list(set(violated_sets))

def build_path_from_solution(soluzione_x, deposito=1):
    """
    Ricostruisce i percorsi dei veicoli a partire dalla soluzione di un modello CVRP.

    Args:
        soluzione_x (dict): Un dizionario con chiavi tuple (i, j) rappresentanti gli archi
                            e valori 1 se l'arco è nella soluzione, 0 altrimenti.
        deposito (int): Il nodo del deposito (default è 1).

    Returns:
        list: Una lista di liste, dove ogni lista interna rappresenta un percorso completo
              di un veicolo, partendo e finendo al deposito.
    """
    # Gli archi con valore 2 rappresentano un percorso con un solo nodo, li gestisco prima
    archi_unici = [(i, j) for (i, j), valore in soluzione_x.items() if valore == 2]

    percorsi_finali = []

    for arco in archi_unici:
        if arco[0] == deposito:
            percorsi_finali.append(([1, arco[1], 1], False))
        elif arco[1] == deposito:
            percorsi_finali.append(([1, arco[0], 1], False))

    # 1. Filtra solo gli archi attivi (con valore > 1)
    archi_attivi = [arco for arco, valore in soluzione_x.items() if valore == 1]

    # 2. Inizializzazione
    nodi_partenza_usati = set()

    # 3. Trova tutti gli archi che partono dal deposito
    partenze_dal_deposito = [arco for arco in archi_attivi if deposito in arco]

    print(f"DEBUG: Archi attivi dal deposito {deposito}: {archi_attivi}")
    print(f"DEBUG: Partenze dal deposito: {partenze_dal_deposito}")

    # 4. Ciclo principale per costruire ogni percorso
    while len(partenze_dal_deposito) > 0:
        partenza, prossimo_nodo = partenze_dal_deposito[0]
        print("Partenze deposito rimanenti:", partenze_dal_deposito)
        print(f"Inizio nuovo percorso da arco: ({partenza}, {prossimo_nodo})")
        # a. Inizia un nuovo percorso
        percorso_attuale = [deposito, prossimo_nodo]
        nodo_corrente = prossimo_nodo
        # tolgo l'arco dalla lista delle partenze
        partenze_dal_deposito.remove((partenza, prossimo_nodo))
        archi_attivi.remove((partenza, prossimo_nodo))

        # b. Segui il sentiero fino a tornare al deposito
        while nodo_corrente != deposito:
            if not any(nodo_corrente in arco for arco in archi_attivi):
                print(f"Attenzione: Nodo {nodo_corrente} non ha un arco successivo. Percorso incompleto.")
                percorsi_finali.append(percorso_attuale)
                break 
            tuple_compatibili = [arco for arco in archi_attivi if nodo_corrente in arco]
            for arco in tuple_compatibili:
                if arco[0] == nodo_corrente:
                    prossimo_nodo_trovato = arco[1]
                elif arco[1] == nodo_corrente:
                    prossimo_nodo_trovato = arco[0]
                archi_attivi.remove(arco)
                try: 
                    partenze_dal_deposito.remove(arco)
                except:
                    pass
            percorso_attuale.append(prossimo_nodo_trovato)
            nodo_corrente = prossimo_nodo_trovato
        print(f"Dati domande: {dati['domande']}")
        print(f"Percorso attuale prima del controllo capacità: {percorso_attuale}")
        sum_cap = 0
        for nodo in percorso_attuale:
            sum_cap += dati["domande"].get(nodo, 0)

        if sum_cap > dati["capacita"]:
            print(f"Attenzione: Capacità del veicolo superata nel percorso {percorso_attuale}: {sum_cap} > {dati['capacita']}")
            percorsi_finali.append((percorso_attuale, True))
        else:
            print(f"Capacità del veicolo nel percorso {percorso_attuale}: {sum_cap}")
            # c. Salva il percorso completo
            percorsi_finali.append((percorso_attuale, False))
        print("Partenze deposito rimanenti dopo il percorso:", partenze_dal_deposito)

    print("Sono uscito dal ciclo")
    return percorsi_finali

# --- 1. Generazione Dati in Python ---
# num_clienti = 15
# num_veicoli = 4
# capacita_veicolo = 50
# deposito = 0

# random.seed(42)
# punti = {i: (random.randint(0, 100), random.randint(0, 100)) for i in range(num_clienti + 1)}
# nodi = list(punti.keys())
# clienti = [i for i in nodi if i != deposito]

# domande = {i: random.randint(10, 20) for i in clienti}

# distanze = {(i, j): 
#             ((punti[i][0] - punti[j][0])**2 + (punti[i][1] - punti[j][1])**2)**0.5 
#             for i in nodi for j in nodi}

# Leggo da file .dat 
file_data = 'A/A-n32-k5.vrp'

dati = extract_data_from_vrp(file_data)

# for k in list(dati["coordinate"].keys())[-20:]:
#     dati["coordinate"].pop(k)

distanze = {(i, j): ((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5 
            for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}



# --- 2. Interazione con AMPL ---
# Crea un'istanza di AMPL
ampl = AMPL()

# Imposta Gurobi come solutore
ampl.option['solver'] = 'gurobi'
ampl.option['solver_msg'] = 1  # Mostra i messaggi del solver
#ampl.option['gurobi_options'] = 'MIPFocus=1 TimeLimit=30'  # Opzioni di Gurobi
ampl.option['time'] = 1  # Abilita il monitoraggio del tempo
ampl.option['presolve'] = 0  # Abilita il presolve
# Modifica la riga delle opzioni di Gurobi in questo modo:
# Test with only one option to isolate the problem
#ampl.option['gurobi_options'] = 'DisplayInterval=5'

# Leggi il file del modello
ampl.read('vrp.mod')

# --- 3. Passaggio dei Dati da Python ad AMPL ---
# Assegna gli insiemi
# ampl.set['V'] = range(0, dati["clienti"] + 1)#[:-20]
# ampl.set['Customers'] = range(1, dati["clienti"] + 1)#[:-20]
ampl.param['K'] = int(dati["veicoli"])

# Assegna i parametri
ampl.param['N'] = dati["clienti"]
ampl.param['Q'] = dati["capacita"]
# ampl.param['deposito'] = 0

# for k in list(dati["domande"].keys())[-20:]:
#     dati["domande"].pop(k)
print(dati["domande"])
ampl.param['d'] = dati["domande"] 

ampl.param['c'] = distanze

# --- 4. Risoluzione del Modello ---
print("Risoluzione del modello VRP con AMPL e Gurobi...")
iteration = 0
while(True):
    iteration += 1
    ampl.solve()

    # --- 5. Recupero e Visualizzazione dei Risultati ---
    solve_result = ampl.get_value('solve_result')
    print(f"Stato della soluzione: {solve_result}")

    if solve_result == 'infeasible':
        print("Il modello è risultato INFEASIBILE. Interrompo.")
        break

    try:
        solve_time = ampl.get_value('_solve_time')
        print(f"DEBUG: Tempo di risoluzione recuperato con successo: {solve_time:.4f} secondi")
    except Exception as e:
        print(f"DEBUG: IMPOSSIBILE recuperare _solve_time. Errore: {e}")


    # Prova a recuperare i valori. Se non è stata trovata nemmeno una soluzione
    # ammissibile, questo blocco potrebbe generare un'eccezione.
    
    # Valore della migliore soluzione trovata (Upper Bound)
    distanza_trovata = ampl.get_objective('Total_Cost').value()
    print(f"Migliore soluzione trovata (costo totale): {distanza_trovata:.2f}")

    # --- Visualizzazione del percorso (se esiste una soluzione) ---
    print("\nRecupero dei percorsi per la visualizzazione...")
    x = ampl.get_variable('x').get_values().to_dict()

    print(x)

    paths = build_path_from_solution(x)
    print(f"Percorsi trovati per i veicoli:")
    for idx, path in enumerate(paths):
        print(f"  Veicolo {idx + 1}: {path[0]}")

    violated_gsecs = find_violated_gsecs2(x, dati["coordinate"].keys(), dati["domande"], dati["capacita"])

    print(f"Trovati {len(violated_gsecs)} vincoli GSEC violati:")
    for s in violated_gsecs:
        print(f"  Set S violato: {set(s)}")

    for path in paths:
       if path[1]:
           violated_gsecs.append(frozenset(path[0]))
           print(f"  Aggiunto vincolo GSEC per percorso che viola capacità: {set(path[0])}")

    #Inserisco i nuovi vincoli GSEC
    if not violated_gsecs:
        print("soluzione ottima trovata")
        print("Domande clienti:", dati["domande"])
        print("Distanze:", distanze)
        break

    

    for set_S in violated_gsecs:
        S = list(set_S)

        demand_S = sum(dati["domande"][k] for k in S)
        gamma_S = (demand_S + dati["capacita"] - 1) // dati["capacita"]
        rhs = len(S) - gamma_S

        #Costruisci il lato sinistro del vincolo come stringa
        # Usiamo tuple ordinate per coerenza con il modello
        lhs_parts = [f"x[{i},{j}]" for i, j in itertools.combinations(sorted(S), 2)]
        lhs_string = " + ".join(lhs_parts)

        # Crea un nome univoco per il nuovo vincolo
        nome_vincolo = f"GSEC_cut_{iteration}_{'_'.join(map(str, sorted(S)))}"
        
        # Costruisci il comando AMPL completo
        comando_ampl = f"subject to {nome_vincolo}: {lhs_string} <= {rhs};"
        
        print(f"Aggiungo: {comando_ampl}")
        
        # 6. Esegui il comando per aggiungere dinamicamente il vincolo
        ampl.eval(comando_ampl)
    
    # (Qui puoi inserire il tuo codice per la visualizzazione con matplotlib)
    # Esempio di stampa dei percorsi:
    # percorsi = {k: [] for k in range(1, int(dati["veicoli"]) + 1)}
    # for (i, j, k), val in x.items():
    #     if val > 0.5: # Se l'arco (i,j) è usato dal veicolo k
    #         percorsi[k].append((i, j))
    
    # for k, archi in percorsi.items():
    #     if archi: # Stampa solo se il veicolo è usato
    #         print(f"Percorso Veicolo {k}: {archi}")



