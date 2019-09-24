import configparser
import sys
from PySide2.QtWidgets import QApplication, QLabel, QDialog, QLineEdit, QDialogButtonBox, QFormLayout

import IniConfig


class Form(QDialog):

    cfg = configparser.ConfigParser()

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        client_ID, client_secret, user_agent = IniConfig.get_ini(self.cfg)
        self.clientID, self.clientSecret, self.userAgent = client_ID, client_secret, user_agent

        self.setWindowTitle("Ini Configurator")

        self.t_clientID = QLabel("Client ID")
        self.t_clientSecret = QLabel("Client Secret")
        self.t_userAgent = QLabel("User Agent")

        self.f_clientID = QLineEdit(client_ID)
        self.f_clientSecret = QLineEdit(client_secret)
        self.f_userAgent = QLineEdit(user_agent)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        layout = QFormLayout()
        layout.addRow(self.t_clientID, self.f_clientID)
        layout.addRow(self.t_clientSecret, self.f_clientSecret)
        layout.addRow(self.t_userAgent, self.f_userAgent)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.save)
        self.buttonBox.rejected.connect(self.cancel)

    def save(self):
        if self.f_clientID.isModified() or self.f_clientSecret.isModified() or self.f_userAgent.isModified():
            IniConfig.save_ini(self.cfg,
                               self.f_clientID.text(),
                               self.f_clientSecret.text(),
                               self.f_userAgent.text())
        self.accept()

    def cancel(self):
        self.reject()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    sys.exit(app.exec_())
