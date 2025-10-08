import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from clarke_euristic import capacity
from parser_dat_file import extract_data_from_vrp
from amplpy import AMPL
import time
import itertools
import os
import glob
import logging

def show_graph(g):
    plt.clf()
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True, node_color='lightblue', node_size=20, font_size=10, font_color='black', font_weight='bold', edge_color='gray')
    plt.title("Grafo delle soluzioni")
    #plt.show()
    # salvo il grafo con il timestamp
    plt.savefig(f"graph/{time.time()}.png")

def find_violation(x_solution, domande, capacita):
    violated_tours = set()

    G = nx.Graph()
    for (i, j), val in x_solution.items():
        if val > 0: # Considera solo archi con flusso non nullo
            G.add_edge(i, j, capacity=val)

    #show_graph(G)
    components = list(nx.connected_components(G))
    #logging.debug(f"DEBUG: Numero di componenti connesse: {len(components)}")


    if len(components) > 1:
        #logging.debug("Tutti i nodi sono connessi. Nessun sottotour trovato.")

        for S in components:
            logging.debug(f"DEBUG: Analizzando componente connessa S = {S}")
            if len(S) < 3:
                continue

            if 1 not in S:
                #logging.debug("Sottotour non collegato al deposito trovato:", S)
                violated_tours.add(frozenset(S))

        paths = []
        # rimuovo dal grafo i sottotour trovati
        for tour in violated_tours:
            G.remove_nodes_from(tour)

        #show_graph(G)
        #logging.debug(f"Violated tours found: {violated_tours}")

        components = list(nx.connected_components(G))
        #logging.debug(f"DEBUG: Numero di componenti connesse dopo rimozione: {len(components)}")


    # ora rimuovo il deposito dal grafo
    G.remove_node(1)

    #show_graph(G)
    components = list(nx.connected_components(G))
    paths = components
    #logging.debug(f"DEBUG: Numero di componenti connesse dopo rimozione del deposito: {len(components)}")
    for path in components:
        capacity = 0
        sub_path = []
        for n in path:
            sub_path.append(n)
            capacity += domande[n]
            if capacity > capacita:
                violated_tours.add(frozenset(path))
                break
    
    return list(violated_tours), paths

def find_tour(x_solution):
    starting_nodes = []
    G = nx.Graph()
    for (i, j), val in x_solution.items():
        if val > 0: # Considera solo archi con flusso non nullo
            G.add_edge(i, j, capacity=val)
            if i == 1:
                starting_nodes.append(j)
            elif j == 1:
                starting_nodes.append(i)
    G.remove_node(1)
    #show_graph(G)
    tours = []
    logging.debug("starting_nodes:", starting_nodes)
    for start in starting_nodes:
        if not any(start in tour for tour in tours):
            tour = nx.dfs_preorder_nodes(G, source=start)
            tours.append(list(tour))
    logging.debug(f"DEBUG: Tours found: {tours}")
    return tours

