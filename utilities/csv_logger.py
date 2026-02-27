import csv
import os
from datetime import datetime

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
        
        # Asegurarse de que el directorio exista
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
            print(f"CSV Logger: Archivo '{self.file_path}' creado. Cabecera escrita.")
        except IOError as e:
            print(f"CSV Logger Error: No se pudo abrir/escribir el archivo {self.file_path}: {e}")
            self.close()  # Intentar cerrar si falló

    def log_data(self, current_values: dict):
        """
        Registra una fila de datos en el archivo CSV.

        :param current_values: Diccionario con los valores actuales de monitorización.
        """
        if not self.csv_writer:
            print("CSV Logger Error: Writer no inicializado. No se puede registrar.")
            return

        try:
            row_data = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # Timestamp con milisegundos
            ]

            # Agregar valores según el orden del mapeo
            for cv_key in self.parameter_key_map.keys():
                value = current_values.get(cv_key, 'N/A')
                row_data.append(value)
            
            self.csv_writer.writerow(row_data)
            self.file.flush()  # Escribir inmediatamente al disco
        except IOError as e:
            print(f"CSV Logger Error: Error al escribir en {self.file_path}: {e}")
        except Exception as e:
            print(f"CSV Logger Error: Error inesperado al registrar: {e}")

    def close(self):
        """
        Cierra el archivo CSV. Crucial al finalizar sesión o aplicación.
        """
        if self.file and not self.file.closed:
            self.file.close()
            print(f"CSV Logger: Archivo '{self.file_path}' cerrado.")


# import csv
# import os
# from datetime import datetime

# class CsvLogger:
#     """
#     Clase para registrar datos de monitorización en un archivo CSV.
#     """
#     # def __init__(self, log_directory: str, patient_id: str, parameter_key_map: dict):
#     def __init__(self, log_directory: str,  parameter_key_map: dict):

#         """
#         Inicializa el logger CSV.

#         :param log_directory: Directorio donde se guardarán los archivos CSV.
#         :param patient_id: ID del paciente actual (usado para el nombre del archivo).
#         :param parameter_key_map: Un diccionario de mapeo {cv_key: db_key}.
#                                   cv_key: la clave interna en tu 'current_values'.
#                                   db_key: el nombre de la columna en el CSV.
#         """
#         self.log_directory = log_directory
#         # self.patient_id = patient_id
#         self.parameter_key_map = parameter_key_map
        
#         # Asegurarse de que el directorio de logs exista
#         os.makedirs(self.log_directory, exist_ok=True)

#         # Generar un nombre de archivo único basado en paciente y fecha/hora
#         timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
#         self.file_path = os.path.join(
#             self.log_directory,
#             f"hemodialysis_log_{timestamp_str}.csv"
#         )

#         self.file = None
#         self.csv_writer = None
#         self._open_file_and_write_header()

#     def _open_file_and_write_header(self):
#         """
#         Abre el archivo CSV y escribe la fila de cabecera.
#         """
#         try:
#             self.file = open(self.file_path, 'w', newline='', encoding='utf-8')
#             self.csv_writer = csv.writer(self.file)

#             # Cabeceras estándar + las definidas por el usuario
#             headers = ['Timestamp', 'Patient ID'] + list(self.parameter_key_map.values())
#             self.csv_writer.writerow(headers)
#             print(f"CSV Logger: Archivo '{self.file_path}' creado. Cabecera escrita.")
#         except IOError as e:
#             print(f"CSV Logger Error: No se pudo abrir/escribir el archivo {self.file_path}: {e}")
#             # Considera lanzar una excepción o manejar este error de forma más robusta en tu aplicación
#             self.close() # Asegurarse de cerrar si falló la apertura

#     def log_data(self, current_values: dict):
#         """
#         Registra una fila de datos en el archivo CSV.

#         :param current_values: Un diccionario que contiene todos los valores de monitorización actuales.
#         """
#         if not self.csv_writer:
#             print("CSV Logger Error: Writer no inicializado. No se puede registrar.")
#             return

#         try:
#             row_data = [
#                 datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], # Timestamp con milisegundos
#                 self.patient_id
#             ]

#             # Recorrer el mapeo para obtener los valores en el orden correcto
#             for cv_key in self.parameter_key_map.keys():
#                 # Usar .get() para evitar KeyError si un valor no está presente
#                 # Puedes usar una cadena vacía, 'N/A', o 0.0 como valor por defecto
#                 value = current_values.get(cv_key, 'N/A') 
#                 row_data.append(value)
            
#             self.csv_writer.writerow(row_data)
#             self.file.flush() # Forzar la escritura al disco inmediatamente
#         except IOError as e:
#             print(f"CSV Logger Error: Error al escribir en el archivo {self.file_path}: {e}")
#             # Esto podría indicar que el archivo fue eliminado, disco lleno, etc.
#         except Exception as e:
#             print(f"CSV Logger Error: Error inesperado al registrar datos: {e}")

#     def close(self):
#         """
#         Cierra el archivo CSV. Es crucial llamarlo al finalizar la aplicación o la sesión.
#         """
#         if self.file and not self.file.closed:
#             self.file.close()
#             print(f"CSV Logger: Archivo '{self.file_path}' cerrado.")
