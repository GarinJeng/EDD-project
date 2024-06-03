import sys
from PyQt5.QtWidgets import QApplication
from design import Window

def except_hook(cls, exception, traceback):  # makes it so when called there's a traceback instead of an error code
  sys.__excepthook__(cls, exception, traceback)

# Calculations().compute()
if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = Window()
  sys.excepthook = except_hook
  sys.exit(app.exec_())

# Useful links:
# https://www.python.org/dev/peps/pep-0008/
# https://www.pythonguis.com/tutorials/packaging-pyqt5-pyside2-applications-windows-pyinstaller/
# https://cloudconvert.com/

# To create executable:
    # console commands
        # pip install pyinstaller
        # pyinstaller --onefile --windowed --noconsole --add-data "opple_o.ico;." --name "OppleInc_mount_instruction" --icon="opple_o.ico" main.py
    # pull file from "dist" folder in EDD_Project
    # create link to download file --> https://www.wikihow.com/Make-an-Exe-File
        # run iexpress as administator (right click on application)
        # package title: OppleInc_mount_instruction
        # user prompt: "Are you sure you want to install Opple Incorporated's "Mount Instruction" application?"
        # upload Mount Instruction Software Licensing Agreement plain text file
        # installation message: "Installation Complete"

# Image crediting (CC licensing):
# https://commons.wikimedia.org/wiki/File:Eo_circle_deep-purple_letter-o.svg#/media/File:Eo_circle_deep-purple_letter-o.svg

# exectuable with window
# pyinstaller --onefile --windowed --add-data "opple_o.ico;." --name "OppleInc_mount_instruction" --icon="opple_o.ico" main.py
# pyinstaller --onefile --name "pyfirmata_testing" testing1.py

# C:\Users\ghjen\AppData\Local\Programs\Python\Python37\python.exe
# change python to python3.7 (compatible with 2.7, 3.6, and 3.7)

# when installing pip, need to use special versions as designated in requirements:
# (pip install "PyQt5-sip==12.7.0")
# (pip install "PyQt5==5.13.1")