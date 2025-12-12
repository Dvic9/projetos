import sys
import random
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QDateTime
import Option_system
from Option_system import SistemaOption  # Importando o sistema Option

API_URL = "https://api.optionbakerysystems.com"  

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Option")
        self.setFixedSize(460, 560)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.humor = "cristão"
        self.tentativas = 0
        self.max_tentativas = 3
        self.token = None  # Guarda token JWT após login

        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background-color: #0f0f0f; border-radius: 10px;")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        self.central_widget.setPalette(palette)
        self.central_widget.setFont(QFont("Segoe UI", 14))

        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(80)
        self.shadow_effect.setColor(QColor("#00c9c9ff"))
        self.central_widget.setGraphicsEffect(self.shadow_effect)

        layout_conteudo = QVBoxLayout(self.central_widget)
        layout_conteudo.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Option\n Por favor, Digite seu Login:")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #00fff7")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_conteudo.addWidget(title)
        layout_conteudo.addSpacing(40)

        layout_conteudo.addWidget(QLabel("CPF/CNPJ", styleSheet="color: white"))
        self.username = QLineEdit()
        self.username.setStyleSheet("background-color: #1e1e1e; color: #00fff7; border-radius: 8px;")
        layout_conteudo.addWidget(self.username)

        layout_conteudo.addWidget(QLabel("Senha", styleSheet="color: white"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setStyleSheet("background-color: #1e1e1e; color: #00fff7; border-radius: 8px;")
        layout_conteudo.addWidget(self.password)
        self.password.returnPressed.connect(self.check_login)
        layout_conteudo.addSpacing(30)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #aaa; font-style: italic")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_conteudo.addWidget(self.status_label)

        login_button = QPushButton("Entrar")
        login_button.setFont(QFont("Segoe UI", 12))
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #00fff7;
                color: #0f0f0f;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00c9c9;
            }
        """)
        login_button.clicked.connect(self.check_login)
        layout_conteudo.addWidget(login_button)

        layout_conteudo.addStretch()
        footer = QLabel(f"© {QDateTime.currentDateTime().toString('yyyy')} Option")
        footer.setStyleSheet("color: #555")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_conteudo.addWidget(footer)

        layout_principal = QVBoxLayout(self)
        layout_principal.addWidget(self.central_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_principal.setContentsMargins(25, 25, 25, 25)

        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

        # Configurações de sombra animada
        self.sombra_cores = [
            QColor("#00c9c9"), QColor("#00ff95"), QColor("#00ff4c"),
            QColor("#00ff15"), QColor("#ffd900"), QColor("#ff7300"),
            QColor("#ff2600"), QColor("#ff0000"), QColor("#ff00aa"),
            QColor("#6200ff"), QColor("#001aff")
        ]
        self.sombra_index, self.next_index = 0, 1
        self.steps, self.step = 30, 0

        self.timer_cor = QTimer()
        self.timer_cor.timeout.connect(self.atualizar_sombra_cor)
        self.timer_cor.start(50)

        self.angle, self.raio = 15, 15
        self.timer_giro = QTimer()
        self.timer_giro.timeout.connect(self.atualizar_sombra_offset)
        self.timer_giro.start(50)

    def atualizar_sombra_cor(self):
        cor_atual = self.sombra_cores[self.sombra_index]
        cor_proxima = self.sombra_cores[self.next_index]
        r = cor_atual.red() + (cor_proxima.red() - cor_atual.red()) * self.step / self.steps
        g = cor_atual.green() + (cor_proxima.green() - cor_atual.green()) * self.step / self.steps
        b = cor_atual.blue() + (cor_proxima.blue() - cor_atual.blue()) * self.step / self.steps
        nova_cor = QColor(int(r), int(g), int(b))
        self.shadow_effect.setColor(nova_cor)

        self.step += 1
        if self.step > self.steps:
            self.step = 0
            self.sombra_index = self.next_index
            self.next_index = (self.next_index + 1) % len(self.sombra_cores)

    def atualizar_sombra_offset(self):
        from math import cos, sin, radians
        self.angle = (self.angle + 5) % 360
        rad = radians(self.angle)
        dx = int(self.raio * cos(rad))
        dy = int(self.raio * sin(rad))
        self.shadow_effect.setOffset(dx, dy)

    def falar_com_usuario(self, tipo):
        frases = {
            "login_sucesso": {
                "cristão": [
            "Fl 4:13 - Posso todas as coisas em Cristo que me fortalece.",
            "Cl 3:17 - Tudo quanto fizerdes, fazei-o em \n nome de Jesus, dando graças a Deus.",
            "Jo 14:6 - Jesus disse: Eu sou o caminho, a verdade e a vida.",
            "2 Co 5:17 - Quem está em Cristo é nova criação; \nas coisas antigas já passaram.",
            "Ef 6:10 - Fortalecei-vos no Senhor e na força do seu poder.",
            "Jo 1:1 - No princípio era o Verbo, e o Verbo estava com Deus,\n e o Verbo era Deus...",
            "2 Co 12:9 - Minha graça te basta; o poder de Cristo \nse aperfeiçoa na fraqueza.",
            "Hb 13:5-6 - O Senhor é meu ajudador; não temerei.",
            "Fl 1:6 - Aquele que começou a boa obra em vocês a \n completará em Cristo Jesus.",
            "Jo 16:33 - No mundo tereis aflições, mas tende bom ânimo;\n eu venci o mundo."
        ],
},
            "erro_login": {
                "cristão": [
            "Jo 1:1 - No princípio era o Verbo, e o Verbo estava com Deus,\n e o Verbo era Deus...",
            "2 Co 12:9 - Minha graça te basta; o poder de Cristo \nse aperfeiçoa na fraqueza.",
            "Hb 13:5-6 - O Senhor é meu ajudador; não temerei.",
            "Fl 1:6 - Aquele que começou a boa obra em vocês a \n completará em Cristo Jesus.",
            "Jo 16:33 - No mundo tereis aflições, mas tende bom ânimo;\n eu venci o mundo."
        ]
    }
}
        return random.choice(frases[tipo][self.humor])

    def check_login(self):
        username = self.username.text()
        senha = self.password.text()
        self.status_label.setText("Conectando...")
        QApplication.processEvents()

        try:
            response = requests.post(
                f"{API_URL}/login",
                json={"documento": username, "senha": senha},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                frase = self.falar_com_usuario("login_sucesso")
                self.status_label.setText(frase)

                def abrir_editor():
                    grupo = data.get("grupo", "default")
                    self.editor = SistemaOption(grupo, username, token=self.token)
                    self.editor.show()
                    self.close()

                QTimer.singleShot(2000, abrir_editor)

            elif response.status_code == 401:
                # Documento ou senha incorretos
                self.status_label.setText("Usuário ou senha incorretos.")

            elif response.status_code == 403:
                # Usuário existe, senha correta, mas não está ativo
                self.status_label.setText("Usuário não está ativo. Contate o administrador.")

            else:
                # Qualquer outro erro inesperado
                self.status_label.setText(f"Erro inesperado: {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.status_label.setText(f"Erro de conexão: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
