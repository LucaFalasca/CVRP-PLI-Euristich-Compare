import re # Libreria per gestire le espressioni regolari, utile per splittare le righe

def extract_data_from_vrp(file_input):
    """
    Estrae i dati da un file in formato VRP-LIB e li salva in un dizionario

    Args:
        file_input (str): Il percorso del file .vrp da leggere.
    """
    # 1. Inizializzazione delle strutture dati
    dati = {
        "nome": "",
        "clienti": 0,
        "veicoli": 0,
        "capacita": 0,
        "coordinate": {}, # Dizionario per {id_nodo: (x, y)}
        "domande": {}      # Dizionario per {id_nodo: domanda}
    }

    # 2. Lettura e parsing del file di input
    sezione_corrente = None # Tiene traccia della sezione che stiamo leggendo

    print(f"📄 Inizio la lettura di '{file_input}'...")

    with open(file_input, 'r') as f:
        dati["veicoli"] = file_input.split('-k')[-1].split('.')[0] # Estrae il numero di veicoli dal nome del file
        for linea in f:
            linea = linea.strip() # Rimuove spazi e a capo extra

            if not linea or linea.startswith("COMMENT"):
                continue # Salta le righe vuote o i commenti

            # Rilevamento delle parole chiave per i dati principali
            if linea.startswith("NAME"):
                dati["nome"] = linea.split(':')[1].strip()
            elif linea.startswith("DIMENSION"):
                dati["clienti"] = int(linea.split(':')[1].strip())
            elif linea.startswith("CAPACITY"):
                dati["capacita"] = int(linea.split(':')[1].strip())
            
            # Rilevamento delle sezioni di dati
            elif linea.startswith("NODE_COORD_SECTION"):
                sezione_corrente = "COORDS"
                continue
            elif linea.startswith("DEMAND_SECTION"):
                sezione_corrente = "DEMANDS"
                continue
            elif linea.startswith("DEPOT_SECTION") or linea.startswith("EOF"):
                sezione_corrente = None # Fine delle sezioni di dati
                continue

            # Parsing dei dati in base alla sezione corrente
            if sezione_corrente:
                # Usa re.split per gestire spazi multipli tra i numeri
                parti = re.split(r'\s+', linea)
                
                if not parti or not parti[0].isdigit():
                    continue

                if sezione_corrente == "COORDS":
                    id_nodo, x, y = int(parti[0]), float(parti[1]), float(parti[2])
                    dati["coordinate"][id_nodo] = (x, y)
                
                elif sezione_corrente == "DEMANDS":
                    id_nodo, domanda = int(parti[0]), int(parti[1])
                    dati["domande"][id_nodo] = domanda
    
    return dati

def extract_data_from_vrp2(file_input):
    """
    Estrae i dati da un file in formato VRP-LIB e li salva in un dizionario

    Args:
        file_input (str): Il percorso del file .vrp da leggere.
    """
    # 1. Inizializzazione delle strutture dati
    dati = {
        "nome": "",
        "clienti": 0,
        "veicoli": 0,
        "capacita": 0,
        "coordinate": {}, # Dizionario per {id_nodo: (x, y)}
        "domande": {}      # Dizionario per {id_nodo: domanda}
    }

    # 2. Lettura e parsing del file di input
    sezione_corrente = None # Tiene traccia della sezione che stiamo leggendo

    print(f"📄 Inizio la lettura di '{file_input}'...")

    with open(file_input, 'r') as f:
        #dati["veicoli"] = file_input.split('-k')[-1].split('.')[0] # Estrae il numero di veicoli dal nome del file
        for linea in f:
            linea = linea.strip() # Rimuove spazi e a capo extra

            if not linea or linea.startswith("COMMENT"):
                continue # Salta le righe vuote o i commenti

            # Rilevamento delle parole chiave per i dati principali
            if linea.startswith("NAME"):
                dati["nome"] = linea.split(':')[1].strip()
            elif linea.startswith("DIMENSION"):
                dati["clienti"] = int(linea.split(':')[1].strip())
            elif linea.startswith("CAPACITY"):
                dati["capacita"] = int(linea.split(':')[1].strip())
            
            # Rilevamento delle sezioni di dati
            elif linea.startswith("NODE_COORD_SECTION"):
                sezione_corrente = "COORDS"
                continue
            elif linea.startswith("DEMAND_SECTION"):
                sezione_corrente = "DEMANDS"
                continue
            elif linea.startswith("DEPOT_SECTION") or linea.startswith("EOF"):
                sezione_corrente = None # Fine delle sezioni di dati
                continue

            # Parsing dei dati in base alla sezione corrente
            if sezione_corrente:
                # Usa re.split per gestire spazi multipli tra i numeri
                parti = re.split(r'\s+', linea)
                
                if not parti or not parti[0].isdigit():
                    continue

                if sezione_corrente == "COORDS":
                    id_nodo, x, y = int(parti[0]), float(parti[1]), float(parti[2])
                    dati["coordinate"][id_nodo] = (x, y)
                
                elif sezione_corrente == "DEMANDS":
                    id_nodo, domanda = int(parti[0]), int(parti[1])
                    dati["domande"][id_nodo] = domanda
    
    return dati


def extract_data_from_solution(file_input):
    """
    Estrae i dati da un file di soluzione e li salva in un dizionario

    Args:
        file_input (str): Il percorso del file di soluzione da leggere.
    """
    # 1. Inizializzazione delle strutture dati
    dati = {
        "costo_totale": 0,
        "tours": []  # Lista di liste, ogni lista interna rappresenta un tour
    }

    print(f"📄 Inizio la lettura di '{file_input}'...")

    with open(file_input, 'r') as f:
        for linea in f:
            linea = linea.strip() # Rimuove spazi e a capo extra

            if not linea:
                continue # Salta le righe vuote

            if linea.startswith("Cost"):
                dati["costo_totale"] = float(linea.split(' ')[1].strip())
            elif linea.startswith("Route"):
                # Estrae il tour come lista di interi
                tour_str = linea.split(':')[1].strip()
                tour = [int(nodo) for nodo in re.split(r'\s+', tour_str) if nodo.isdigit()]
                dati["tours"].append(tour)
    
    return dati

# --- Esecuzione dello script ---
if __name__ == "__main__":
    # Nomi dei file. Modificali se necessario.
    nome_file_vrp = "A/A-n32-k5.sol"  

    try:
        dati = extract_data_from_solution(nome_file_vrp)
        print("✅ Estrazione completata con successo. Ecco i dati estratti:")
        print(dati)
    except FileNotFoundError:
        print(f"ERRORE: File non trovato. Assicurati che '{nome_file_vrp}' esista nella stessa cartella dello script.")
    # except Exception as e:
    #     print(f"Si è verificato un errore inaspettato: {e}")