# Perímetro de la Ventana de Viviani

Proyecto de Cálculo Vectorial (ESPOL, PAO II 2026-2027). El programa aproxima el
perímetro de la Ventana de Viviani generada por una esfera de radio R (en cm),
mediante una suma de Riemann de la función subintegral de la longitud de arco.

## Fundamento matemático

Parametrización de la curva (t ∈ [0, 2π]):

    r(t) = (R cos²t, R sen t cos t, R sen t)

Longitud de arco:

    L = ∫₀^{2π} ‖r′(t)‖ dt = ∫₀^{2π} R √(1 + cos²t) dt

La integral no tiene antiderivada elemental, por lo que se aproxima con

    L ≈ Σ f(tᵢ) Δt,    Δt = 2π / n,    f(t) = R √(1 + cos²t)

Valor de control: L ≈ 7,6404 · R.

## Requisitos

- Python 3.8 o superior. No se necesitan librerías externas.

## Uso

```
python perimetro_viviani.py
```

El programa solicita el radio R (cm) y el número de subintervalos n, valida las
entradas y muestra el perímetro aproximado junto con el error respecto al valor
de control.

Ejemplo:

```
Ingrese el radio R de la esfera (cm): 5
Ingrese el número de subintervalos n: 100
Perímetro aproximado       : 38,201978 cm
```

## Pruebas

```
python -m unittest -v
```

## Estructura

| Archivo | Contenido |
|---|---|
| `perimetro_viviani.py` | Programa principal |
| `test_perimetro_viviani.py` | Pruebas automáticas |
| `README.md` | Esta descripción |

## Integrantes

(Completar en orden alfabético por primer apellido.)
