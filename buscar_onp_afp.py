with open("scripts/script_completo/script.py",
          encoding="utf-8", errors="ignore") as f:
    lineas = f.readlines()

terminos = ['ONP', 'AFP', 'jubil', 'pension',
            'PENSION', 'P550', 'P551', 'P552',
            'P553', 'P554', 'ingreso', 'INGRESO',
            'transfer', 'TRANSFER']

encontrados = set()
for i, linea in enumerate(lineas):
    if any(t in linea for t in terminos):
        if i not in encontrados:
            encontrados.add(i)
            inicio = max(0, i-2)
            fin    = min(len(lineas), i+3)
            print(f"\nLinea {i+1}:")
            for j in range(inicio, fin):
                print(f"  {j+1}: {lineas[j]}", end="")
