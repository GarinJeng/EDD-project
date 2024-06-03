from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from calculations import Calculations
import os
from pyfirmata import Arduino, util
import pyfirmata
import StepperLib
from time import sleep

basedir = os.path.dirname(__file__)

# NOTE******** STEPPER TAKES SIGNIFICANTLY LONGER WHEN TURNING COUNTERCLOCKWISE THAN CLOCKWISE (resistance levels not the same)

class Window(QWidget):
    def __init__ (self):
        super().__init__()
        self.initUI()

    def initUI(self):
        try:
            self.board = Arduino('COM4')  # Specify the correct port

            # Initialize Servo and Stepper motors
            self.board.servo_config(9)
            self.reader = util.Iterator(self.board)  # reads inputs of the circuit
            self.reader.start()

            self.servo_alt_off = 15  # initial angle off from horizon if mount is perfectly level
            self.mount_alt_off = 0  # displacement to adjust servo when mount is not level
                                    # TODO change based on IMU magnometer values (set equal to pitch)/ adjust for pitch angle
            self.alt_home = self.servo_alt_off + self.mount_alt_off
            self.az_home = 0  # displacement needed to adjust servo to **magnetic** north (true north adjusted later)
                              # TODO change based on IMU magnometer values (set equal to yaw)/ adjust for pitch angle

            # 2, 3, 4, 5 are digital pin numbers and 2038 is the number of steps in the stepper motor used
            self.motor = StepperLib.Stepper(200, self.board, self.reader, 5, 10, 8, 11)
            self.motor.set_speed(0.025)  # 12 rpm

            # writes servo to stable position (not necessarily horizon) so it doesn't automatically jerk to 0 degrees
            # on app open
            current_alt = self.board.digital[9].read()
            while (current_alt < self.servo_alt_off):  # if initial servo position is greater than horizon (most cases)
                current_alt += 1
                self.board.digital[9].write(current_alt)
                sleep(0.01 + 0.025) # briefly pauses servo between moves (the 0.025 is what it additionally takes if
                                    # the stepper motor were running [keeping speeds constant throughout the program])
            while (current_alt > self.servo_alt_off):  # if initial servo position is below horizon (unlikely)
                current_alt -= 1
                self.board.digital[9].write(current_alt)
                sleep(0.01 + 0.025)

        except:
            # used later to check if board is connected
            self.board = False

        self.steps_per_revolution = 200
        self.step_angle = 1.8
        self.gear_ratio = 40/11  # 11:40

        # PYQT5 interface
        self.resize(325, 175)
        self.center()
        # Create buttons
        self.button1 = QPushButton('Name', self)
        self.button1.setCheckable(True)
        self.button1.setChecked(True)
        self.option = 1
        self.button1.clicked[bool].connect(self.on_button1_clicked)

        self.button2 = QPushButton('Coordinates', self)
        self.button2.setCheckable(True)
        self.button2.clicked[bool].connect(self.on_button2_clicked)

        # Create input boxes
        self.object_label = QLabel("Object:", self)
        self.object_input = QLineEdit(self)
        self.altitude_label = QLabel("Altitude:", self)
        self.altitude_input = QLineEdit(self)
        self.azimuth_label = QLabel("Azimuth:", self)
        self.azimuth_input = QLineEdit(self)

        # Hide input boxes and labels initially
        self.altitude_input.hide()
        self.azimuth_input.hide()
        self.altitude_label.hide()
        self.azimuth_label.hide()

        # Create submit button
        self.submit_button = QPushButton('Submit', self)
        self.submit_button.clicked.connect(self.submit)

        # Create label for displaying "Submitted"
        self.submitted_label = QLabel('', self)
        self.submitted_label.setAlignment(Qt.AlignCenter)

        # Layout setup
        vbox = QVBoxLayout()
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.button1)
        hbox_buttons.addWidget(self.button2)
        vbox.addLayout(hbox_buttons)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.object_label)
        hbox1.addWidget(self.object_input)
        vbox.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.altitude_label)
        hbox2.addWidget(self.altitude_input)
        vbox.addLayout(hbox2)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.azimuth_label)
        hbox3.addWidget(self.azimuth_input)
        vbox.addLayout(hbox3)

        vbox.addWidget(self.submit_button)
        vbox.addWidget(self.submitted_label)

        self.setLayout(vbox)

        # icon_path = os.path.join(sys._MEIPASS, 'opple_o.ico')
        self.setWindowIcon(QIcon(os.path.join(basedir, "opple_o.ico")))
        self.setWindowTitle('Opple Incorporated')
        self.setToolTip('Opple Incorporated')

        # creating progress bar
        # self.pbar = QProgressBar(self)
        # self.pbar.hide()

        self.spacing_label = QLabel('', self)

        # Create arrow buttons
        self.up_button = QPushButton('↑', self)
        self.down_button = QPushButton('↓', self)
        self.left_button = QPushButton('←', self)
        self.right_button = QPushButton('→', self)

        # Connect click events to corresponding functions
        self.up_button.clicked.connect(self.up)
        self.down_button.clicked.connect(self.down)
        self.left_button.clicked.connect(self.left)
        self.right_button.clicked.connect(self.right)

        # Layout setup
        hbox_buttons2 = QHBoxLayout()
        hbox_buttons2.addWidget(self.left_button)
        hbox_buttons2.addWidget(self.up_button)
        hbox_buttons2.addWidget(self.down_button)
        hbox_buttons2.addWidget(self.right_button)
        vbox.addLayout(hbox_buttons2)

        # Hide arrow buttons initially
        self.hide_arrow_buttons()
        self.show()

    def on_button1_clicked(self, checked):
        if checked:
            self.hide_arrow_buttons()
            self.submitted_label.setText(' ')
            self.option = 1
            self.button2.setChecked(False)
            self.object_label.show()
            self.object_input.show()
            self.altitude_label.hide()
            self.altitude_input.hide()
            self.azimuth_label.hide()
            self.azimuth_input.hide()

    def on_button2_clicked(self, checked):
        if checked:
            self.hide_arrow_buttons()
            self.submitted_label.setText(' ')
            self.option = 2
            self.button1.setChecked(False)
            self.object_label.hide()
            self.object_input.hide()
            self.altitude_label.show()
            self.altitude_input.show()
            self.azimuth_label.show()
            self.azimuth_input.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def angleToSteps(self, angle):
        steps = (angle * 2.205 * self.steps_per_revolution * self.gear_ratio) / 360  # 2.205 is to account for error
        return round(steps)

    def moveMount(self, mag_dec, alt, az):
        # moves the mount to its altitude zero position (adjusted to 40 degrees for plane discrepancies)
        mag_dec = float(mag_dec)
        alt = float(alt)
        az = float(az)

        if self.board is False:  # checks if board port does not match with connected port
            self.submitted_label.setText('*Mount not connected -- please connect and retry*')
            return False  # "break" substitution

        if alt > 90:  # checks if user inputted altitude is above 90 degrees (scraped values defaulted not to be)
            # adjusting altitude to be equivalent angle but under 90 degrees
            alt = 180 - alt
            # adjusting azimuth to be opposite angle to compensate for altitude change
            if az >= 0:
                az = 360 - az
            elif az < 0:
                az = 360 + az

        if alt <= 0:  # checks if altitude is below or at horizon (not visible for user)
            # (limitation only brought by scraped values)
            self.submitted_label.setText('*Your object is below the horizon*')
            return False

        alt += self.alt_home  # compensating for servo offset from horizon
        az += self.az_home  # compensating for stepper offset from magnetic north
        # az += mag_dec  # compensating for stepper offset from true north  TODO check if works or not

        if az >= 360:  # corrects for possible extra turn caused by mathematical adjustments
            az -= 360
        elif az <= -360:
            az += 360

        if az >= 180:  # azimuth adjustments for movement efficiency
            az -= 360
        elif az < -180:
            az += 360

        if alt > 90:  # checks if adjusted object values are within mount range (*rotation* of 90 degrees)
            self.submitted_label.setText(
                '*Your object is outside of the mount\'s motion range \nAdjust stand angle and '
                'restart program or find new object*')  # adjusting stand would make a greater
            # incline possible
            return False

        try:
            current_alt = self.alt_home
            current_az = 0
            target_steps = self.angleToSteps(az)
            # alt = self.alt_home
            # az = 180
            print("Moving azimuth by", az, "degrees to object")
            # writing servo and stepper to object position

            self.motor.step(target_steps)

            while (current_alt < alt):
                if current_alt < alt:
                    current_alt += 1
                    self.board.digital[9].write(current_alt)
                sleep(0.02)

            self.az_home -= az  # adjusting azimuth home position for if another object is located
            self.show_arrow_buttons()
            self.submitted_label.setText("*Use buttons below to adjust mount position*")
            # TODO create function to double check azimuth error and correct position (+ or - 10 degrees of error found)
        except:
            self.submitted_label.setText('*Something went wrong with the mount direction*')

    def submit(self):
        self.submitted_label.setAlignment(Qt.AlignTop)

        object_text = self.object_input.text()
        altitude_text = self.altitude_input.text()
        azimuth_text = self.azimuth_input.text()

        if self.option == 1:
            object_text = object_text.strip()
            data = Calculations().compute(object_text)
            if data[0] is not False:
                print("\nObject:", object_text)
                print("Magnetic Declination:", data[0])
                print("Altitude:", data[1])
                print("Azimuth:", data[2])
                self.submitted_label.setText('*Submitted*')
                self.moveMount(data[0], data[1], data[2])
            else:
                self.submitted_label.setText(
                    '*There was an error with the object name -- please retry*')
        else:
            # isnumeric returns True for "" and False on negative numbers, so more conditionals are needed
            if (altitude_text.strip() != "" and azimuth_text.strip() != "" and
                    ((altitude_text.isnumeric() is True
                      and azimuth_text.isnumeric() is True) or
                     (altitude_text[0] == "-" and altitude_text[1:].isnumeric() is True
                      and azimuth_text.isnumeric() is True) or
                     (azimuth_text[0] == "-" and azimuth_text[1:].isnumeric() is True
                      and altitude_text.isnumeric() is True) or
                     (altitude_text[0] == "-" and altitude_text[1:].isnumeric() is True
                      and azimuth_text[0] == "-"
                      and azimuth_text[1:].isnumeric() is True))):
                altitude_text = float(altitude_text)
                azimuth_text = float(azimuth_text)
                if (altitude_text < 90 and altitude_text > 0) and (azimuth_text <= 180 and azimuth_text >= -180):
                    data = Calculations().compute("None")
                    print("\nObject: None")
                    print("Magnetic Declination:", data)
                    print("Altitude:", altitude_text)
                    print("Azimuth:", azimuth_text)
                    self.submitted_label.setText('*Submitted*')
                    self.moveMount(data, altitude_text, azimuth_text)
                else:
                    self.submitted_label.setText(
                        "*There was an error with your altitude/azimuth -- please review inputs\n(Altitude should be between 0 & 90 and azimuth should be between -180 & 180)*")
            else:
                self.submitted_label.setText(
                    "*There was an error with your altitude/azimuth -- please review inputs*")

    def hide_arrow_buttons(self):
        self.up_button.hide()
        self.down_button.hide()
        self.left_button.hide()
        self.right_button.hide()

    def show_arrow_buttons(self):
        self.up_button.show()
        self.down_button.show()
        self.left_button.show()
        self.right_button.show()

    def up(self):
        current_position = self.board.digital[9].read()
        # values adjusted (90 - 2) so self.down() can work after
        if (current_position <= 88) and (current_position >= (0 + self.alt_home)):
            self.board.digital[9].write(current_position + 2)
            print("Up")
            self.submitted_label.setText(" ")
        else:
            self.submitted_label.setText("*Mount cannot incline further up*")

        current_position = self.board.digital[9].read()
        print("Current position:", current_position)

    def down(self):
        current_position = self.board.digital[9].read()
        # values adjusted (self.alt_home + 2) so self.up() can work after
        if (current_position <= 90) and (current_position >= (self.alt_home + 2)):
            self.board.digital[9].write(current_position - 2)
            print("Down")
            self.submitted_label.setText(" ")
        else:
            self.submitted_label.setText("*Mount cannot incline further down*")

        current_position = self.board.digital[9].read()
        print("Current position:", current_position)

    def left(self):
        print("Left")
        self.motor.step(-2)  # Move stepper counterclockwise by one step
        self.az_home -= 2

    def right(self):
        print("Right")
        self.motor.step(2)  # Move stepper clockwise by one step
        self.az_home += 2


