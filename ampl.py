import random
import matplotlib.pyplot as plt
from amplpy import AMPL

from parser_dat_file import extract_data_from_vrp


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

distanze = {(i, j): 
            ((dati["coordinate"][i][0] - dati["coordinate"][j][0])**2 + (dati["coordinate"][i][1] - dati["coordinate"][j][1])**2)**0.5 
            for i in dati["coordinate"].keys() for j in dati["coordinate"].keys()}

# --- 2. Interazione con AMPL ---
# Crea un'istanza di AMPL
ampl = AMPL()

# Imposta Gurobi come solutore
ampl.option['solver'] = 'gurobi'
ampl.option['solver_msg'] = 1  # Mostra i messaggi del solver
ampl.option['gurobi_options'] = 'MIPFocus=1 TimeLimit=300'  # Opzioni di Gurobi
ampl.option['time'] = 1  # Abilita il monitoraggio del tempo
ampl.option['presolve'] = 0  # Abilita il presolve
# Modifica la riga delle opzioni di Gurobi in questo modo:
# Test with only one option to isolate the problem
#ampl.option['gurobi_options'] = 'DisplayInterval=5'

# Leggi il file del modello
ampl.read('vrp.mod')

# --- 3. Passaggio dei Dati da Python ad AMPL ---
# Assegna gli insiemi
ampl.set['NODI'] = range(1, dati["clienti"] + 1)#[:-20]
ampl.set['CLIENTI'] = range(1, dati["clienti"] + 1)#[:-20]
ampl.set['VEICOLI'] = range(1, int(dati["veicoli"]) + 1)#[:-20]

# Assegna i parametri
ampl.param['num_clienti'] = dati["clienti"]# - 20
ampl.param['capacita_veicolo'] = dati["capacita"]
ampl.param['deposito'] = 1

# for k in list(dati["domande"].keys())[-20:]:
#     dati["domande"].pop(k)
ampl.param['domanda'] = dati["domande"]

ampl.param['dist'] = distanze

# --- 4. Risoluzione del Modello ---
print("Risoluzione del modello VRP con AMPL e Gurobi...")
ampl.solve()

print("\n--- DEBUG CON AMPL.DISPLAY ---")
try:
    ampl.display('Total_Distance.best_bound')
    ampl.display('_solve_result_num') # Proviamo anche un altro suffisso
except Exception as e:
    print(f"Errore durante ampl.display: {e}")
print("--- FINE DEBUG ---\n")

# --- 5. Recupero e Visualizzazione dei Risultati ---
solve_result = ampl.get_value('solve_result')
print(f"Stato della soluzione: {solve_result}")

try:
    solve_time = ampl.get_value('_solve_time')
    print(f"DEBUG: Tempo di risoluzione recuperato con successo: {solve_time:.4f} secondi")
except Exception as e:
    print(f"DEBUG: IMPOSSIBILE recuperare _solve_time. Errore: {e}")


try:
    # Prova a recuperare i valori. Se non è stata trovata nemmeno una soluzione
    # ammissibile, questo blocco potrebbe generare un'eccezione.
    
    # Valore della migliore soluzione trovata (Upper Bound)
    distanza_trovata = ampl.get_objective('Total_Distance').value()
    print(f"Migliore soluzione trovata (distanza totale): {distanza_trovata:.2f}")



    # Miglior stima del limite inferiore (Lower Bound)
    lower_bound = ampl.get_objective('Total_Distance').get('best_bound')
    if lower_bound is not None:
        print(f"Lower Bound (stima ottima teorica): {lower_bound}")

    # Gap di ottimalità relativo
    # Nota: il valore è una frazione (es. 0.05 per 5%)
    mip_gap = ampl.get_objective('Total_Distance').get('rel_mipgap')
    if mip_gap is not None:
        print(f"Gap di ottimalità: {mip_gap * 100:.4f}%")
        
    # Se il gap è molto piccolo o zero, possiamo considerarla ottima
    if mip_gap is not None and mip_gap < 1e-6:
        print("\nLa soluzione trovata è ottima!")
    else:
        print("\nLa soluzione potrebbe non essere ottima (interrotta da time limit o altro).")


    # --- Visualizzazione del percorso (se esiste una soluzione) ---
    print("\nRecupero dei percorsi per la visualizzazione...")
    x = ampl.get_variable('x').get_values().to_dict()
    
    # (Qui puoi inserire il tuo codice per la visualizzazione con matplotlib)
    # Esempio di stampa dei percorsi:
    percorsi = {k: [] for k in range(1, int(dati["veicoli"]) + 1)}
    for (i, j, k), val in x.items():
        if val > 0.5: # Se l'arco (i,j) è usato dal veicolo k
            percorsi[k].append((i, j))
    
    for k, archi in percorsi.items():
        if archi: # Stampa solo se il veicolo è usato
            print(f"Percorso Veicolo {k}: {archi}")
            
except Exception as e:
    print(f"\nNessuna soluzione ammissibile trovata entro il limite di tempo. Errore: {e}")
