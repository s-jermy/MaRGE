import os
import sys
import csv
from configs import hw_config as hw
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QHBoxLayout, QLabel
)


class RfWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.dynamic_container = QVBoxLayout()  # Store reference
        self.layout = QVBoxLayout()
        self.main_layout.addLayout(self.layout)

        # Labels and Boxes lists
        labels = ["RF de-blanking time (us)",  # RF
                  "RF dead time (us)",
                  "Larmor frequency (MHz)",
                  "Reference time (us)",
                  "Oversampling factor",  # ADC
                  "Max readout points",
                  "Add readout points",
                  "LNA gain (dB)",
                  "RF gain min (dB)",
                  "RF gain max (dB)",
                  ]
        values = ["15",
                  "400",
                  "3.066",
                  "70",
                  "5",
                  "1e5",
                  "5",
                  "45",
                  "45",
                  "76",
                  ]

        # Dictionary to store references to input fields
        self.input_boxes = {}

        # Create blocks iteratively
        for label, value in zip(labels, values):
            row_layout = QHBoxLayout()
            label_widget = QLabel(label)
            input_box = QLineEdit(value)
            self.input_boxes[label] = input_box
            row_layout.addWidget(label_widget)
            row_layout.addWidget(input_box)
            self.layout.addLayout(row_layout)

        # Input field for RP ip address
        self.text_box_1 = QLineEdit(self)
        self.text_box_1.setPlaceholderText("RF coil ID")

        self.text_box_2 = QLineEdit(self)
        self.text_box_2.setPlaceholderText("Efficiency (rads/us/unit)")

        # Buttons
        self.add_button = QPushButton('Add', self)
        self.add_button.clicked.connect(self.add_rf)

        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_rf_entries)

        self.layout.addLayout(self.dynamic_container)

        layout = QHBoxLayout()
        layout.addWidget(self.text_box_1)
        layout.addWidget(self.text_box_2)
        layout.addWidget(self.add_button)
        layout.addWidget(self.save_button)
        self.main_layout.addStretch()
        self.main_layout.addLayout(layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle('Red Pitaya Entry')
        self.resize(400, 200)

        # Counter for IDs
        self.rf_counter = 1

        # Store added RPs in a list
        self.added_rfs = []

        # Load saved RP entries
        self.load_rf_entries()

        # Update hardware
        self.update_hw_config_rf()

    def update_hw_config_rf(self):
        hw.blkTime = float(self.input_boxes["RF de-blanking time (us)"].text())
        hw.deadTime = float(self.input_boxes["RF dead time (us)"].text())
        hw.larmorFreq = float(self.input_boxes["Larmor frequency (MHz)"].text())
        hw.oversamplingFactor = int(self.input_boxes["RF dead time (us)"].text())
        hw.maxRdPoints = int(float(self.input_boxes["Max readout points"].text()))
        hw.addRdPoints = int(self.input_boxes["Add readout points"].text())
        hw.reference_time = float(self.input_boxes["Reference time (us)"].text())
        hw.lnaGain = float(self.input_boxes["LNA gain (dB)"].text())
        hw.rf_min_gain = float(self.input_boxes["RF gain min (dB)"].text())
        hw.rf_max_gain = float(self.input_boxes["RF gain max (dB)"].text())
        for rf_id, rf_eff in self.added_rfs:
            rf_name = rf_id
            rf_value = float(rf_eff)
            hw.antenna_dict[rf_name] = rf_value

    def add_rf(self):
        rf_identifier = self.text_box_1.text().strip()
        rf_efficiency = self.text_box_2.text().strip()
        if rf_identifier and rf_efficiency:
            row_layout = QHBoxLayout()
            identifier_label = QLabel(rf_identifier)  # Unique identifier
            efficiency_label = QLabel(rf_efficiency)  # User input

            # Add Delete button for this RP entry
            delete_button = QPushButton('Delete')
            delete_button.clicked.connect(lambda: self.delete_rf(row_layout))

            row_layout.addWidget(identifier_label)
            row_layout.addWidget(efficiency_label)
            row_layout.addWidget(delete_button)

            self.dynamic_container.addLayout(row_layout)  # Add to container

            # Add the RF to the list for saving/deleting purposes
            self.added_rfs.append((rf_identifier, rf_efficiency))

            self.rf_counter += 1  # Increment counter
            self.text_box_1.clear()
            self.text_box_2.clear()

    def delete_rf(self, row_layout):
        # Remove the RP entry from the container and list
        for i, (rf_identifier, rf_efficiency) in enumerate(self.added_rfs):
            if row_layout.itemAt(0).widget().text() == rf_identifier:
                self.added_rfs.pop(i)
            if row_layout.itemAt(0).widget().text() == rf_efficiency:
                self.added_rfs.pop(i)
                break

        # Remove layout (delete UI elements)
        for i in reversed(range(row_layout.count())):
            widget = row_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.dynamic_container.update()

    def save_rf_entries(self):
        file_name = "configs/hw_rf.csv"
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Value"])
            for label, input_box in self.input_boxes.items():
                writer.writerow([label, input_box.text()])  # Write each pair
            for rf_identifier, rf_efficiency in self.added_rfs:
                writer.writerow([rf_identifier, rf_efficiency])
        self.update_hw_config_rf()
        print(f"Data saved for rf.")

    def load_rf_entries(self):
        file_name = "configs/hw_rf.csv"
        if os.path.exists(file_name):
            with open(file_name, 'r') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header row
                for row in reader:
                    label, value = row
                    if label in self.input_boxes:
                        self.input_boxes[label].setText(value)
                    else:
                        self.added_rfs.append((label, value))
                        self.add_rf_from_data(label, value)
        else:
            print("No hardware configuration loaded for red pitayas.")

    def add_rf_from_data(self, rf_id, rf_ef):
        row_layout = QHBoxLayout()
        identifier_label = QLabel(rf_id)
        text_label = QLabel(rf_ef)

        # Add Delete button for this RP entry
        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(lambda: self.delete_rf(row_layout))

        row_layout.addWidget(identifier_label)
        row_layout.addWidget(text_label)
        row_layout.addWidget(delete_button)

        self.dynamic_container.addLayout(row_layout)  # Add to container


if __name__ == '__main__':
    # Run the application
    app = QApplication(sys.argv)
    widget = RfWidget()
    widget.show()
    sys.exit(app.exec())