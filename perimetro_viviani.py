"""
Perímetro de la Ventana de Viviani mediante una suma de Riemann.

Proyecto de Cálculo Vectorial - ESPOL (PAO II 2026-2027).

La Ventana de Viviani es la curva que resulta de intersecar una esfera de
radio R con un cilindro de radio R/2 que pasa por el centro de la esfera:

    Esfera:   x^2 + y^2 + z^2 = R^2
    Cilindro: (x - R/2)^2 + y^2 = (R/2)^2

Parametrización (t en [0, 2*pi]):

    r(t) = ( R*cos(t)^2 , R*sen(t)*cos(t) , R*sen(t) )

Longitud de arco:

    L = integral de 0 a 2*pi de ||r'(t)|| dt = integral de R*sqrt(1 + cos(t)^2) dt

Esa integral no tiene antiderivada elemental, por lo que se aproxima con una
suma de Riemann:

    L  ~  suma de f(t_i) * delta_t,   con delta_t = 2*pi / n
"""

import math

# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------
T_INICIAL = 0.0                 # límite inferior del parámetro t
T_FINAL = 2 * math.pi           # límite superior del parámetro t
MAX_SUBINTERVALOS = 10_000_000  # tope para evitar que el programa se cuelgue

# Valor de control: L/R de la integral calculada con precisión alta
# (integral elíptica completa de segunda especie, L = 4*sqrt(2)*R*E(m=1/2)).
RAZON_REFERENCIA = 7.640395578055424

METODOS_VALIDOS = ("izquierda", "derecha", "punto_medio")


# ----------------------------------------------------------------------
# Parte matemática
# ----------------------------------------------------------------------
def funcion_subintegral(t, radio):
    """Rapidez ||r'(t)|| = R*sqrt(1 + cos(t)^2) de la parametrización."""
    return radio * math.sqrt(1 + math.cos(t) ** 2)


def suma_de_riemann(radio, n, metodo="punto_medio"):
    """
    Aproxima el perímetro de la Ventana de Viviani (en las mismas unidades
    que `radio`) con una suma de Riemann de `n` subintervalos.

    metodo: "izquierda", "derecha" o "punto_medio" (punto de muestra de
    cada subintervalo).
    """
    # Validación (también protege si otro programa importa esta función)
    if not math.isfinite(radio) or radio <= 0:
        raise ValueError("El radio R debe ser un número real positivo.")
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("El número de subintervalos debe ser un entero positivo.")
    if n > MAX_SUBINTERVALOS:
        raise ValueError(
            f"El número de subintervalos no debe superar {MAX_SUBINTERVALOS:,}."
        )
    if metodo not in METODOS_VALIDOS:
        raise ValueError(f"Método no válido. Opciones: {METODOS_VALIDOS}.")

    # Ancho de cada subintervalo: (b - a) / n
    delta_t = (T_FINAL - T_INICIAL) / n

    # Desplazamiento dentro de cada subintervalo según el método:
    # 0 -> extremo izquierdo, 1 -> extremo derecho, 0.5 -> punto medio
    desplazamiento = {"izquierda": 0.0, "derecha": 1.0, "punto_medio": 0.5}[metodo]

    suma = 0.0
    for i in range(n):
        t_i = T_INICIAL + (i + desplazamiento) * delta_t   # punto de muestra
        suma += funcion_subintegral(t_i, radio)            # f(t_i)

    perimetro = suma * delta_t                              # suma de f(t_i)*delta_t
    if not math.isfinite(perimetro):
        raise ValueError("El resultado es demasiado grande para representarse.")
    return perimetro


# ----------------------------------------------------------------------
# Entrada y salida con el usuario
# ----------------------------------------------------------------------
def leer_radio():
    """Pide R (cm) hasta que el usuario escriba un número real positivo."""
    while True:
        texto = input("Ingrese el radio R de la esfera (cm): ").strip()
        try:
            # Se acepta coma o punto decimal (ej.: 7,5 o 7.5)
            radio = float(texto.replace(",", "."))
        except ValueError:
            print("  Error: escriba un número (por ejemplo, 5 o 7,5).")
            continue
        if not math.isfinite(radio):
            print("  Error: el radio debe ser un número finito.")
        elif radio <= 0:
            print("  Error: el radio debe ser mayor que cero.")
        else:
            return radio


def leer_subintervalos():
    """Pide n hasta que el usuario escriba un entero positivo."""
    while True:
        texto = input("Ingrese el número de subintervalos n: ").strip()
        try:
            n = int(texto)
        except ValueError:
            print("  Error: escriba un número entero (por ejemplo, 100).")
            continue
        if n <= 0:
            print("  Error: n debe ser mayor que cero.")
        elif n > MAX_SUBINTERVALOS:
            print(f"  Error: n no debe superar {MAX_SUBINTERVALOS:,}.")
        else:
            return n


def formatear(valor, decimales=6):
    """Número con coma decimal, como en el reporte (ej.: 7,640396)."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def mostrar_resultados(radio, n, perimetro):
    """Imprime el perímetro aproximado y lo compara con el valor de control."""
    referencia = RAZON_REFERENCIA * radio
    error_abs = abs(perimetro - referencia)
    error_rel = error_abs / referencia * 100

    print()
    print("---------------- RESULTADOS ----------------")
    print(f"Radio R                    : {formatear(radio)} cm")
    print(f"Subintervalos n            : {n}")
    print(f"Perímetro aproximado       : {formatear(perimetro)} cm")
    print(f"Valor de control (7,6404R) : {formatear(referencia)} cm")
    print(f"Error absoluto             : {error_abs:.3e} cm")
    print(f"Error relativo             : {error_rel:.3e} %")
    print("--------------------------------------------")


def main():
    print("=" * 44)
    print(" PERÍMETRO DE LA VENTANA DE VIVIANI")
    print(" Aproximación con suma de Riemann")
    print("=" * 44)

    while True:
        radio = leer_radio()
        n = leer_subintervalos()
        perimetro = suma_de_riemann(radio, n)   # punto medio por defecto
        mostrar_resultados(radio, n, perimetro)

        otra = input("¿Desea realizar otro cálculo? (s/n): ").strip().lower()
        if otra not in ("s", "si", "sí"):
            print("Programa finalizado.")
            break
        print()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido por el usuario.")
