from amplpy import AMPL

print("Inizio test minimale...")

try:
    ampl = AMPL() # Crea un'istanza di AMPL

    print("Imposto Gurobi come solutore...")
    ampl.option['solver'] = 'gurobi'
    ampl.option['solver_msg'] = 1 # Abilita i log

    print("Definisco un modello banale...")
    ampl.eval("""
        var x >= 0;
        maximize z: x;
        s.t. c: x <= 1;
    """)

    print("Avvio la risoluzione...")
    ampl.solve()
    print("Risoluzione terminata.")

    # Stampa il risultato
    solve_result = ampl.get_value('solve_result')
    print(f"Risultato del solutore: {solve_result}")


except Exception as e:
    print(f"Si è verificato un errore: {e}")