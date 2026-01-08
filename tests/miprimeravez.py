from PySide6.QtWidgets import QApplication, QWidget
import sys # solo se requiere si necesitas tener acceso a argumentos de commandos
#son comandos donde los usuarios pueden interacturar con el sistema operativo o software. Ejemplo cuando ejecutas un script desde un comando de linea en cmd en el que ingresas datos 


app = QApplication(sys.argv)

window = QWidget()
window.show()
app.exec() #inicia el loop


