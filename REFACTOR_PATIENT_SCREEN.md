# Refactorización de patient_config_screen.py

## Descripción de cambios

Se reescribió completamente la pantalla de configuración de paciente (`gui/therapy/patient_config_screen.py`) siguiendo las especificaciones del usuario:

### Cambios en la estructura UI

**Antes:**
- QScrollArea con contenido desplazable
- QFormLayout vertical (labels a la derecha, inputs a la izquierda)
- Altura expandible

**Después:**
- SIN QScrollArea (UI compacta y fija)
- QGridLayout con 4 columnas
- Lista de pacientes con altura fija de 200px

### Disposición de pantalla (de arriba a abajo)

1. **Título centrado**: "Expediente y Configuración Clínica del Paciente"
   - Font: 34px, Color: #0f172a
   - Alineación: centrado

2. **GroupBox "Seleccionar o registrar paciente"**
   - Fondo: blanco (#ffffff)
   - Borde: #cbd5e1
   - Título: azul (#2563eb)
   - Lista: altura fija de 200px, no expandible
   - Botones a la derecha de la lista:
     - "Nuevo Paciente" (verde #10b981, 210x48px)
     - "Eliminar Paciente" (rojo #dc2626, 210x48px, deshabilitado inicialmente)

3. **GroupBox "Datos Clínicos, Antropométricos y Prescripción Base"**
   - Siempre visible
   - GridLayout 4 columnas × 5 filas
   
   **Fila 0:** ID | N.S.S. | Género | Edad
   **Fila 1:** Nombre (2 cols) | Altura (cm) | Peso seco (kg)
   **Fila 2:** Peso pre (kg) | Acceso | Grupo | Filtro
   **Fila 3:** Diagnóstico (2 cols) | Médico (2 cols)
   **Fila 4:** Alergias (4 cols)

4. **Botón "Guardar y Seleccionar"**
   - Tamaño: 320x52px
   - Color: azul #2563eb
   - Centrado
   - Deshabilitado inicialmente

### Cambios en los datos del paciente

Se agregan 7 nuevos campos a la estructura de paciente en `patients.json`:
- `patient_nss`: N.S.S. (Número de Seguridad Social)
- `patient_access_type`: Tipo de acceso vascular
- `patient_blood_type`: Grupo sanguíneo
- `patient_dialyzer`: Tipo de filtro/dializador
- `patient_diagnosis`: Diagnóstico
- `patient_physician`: Médico responsable
- `patient_allergies`: Alergias conocidas

### Valores por defecto para nuevos pacientes

Al crear un paciente nuevo, se establecen estos valores por defecto:
- `patient_access_type`: "Fístula AV (FAV)"
- `patient_blood_type`: "O+"
- `patient_dialyzer`: "F8HPS (1.8 m²)"
- `patient_diagnosis`: "ERC Estadio 5"
- `patient_allergies`: "Ninguna conocida"

Otros campos vacíos: `patient_nss`, `patient_physician`

### Backward compatibility

Los archivos `patients.json` antiguos sin estos 7 campos se cargan correctamente:
- Los campos faltantes se tratan como strings vacíos
- Los pacientes antiguos pueden editarse y guardarse sin problemas
- Al guardar un paciente antiguo, se agregan automáticamente los 7 nuevos campos

### Opciones de entrada

Cada tipo de campo tiene entrada táctil específica:

- **Campos de texto** (ID, Nombre, Diagnóstico, Médico, Alergias, Filtro, N.S.S.): 
  - Se abren con KeyboardDialog al tocar
  - readOnly = True

- **Campos numéricos** (Edad, Altura, Peso seco, Peso pre):
  - Se abren con NumpadDialog al tocar
  - readOnly = True
  - Validación de rango

- **Combobox** (Género, Acceso, Grupo):
  - Género: "", "Masculino (M)", "Femenino (F)"
  - Acceso: "Fístula AV (FAV)", "Catéter Perm-Cath", "Catéter Temporal (Mahurkar)", "Injerto Vascular (PTFE)"
  - Grupo: "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-", "No especificado"

### Flujo de control

1. **Sin paciente seleccionado:**
   - Todos los campos del formulario deshabilitados y en gris
   - Botón "Guardar y Seleccionar" deshabilitado
   - Botón "Eliminar Paciente" deshabilitado

2. **Al elegir un paciente:**
   - Se cargan sus datos en el formulario
   - Todos los campos se habilitan (color normal)
   - Botones "Guardar" y "Eliminar" se habilitan

3. **Al crear un nuevo paciente:**
   - Se solicita el ID mediante KeyboardDialog
   - Se valida que no exista duplicado
   - Se crea con valores por defecto
   - Se selecciona automáticamente
   - El usuario puede editar los campos

4. **Al eliminar un paciente:**
   - Se muestra confirmación flotante
   - Se elimina de `patients.json`
   - Se limpia el formulario
   - Se deshabilitan todos los campos

5. **Al guardar:**
   - Se valida: ID y Nombre son obligatorios, Género debe ser 1 o 2
   - Se calcula `uf_goal_liters = max(0, peso_pre - peso_seco)`
   - Se guarda en `patients.json` y `current_values`
   - Se actualiza la pantalla dialysis_screen si existe

### Cambios preservados (sin modificar)

- `_load_patients_from_file()`: Mantiene la lógica original
- `_save_patients_to_file()`: Mantiene la lógica original
- NumpadDialog: Sin cambios
- KeyboardDialog: Sin cambios
- FloatingConfirmDialog: Sin cambios
- FloatingMessage: Sin cambios

### Commit

```
commit fa4c64a
Author: Miguel de Jesus Cuauhtemoc Espinoza Calderon <miguel.espinoza@ciateq.mx>

    Refactora patient_config_screen.py: quita scroll, usa GridLayout 4 columnas, agrega 7 nuevos campos
    
    - Reemplaza QScrollArea con layout fijo
    - Implementa QGridLayout 4 columnas × 5 filas
    - Lista de pacientes con altura fija de 200px
    - Agrega nuevos campos: NSS, Acceso, Tipo de sangre, Dializador, Diagnóstico, Médico, Alergias
    - Mantiene backward compatibility con patients.json antiguos
    - Todos los campos deshabilitados hasta seleccionar/crear paciente
```

