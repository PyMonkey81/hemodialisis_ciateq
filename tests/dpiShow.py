import ctypes

# Obtener el contexto del dispositivo (DC) para la pantalla principal
hdc = ctypes.windll.user32.GetDC(0)

# Obtener DPI (Puntos por pulgada) vertical y horizontal
dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88) # 88 = LOGPIXELSX (Horizontal)

ctypes.windll.user32.ReleaseDC(0, hdc)

# El DPI estándar de Windows es 96.
# Si tienes 125%, el DPI será 120. (96 * 1.25 = 120)
scale_factor = dpi / 96

print(f"Escala detectada: {scale_factor * 100}%")

# Ahora puedes multiplicar el tamaño de tu ventana por este factor
ancho_base = 1920
alto_base = 1080

# Si quieres que se ajuste al espacio visual disponible:
ancho_ajustado = int(ancho_base / scale_factor)
alto_ajustado = int(alto_base / scale_factor)

print(f"Tamaño ajustado para programar: {ancho_ajustado}x{alto_ajustado}")
