"""Preguntas al sistema operativo (Windows): animaciones y tamaño del texto.

Las dos funciones nunca lanzan errores: si algo falla (otro sistema, permisos,
registro sin la clave) devuelven un valor neutro y la aplicación sigue igual.
"""

SPI_GETCLIENTAREAANIMATION = 0x1042  # "Efectos de animación" de Windows


def reducir_movimiento():
    """True si el usuario desactivó las animaciones de Windows.

    Corresponde a Configuración > Accesibilidad > Efectos visuales >
    Efectos de animación. Si no se puede consultar, devuelve False (animar).
    """
    try:
        import ctypes

        activadas = ctypes.c_int(1)
        consulta = ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(activadas), 0
        )
        return bool(consulta) and activadas.value == 0
    except Exception:
        return False


def factor_de_texto():
    """Factor del tamaño de texto de Windows: 1,0 (100 %) hasta 2,25 (225 %)."""
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Accessibility"
        ) as clave:
            porcentaje, _tipo = winreg.QueryValueEx(clave, "TextScaleFactor")
        return min(max(int(porcentaje), 100), 225) / 100
    except Exception:
        return 1.0