if __name__ == "__main__":
    # Configurazione del logging, tolgo il debug
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    max_processing_time = 300  # secondi
    dir_path = "A/"
    pattern = os.path.join(dir_path, "*.vrp")
    all_files = glob.glob(pattern)
    # ordino i file per nome
    all_files.sort()
    result_file = "mip-results.csv"
    # Inserisco l'header nel file dei risultati
    #with open(result_file, "w") as f:
    #    f.write("Method,Instance,N,K,Q,Lower_Bound,Optimal_Value,Optimality_Gap(%),Processing_Time(s)\n")

    for file_data in all_files[26:]:
        logging.info(f"Elaborazione del file: {file_data} in corso...")
        dati = extract_data_from_vrp(file_data)

        distanze = {(i, j): round(((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5, 0)
                    for i in dati["coordinate"].keys() for j in dati["coordinate"].keys() if i < j}

        # --- 2. Interazione con AMPL ---
        # Crea un'istanza di AMPL
        ampl = AMPL()

        # Imposta Gurobi come solutore
        ampl.option['solver'] = 'gurobi'
        ampl.option['solver_msg'] = 0  # Mostra i messaggi del solver
        ampl.option['time'] = 1  # Abilita il monitoraggio del tempo

        # Leggi il file del modello
        ampl.read('vrp.mod')

        # --- 3. Passaggio dei Dati da Python ad AMPL ---
        ampl.param['K'] = int(dati["veicoli"])
        ampl.param['N'] = dati["clienti"]
        ampl.param['Q'] = dati["capacita"]
        ampl.param['d'] = dati["domande"] 
        ampl.param['c'] = distanze

        # --- 4. Risoluzione del Modello ---
        logging.debug("Risoluzione del modello VRP con AMPL e Gurobi...")
        processing_time = 0
        start = time.perf_counter()
        iteration = 0
        while(True):
            end = time.perf_counter()
            processing_time = end - start
            if processing_time >= max_processing_time:
                logging.debug("Timeout di 10 secondi raggiunto. Interrompo.")
                processing_time = max_processing_time
                break

            iteration += 1
            logging.debug(f"\n--- Iterazione {iteration} ---")
            ampl.solve()

            # Estrai la soluzione
            x = ampl.get_variable('x')
            solve_result = ampl.get_value('solve_result')
            logging.debug(f"Stato della soluzione: {solve_result}")

            if solve_result == 'infeasible':
                logging.debug("Il modello è risultato INFEASIBILE. Interrompo.")
                break

            try:
                solve_time = ampl.get_value('_solve_time')
                logging.debug(f"DEBUG: Tempo di risoluzione recuperato con successo: {solve_time:.4f} secondi")
            except Exception as e:
                logging.debug(f"DEBUG: IMPOSSIBILE recuperare _solve_time. Errore: {e}")


            # Prova a recuperare i valori. Se non è stata trovata nemmeno una soluzione
            # ammissibile, questo blocco potrebbe generare un'eccezione.
            
            # Valore della migliore soluzione trovata (Upper Bound)
            distanza_trovata = ampl.get_objective('Total_Cost').value()
            logging.debug(f"Migliore soluzione trovata (costo totale): {distanza_trovata:.2f}")

            # --- Visualizzazione del percorso (se esiste una soluzione) ---
            logging.debug("\nRecupero dei percorsi...")
            x = ampl.get_variable('x').get_values().to_dict()


            violated_constraints, paths = find_violation(x, dati["domande"], dati["capacita"])
            #logging.debug(f"violated_constraints: {violated_constraints}")
            #logging.debug(f"paths: {paths}")
            tours = find_tour(x)
            logging.debug(f"tours: {tours}")
            # if iteration >= 100:
            #     for idx, tour in enumerate(tours):
            #         capacity_used = capacity(tour, dati["domande"])
            #         logging.debug(f"  Veicolo {idx + 1}: {tour} (Capacità usata: {capacity_used}/{dati['capacita']})")
            #     exit(0)
            if not violated_constraints:
                logging.debug("Nessun sottotour trovato. Soluzione ottimale raggiunta.")
                logging.debug("Domande clienti:", dati["domande"])
                logging.debug("Distanze:", distanze)
                end = time.perf_counter()
                processing_time = round(end - start, 0)
                logging.debug(f"Tempo totale di esecuzione: {processing_time:.2f} secondi")
                for idx, path in enumerate(tours):
                    capacity_used = capacity(path, dati["domande"])
                    logging.debug(f"  Veicolo {idx + 1}: {path} (Capacità usata: {capacity_used}/{dati['capacita']})") 

                # Calcolo costo totale
                total_cost = 0
                for path in tours:
                    path_list = [1] + path + [1]
                    for i in range(len(path_list) - 1):
                        total_cost += round(distanze[path_list[i], path_list[i + 1]] if path_list[i] < path_list[i + 1] else distanze[path_list[i + 1], path_list[i]], 0)
                logging.debug(f"Costo totale calcolato dei percorsi: {total_cost:.2f}")
                logging.debug(f"Distanza totale della soluzione AMPL: {distanza_trovata:.2f}")
                break

            for index, set_S in enumerate(violated_constraints):
                S = list(set_S)

                demand_S = sum(dati["domande"][k] for k in S)
                gamma_S = (demand_S + dati["capacita"] - 1) // dati["capacita"]
                rhs = len(S) - gamma_S

                #Costruisci il lato sinistro del vincolo come stringa
                # Usiamo tuple ordinate per coerenza con il modello
                
                lhs_parts = [f"x[{i},{j}]" for i, j in itertools.combinations(sorted(S), 2)]
                lhs_string = " + ".join(lhs_parts)

                # Crea un nome univoco per il nuovo vincolo
                #nome_vincolo = f"GSEC_cut_{iteration}_{'_'.join(map(str, sorted(S)))}"
                nome_vincolo = f"GSEC_cut_{iteration}_{index}{'_'.join(map(str, sorted(S)))[:10]}"
                
                # Costruisci il comando AMPL completo
                comando_ampl = f"subject to {nome_vincolo}: {lhs_string} <= {rhs};"
                
                logging.debug(f"Aggiungo: {comando_ampl}")
                
                # 6. Esegui il comando per aggiungere dinamicamente il vincolo
                ampl.eval(comando_ampl)
        instance = file_data.split('/')[-1].replace('.vrp', '')
        n = dati["clienti"] - 1
        k = dati["veicoli"]
        q = dati["capacita"]
        low_bound = distanza_trovata
        solution_file = file_data.replace('.vrp', '.sol')
        with open(solution_file, "r") as f:
            lines = f.readlines()
            opt = float(lines[-1].strip().split()[-1])  # Ultima riga, ultima parola
        logging.debug(f"Optimality flag from solution file: {opt}")
        optimal_gap = round((opt - low_bound) / opt * 100, 2) if opt != 0 else 0
        logging.debug(f"Optimality gap: {optimal_gap:.4f}")
        result = f"{"MIP"},{instance},{n},{k},{q},{low_bound},{opt},{optimal_gap},{processing_time:.6f}\n"
        with open(result_file, "a") as f:
            f.write(f"{result}")

        logging.info(f"Elaborazione completata per il file: {file_data}\n")
        logging.info(f"Result: {result}\n")
        logging.info(f"----------------------------------------\n")
