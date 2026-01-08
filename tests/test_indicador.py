import matplotlib.pyplot as plt
import numpy as np

# Simula un nivel de tanque (0 a 100%)
nivel = 75  # Valor de ejemplo

fig, ax = plt.subplots(figsize=(2, 6))  # Alto y delgado como un tanque
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_xticks([])  # Oculta ejes para simplicidad
ax.set_yticks([])

# Dibuja el "tanque" (borde)
ax.add_patch(plt.Rectangle((0, 0), 100, 100, fill=False, edgecolor='black', linewidth=2))

# Llena el nivel como "líquido"
ax.add_patch(plt.Rectangle((0, 0), nivel, 100, color='blue', alpha=0.7))

ax.set_title('Nivel del Tanque')
plt.tight_layout()
plt.show()