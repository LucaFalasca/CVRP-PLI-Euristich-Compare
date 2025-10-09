

#controllo che nel file di log non ci siano duplicati
with open("log_gsec", "r") as file:
    lines = file.readlines()
    unique_lines = set(lines)
    if len(lines) != len(unique_lines):
        print("Ci sono duplicati nel file di log.")
    else:
        print("Non ci sono duplicati nel file di log.")