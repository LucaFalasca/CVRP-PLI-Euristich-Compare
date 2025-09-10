# --- INSIEMI ---
set NODI;         # Insieme di tutti i nodi (deposito + clienti)
set CLIENTI within NODI; # Sottoinsieme dei clienti
set VEICOLI;      # Insieme dei veicoli

# --- PARAMETRI ---
param num_clienti;
param capacita_veicolo > 0;
param deposito symbolic in NODI;

param domanda{CLIENTI} >= 0; # Domanda per ogni cliente
param dist{i in NODI, j in NODI} >= 0; # Matrice delle distanze

# --- VARIABILI DI DECISIONE ---
var x{i in NODI, j in NODI, k in VEICOLI} binary; # 1 se il veicolo k va da i a j
var u{i in CLIENTI, k in VEICOLI} >= 0; # Variabile ausiliaria per eliminare i sottotour

suffix best_bound; # Miglior stima del limite inferiore (Lower Bound)

# --- FUNZIONE OBIETTIVO ---
minimize Total_Distance:
    sum{i in NODI, j in NODI, k in VEICOLI: i != j} dist[i, j] * x[i, j, k];

# --- VINCOLI ---
subject to VisitaCliente{j in CLIENTI}:
    sum{i in NODI, k in VEICOLI: i != j} x[i, j, k] = 1;

subject to ConservazioneFlusso{j in CLIENTI, k in VEICOLI}:
    sum{i in NODI: i != j} x[i, j, k] - sum{i in NODI: i != j} x[j, i, k] = 0;

subject to PartenzaDalDeposito{k in VEICOLI}:
    sum{j in CLIENTI} x[deposito, j, k] <= 1;

subject to RitornoAlDeposito{k in VEICOLI}:
    sum{j in CLIENTI} x[j, deposito, k] <= 1;

subject to CapacitaVeicolo{k in VEICOLI}:
    sum{j in CLIENTI} domanda[j] * (sum{i in NODI: i != j} x[i, j, k]) <= capacita_veicolo;

# Vincoli di Miller-Tucker-Zemlin per l'eliminazione dei sottotour
subject to LimiteInferioreU{i in CLIENTI, k in VEICOLI}:
    u[i, k] >= domanda[i];

subject to LimiteSuperioreU{i in CLIENTI, k in VEICOLI}:
    u[i, k] <= capacita_veicolo;

subject to SubtourElimination{i in CLIENTI, j in CLIENTI, k in VEICOLI: i != j}:
    u[i, k] - u[j, k] + capacita_veicolo * x[i, j, k] <= capacita_veicolo - domanda[j];