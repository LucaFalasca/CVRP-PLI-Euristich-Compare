# Numero clienti
param N integer > 0;

# Insieme di tutti i nodi (0 è il deposito)
set V := 0..N;

# Insieme dei clienti (1..N)
set Customers := 1..N;

# c[i,j] = costo per viaggiare dal nodo i al nodo j
param c{V, V};

# K = numero di veicoli disponibili
param K integer > 0;

# d[i] = domanda del cliente i
param d{Customers};

# Q = capacità di ogni veicolo
param Q > 0;


var x{V, V} binary;  # x[i,j] = 1 se l'arco (i,j) è usato nel percorso, 0 altrimenti

# ==========================================================
# OBJECTIVE FUNCTION
# ==========================================================

minimize Total_Cost:
    sum{i in V, j in V} c[i,j] * x[i,j];

# ==========================================================
# CONSTRAINTS
# ==========================================================

subject to Arrive_At_Customer {j in Customers}:
    sum{i in V} x[i,j] = 1;

subject to Leave_From_Customer {i in Customers}:
    sum{j in V} x[i,j] = 1;

subject to Arrive_At_Depot:
    sum{i in V} x[i,0] = K;

subject to Leave_From_Depot:
    sum{j in V} x[0,j] = K;
