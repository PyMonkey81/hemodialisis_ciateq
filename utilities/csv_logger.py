#utilities/csv_logger.py
"""
Clase para registrar datos de monitorización en un archivo CSV.

Esta clase facilita el registro de datos de monitorización en serie temporal,
como lecturas de sensores o variables del sistema, en un formato CSV estructurado.
Gestiona la creación del archivo, la escritura de la cabecera y la adición de
filas de datos con marcas de tiempo. Su diseño flexible permite mapear claves
internas a nombres de columnas legibles.

Características principales:
-------------------------
- **Automatización de Archivos**: Crea automáticamente el directorio de logs
  si no existe y genera nombres de archivo únicos basados en la fecha y hora
  (`YYYYMMDD_HHMMSS`) para evitar sobrescrituras.
- **Mapeo de Parámetros**: Utiliza un diccionario `parameter_key_map` para
  definir qué variables del diccionario de valores actuales se deben registrar
  y cómo se deben nombrar las columnas en el archivo CSV.
- **Registro de Tiempo Real**: Añade una marca de tiempo precisa (con milisegundos)
  a cada fila de datos, facilitando el análisis cronológico de los eventos.
- **Persistencia Inmediata**: Fuerza la escritura de los datos al disco de forma
  inmediata (`file.flush()`) después de cada registro, minimizando el riesgo
  de pérdida de datos en caso de un fallo inesperado.
- **Manejo Básico de Errores**: Incluye mensajes informativos y de error para
  problemas de apertura o escritura del archivo.

Uso:
----
1.  **Instanciación**: Crear una instancia de `CsvLogger` especificando el
    directorio donde se guardarán los logs y un diccionario de mapeo de parámetros.
2.  **Registro de Datos**: Llamar al método `log_data()` periódicamente,
    pasándole un diccionario con los valores actuales a registrar.
3.  **Cierre**: Llamar al método `close()` cuando ya no se necesite registrar
    más datos (ej. al finalizar una sesión o al cerrar la aplicación) para
    asegurar que el archivo se cierre correctamente.

Ejemplo de `parameter_key_map`:
    `{ "dialyLinePresProcessData": "Presion_Linea", "dialyTempIFProcessData": "Temperatura_EF" }`

"""

import csv
import os
from datetime import datetime
import logging
logger = logging.getLogger(__name__)



class CsvLogger:
    """
    Clase para registrar datos de monitorización en un archivo CSV.
    Versión sin patient_id: solo timestamp y valores mapeados.
    """
    def __init__(self, log_directory: str, parameter_key_map: dict):
        """
        Inicializa el logger CSV.

        :param log_directory: Directorio donde se guardarán los archivos CSV.
        :param parameter_key_map: Diccionario de mapeo {cv_key: db_key}.
                                  cv_key: clave interna en 'current_values'.
                                  db_key: nombre de la columna en el CSV.
        """
        self.log_directory = log_directory
        self.parameter_key_map = parameter_key_map

        os.makedirs(self.log_directory, exist_ok=True)

        # Nombre de archivo único basado solo en fecha/hora
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(
            self.log_directory,
            f"hemodialysis_log_{timestamp_str}.csv"
        )

        self.file = None
        self.csv_writer = None
        self._open_file_and_write_header()

    def _open_file_and_write_header(self):
        """
        Abre el archivo CSV y escribe la fila de cabecera.
        """
        try:
            self.file = open(self.file_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file)

            # Cabeceras: solo Timestamp + las columnas del mapeo
            headers = ['Timestamp'] + list(self.parameter_key_map.values())
            self.csv_writer.writerow(headers)
            logger.info(f"CSV Logger: Archivo '{self.file_path}' creado. Cabecera escrita.")            
        except IOError as e:            
            logger.error(f"CSV Logger Error: No se pudo abrir/escribir el archivo {self.file_path}: {e}")
            self.close()  # Intentar cerrar si falló

    def log_data(self, current_values: dict):
        """
        Registra una fila de datos en el archivo CSV.

        :param current_values: Diccionario con los valores actuales de monitorización.
        """
        if not self.csv_writer:
            logger.error("CSV Logger Error: Writer no inicializado. No se puede registrar.")
            return

        try:
            row_data = [
                # datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # Timestamp con milisegundos
                # datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]   # sigue igual, pero importa con Power Query
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]

            # Agregar valores según el orden del mapeo
            for cv_key in self.parameter_key_map.keys():
                value = current_values.get(cv_key, 'N/A')
                row_data.append(value)
            
            self.csv_writer.writerow(row_data)
            self.file.flush()  # Escribir inmediatamente al disco
        except IOError as e:
            logger.error(f"CSV Logger Error: No se pudo escribir en el archivo {self.file_path}: {e}")
        except Exception as e:
            logger.error(f"CSV Logger Error: Error inesperado al registrar: {e}")

    def close(self):
        """
        Cierra el archivo CSV. Crucial al finalizar sesión o aplicación.
        """
        if self.file and not self.file.closed:
            self.file.close()
            logger.info(f"CSV Logger: Archivo '{self.file_path}' cerrado.")

