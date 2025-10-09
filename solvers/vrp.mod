# Numero clienti
param N integer > 0;

# Insieme di tutti i nodi (1 è il deposito)
set V := 1..N;

set E := {(i,j) in V cross V: i < j};

# Insieme dei clienti (1..N)
set Customers := 2..N;

# c[i,j] = costo per viaggiare dal nodo i al nodo j
param c{E} >= 0;

# K = numero di veicoli disponibili
param K integer > 0;

# d[i] = domanda del cliente i
param d{V};

# Q = capacità di ogni veicolo
param Q > 0;


var x{E} integer >= 0;  # x[i,j] è il numero di volte che l'arco (i,j) è usato nella soluzione

# ==========================================================
# OBJECTIVE FUNCTION
# ==========================================================

minimize Total_Cost:
    sum{(i, j) in E} c[i,j] * x[i,j];

# ==========================================================
# CONSTRAINTS
# ==========================================================

# Ogni cliente deve essere visitato esattamente una volta, quindi il grado
# del nodo corrispondente nel grafo della soluzione deve essere 2.
subject to Degree_Constraint {k in Customers}:
    sum {(i,j) in E: i = k or j = k} x[i,j] = 2;

# Il numero totale di archi usati che partono/arrivano al deposito
# deve essere pari a 2 volte il numero di veicoli.
subject to Depot_Constraint:
    sum {(i,j) in E: i = 1 or j = 1} x[i,j] = 2*K;

# Gli archi tra clienti possono essere usati al massimo una volta.
subject to Bounds_Customers {(i,j) in E: i != 1 and j != 1}:
    x[i,j] <= 1;

# Gli archi che collegano il deposito possono essere usati al massimo due volte
# (un veicolo parte e uno torna sullo stesso "canale" logico).
subject to Bounds_Depot {(i,j) in E: i = 1 or j = 1}:
    x[i,j] <= 2;
