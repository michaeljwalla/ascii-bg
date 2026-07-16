# /// script
# dependencies = [
#     "PySide6",
# ]
# ///

import sys
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

app = QApplication(sys.argv)
window = QMainWindow()

label = QLabel("Hello, Wayland!")
label.setAlignment(QtCore.Qt.AlignCenter)

window.setCentralWidget(label)
window.resize(400, 200)
window.show()
sys.exit(app.exec())

import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

# 1. Create the Qt Application
app = QApplication(sys.argv)

# 2. Create a main window and a text label
window = QMainWindow()
label = QLabel("Hello, Wayland!")

# 3. Center the text and set it as the main window display
label.setAlignment(QtCore.Qt.AlignCenter)  # Requires 'from PySide6 import QtCore'
window.setCentralWidget(label)

# 4. Show the window and start the application loop
window.resize(400, 200)
window.show()
sys.exit(app.exec())

