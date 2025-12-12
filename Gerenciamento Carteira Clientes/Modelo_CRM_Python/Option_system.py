import sys
import math
import psutil 
import re
import os
import hashlib
import subprocess
import requests
from collections import Counter
import json
import time
import threading
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QTimer, QDate, QPoint, QRect, QRegularExpression 
from PySide6.QtCharts import QChart, QChartView, QHorizontalBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QBarSeries
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap, QPainter, QPen, QPolygon, QCursor, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QMessageBox,
    QWidget, QVBoxLayout, QRadioButton, QButtonGroup, QPushButton,
    QHBoxLayout, QStackedWidget, QProgressBar, QTableWidget,
    QTableWidgetItem, QCheckBox, QHeaderView, QGroupBox, QGridLayout, QSpinBox, QDateEdit, QFrame, QLineEdit, QComboBox, QListWidget, QListWidgetItem, QSizePolicy,
    QAbstractItemView, QScrollArea, QMenu, QTableView, QInputDialog, QDialog, QCompleter, QToolTip
)
import psycopg2

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
API_URL = "https://api.optionbakerysystems.com"  

MAQUINAS = [
    "BOLEADORA RB80 L 220V",
    "BOLEADORA RB80 L 380V",
    "BOLEADORA RB80R 220V",
    "BOLEADORA RB80R 380V (NOVO)",
    "BOLEADORA RB80R 380V",
    "CORTADOR E ELEVADOR DE MASSAS",
    "DIVISORA PARTA 220V",
    "DIVISORA VOLUMETRICA DV2000",
    "EMBALADORA BETENDORF",
    "EMBALADORA SS-65 L 220V",
    "EMBALADORA SS-65 L 380V",
    "EMBALADORA SS-65 R 220V",
    "EMBALADORA SS-65 R 380V",
    "ENSACADORA ES25",
    "ENSACADORA NANO 220V",
    "ENSACADORA SEMI-AUTOMATICA - 220V",
    "ESTEIRA COLETORA DE PAES - 220V",
    "ESTEIRA ELEVADORA DE MASSAS - 220V",
    "FATIADOORA BETENDORF",
    "FATIADORA BS-65 L 220V",
    "FATIADORA BS-65 L 380V",
    "FATIADORA BS-65 R 220V",
    "FATIADORA BS-65 R 380V",
    "FATIADORA BS40 220V",
    "FATIADORA DS25",
    "FATIADORA PAULISTINHA 380V",
    "FITILHADOR ELETRONICO BETENDORF",
    "FITILHADOR ELETRONICO T65R SERVO - 220V",
    "FITILHADOR ELETRONICO T65L SERVO - 220V",
    "FITILHADOR MECANICO",
    "FITILHADOR MECANICO USADO",
    "FITILHADOR MECANICO BURFORD",
    "FITILHADOR T7 L 220V (NOVO)",
    "FITILHADOR T7 L 220V",
    "FITILHADOR T7 R 220V (NOVO)",
    "FITILHADOR T7 R 220V",
    "GRANULADOR AP10L",
    "GRANULADOR AP10R 380V",
    "GRANULADOR AP10S",
    "GRANULADOR AP12 380V",
    "MODELADORA PMS40-L (IBR) 220V (NOVO)",
    "MODELADORA PMS40-L (IBR) 380V (NOVO)",
    "MODELADORA PMS40-R (IBR) 220V (NOVO)",
    "MODELADORA PMS40-R (IBR) 380V (NOVO)",
    "MODELADORA PMS40R 220V",
    "CURVA MODELADORA PMS80 L",
    "CURVA MODELADORA PMS80 R",
    "MODELADORA PMS80 L 220V",
    "MODELADORA PMS80 L 380V",
    "MODELADORA PMS80 R 220V",
    "MODELADORA PMS80 R 380V",
    "PEDESTAL GRANULADOR AP12 380V",
    "TRANSPORTE TR17 L 220V (NOVO)",
    "TRANSPORTE TR17 L ELETRÔNICO",
    "TRANSPORTE TR17 L MECÂNICO",
    "TRANSPORTE TR17 R 220V (NOVO)",
    "TRANSPORTE TR17 R ELETRÔNICO",
    "TRANSPORTE TR17 R MECÂNICO",
    "TRANSPORTE TR27 L 220V (NOVO)",
    "TRANSPORTE TR27 R 220V (NOVO)",
    "TRANSPORTE TR28 L 220V",
    "TRANSPORTE TR28 L 380V",
    "TRANSPORTE TR28 R 220V",
    "TRANSPORTE TR28 R 380V",
    "TRANSPORTE TR29",
    "TRANSPORTE TR30",
    "TRANSPORTE TR31 - 380V",
    "TRANSPORTE TR32",
    "TRANSPORTE TR33",
    "TRANSPORTE TR34",
    "TRANSPORTE TR35",
    "TRANSPORTE TR46 L",
    "TRANSPORTE TR49R 380V",
    "TRANSPORTE TR50 R RETO",
    "TRANSPORTE TR52 L RETO",
  ]
DB_URL = os.getenv("DATABASE_URL", "DATABASE_URL")

with open("componentes.json", "r", encoding="utf-8") as arquivo:
    COMPONENTES = json.load(arquivo)


def criar_icone_notificacao(cor="black", tamanho=32, numero=0):
    pixmap = QPixmap(tamanho, tamanho)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Desenha o losango
    pen = QPen(QColor(cor))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.setBrush(QColor(cor))

    pontos = QPolygon([
        QPoint(tamanho // 2, 0),
        QPoint(tamanho, tamanho // 2),
        QPoint(tamanho // 2, tamanho),
        QPoint(0, tamanho // 2)
    ])
    painter.drawPolygon(pontos)

    # Desenha o badge com número (se houver notificações)
    if numero > 0:
        badge_size = 24
        badge_color = QColor("red")
        text_color = QColor("white")

        # Círculo no canto superior direito
        badge_rect = QRect(tamanho - badge_size, 0, badge_size, badge_size)
        painter.setBrush(badge_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(badge_rect)

        # Número dentro do círculo
        font = painter.font()
        font.setBold(True)
        font.setPointSize(15)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(badge_rect, Qt.AlignCenter, str(numero))

    painter.end()
    return QIcon(pixmap)


def formatar_cnpj(cnpj):
    cnpj = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj) != 14:
        return cnpj  # Retorna como está se não tiver 14 dígitos
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

LOG_FILE = "clientes.log"


class SistemaOption(QMainWindow):
    def __init__(self, grupo_usuario, documento, token=None):
        super().__init__()
        self.grupo = grupo_usuario
        self.documento = documento
        self.token = token

        container = QWidget()
        layout = QVBoxLayout(container)


        self.setCentralWidget(container)
        self.cliente_em_edicao = None
        self.setWindowTitle("Sistema Option")
        self.resize(800, 600)
        self.tema_atual = "escuro"
        self.conn = psycopg2.connect(DB_URL)
        self.criar_tabela_clientes()

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pecas_clientes (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                maquina TEXT NOT NULL,
                peca TEXT NOT NULL,
                ultima_compra TEXT
            )
        """)

        # Verifica se a coluna existe antes de criar
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='pecas_clientes' AND column_name='proximo_lembrete'
        """)
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE pecas_clientes ADD COLUMN proximo_lembrete TEXT")

        self.conn.commit()



        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.Window)  # mantém a barra de título padrão

        self.setAttribute(Qt.WA_TranslucentBackground)

        # ===== Container principal =====
        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(10)
        self.setCentralWidget(container)


        menu_bar = self.menuBar()
        self.setMenuBar(menu_bar)  # FIXA no topo

        # Flag do tema (pode depois ser atualizado quando o usuário trocar)
        self.tema_escuro = True  

        # Botão de notificações (ícone do sino)
        numero_notificacoes = self.contar_notificacoes()

            
        self.btn_notificacoes = QPushButton()
        self.btn_notificacoes.setIcon(
            criar_icone_notificacao(
                cor="white" if self.tema_escuro else "black",
                tamanho=32,
                numero=numero_notificacoes
            )
        )
        self.btn_notificacoes.setFixedSize(36, 36)
        self.btn_notificacoes.setStyleSheet("border: none;")
        
        if self.grupo == "cliente":
            self.btn_notificacoes.setVisible(False) # Esconde o botão de notificações para clientes

        # Coloca o losango no canto superior direito da barra de menus
        self.menuBar().setCornerWidget(self.btn_notificacoes, Qt.TopRightCorner)
        self.btn_notificacoes.setToolTip("Notificações")
        self.btn_notificacoes.clicked.connect(self.abrir_notificacoes)  # Muda para a página de notificações

        # ===== Menu =====
        inicio_action = QAction("&Início", self)
        inicio_action.setShortcut("Ctrl+Left")
        inicio_action.triggered.connect(lambda: self.stack.setCurrentIndex(0))
        menu_bar.addAction(inicio_action)

        clientes_action = QAction("&Cliente", self)
        clientes_action.setShortcut("Ctrl+A")
        clientes_action.triggered.connect(self.abrir_clientes)
        menu_bar.addAction(clientes_action)

        dashboard_action = QAction("&Dashboard", self)
        dashboard_action.setShortcut("Ctrl+D")
        dashboard_action.triggered.connect(lambda: self.stack.setCurrentIndex(6))
        menu_bar.addAction(dashboard_action)

        config_action = QAction("&Configurações", self)
        config_action.setShortcut("Ctrl+S")
        config_action.triggered.connect(lambda: self.stack.setCurrentIndex(2))
        menu_bar.addAction(config_action)

        sair_action = QAction("&Sair", self)
        sair_action.setShortcut("Alt+X")
        sair_action.triggered.connect(lambda: self.stack.setCurrentIndex(3))
        menu_bar.addAction(sair_action)


        # ===== Área central com QStackedWidget =====
        self.central_box = QWidget()
        self.central_box.setStyleSheet("""
            background-color: #222;
            border-radius: 14px;
            color: white;
            font-size: 16px;
        """)
        container_layout.addWidget(self.central_box)

        self.stack = QStackedWidget()
        layout_central = QVBoxLayout(self.central_box)
        layout_central.setContentsMargins(0, 0, 0, 0)
        layout_central.addWidget(self.stack)

        # ===== Componentes do Carrossel (MOVIMOS PARA CIMA) =====
        self.carousel_stack = QStackedWidget()
        self.legenda_label = QLabel()
        self.timer_carrossel = QTimer(self)
        self.imagens = []
        self.legendas = []

        # ===== Páginas =====
        self.stack.addWidget(self.criar_pagina_inicio())         # index 0
        inicio_action.triggered.connect(lambda: (self.stack.setCurrentIndex(0), self.atualizar_dashboard()))
        self.stack.addWidget(self.criar_pagina_clientes())      # index 1
        self.stack.addWidget(self.criar_pagina_configuracoes())  # index 2
        self.stack.addWidget(self.criar_pagina_sair())           # index 3
        self.stack.addWidget(self.criar_pagina_cadastro_cliente())  # index 4
        self.stack.addWidget(self.criar_pagina_notificacoes())  # index 5
        self.stack.addWidget(self.criar_pagina_dashboard())  # index 6

        # Aplica o tema escuro logo no início
        self.tema_atual = "escuro"
        self.set_tema("escuro")


    def abrir_clientes(self):
        if self.grupo == "cliente":
            self.editar_cliente_por_cnpj(self.documento)
        else:
            self.stack.setCurrentIndex(1)

    def abrir_notificacoes(self):
        self.contar_notificacoes()
        self.atualizar_notificacoes()
        self.atualizar_icone_notificacoes()
        self.stack.setCurrentIndex(5)
            
    def atualizar_icone_notificacoes(self):
        total = self.contar_notificacoes()
        nova_cor = "white" if self.tema_escuro else "black"
        novo_icone = criar_icone_notificacao(cor=nova_cor, tamanho=32, numero=total)
        self.btn_notificacoes.setIcon(novo_icone)

    def carregar_paises_filtro(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT pais FROM clientes
            WHERE pais IS NOT NULL AND pais != ''
        """)
        paises = [row[0] for row in cursor.fetchall()]
        self.combo_pais_filtro.clear()
        self.combo_pais_filtro.addItem("")
        self.combo_pais_filtro.addItems(sorted(paises))


    def obter_coordenadas_por_status(self, status):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT nome, nome_fantasia, lat, lon
            FROM clientes
            WHERE status = %s
            AND lat IS NOT NULL
            AND lon IS NOT NULL
        """, (status,))
        resultados = cursor.fetchall()

        coordenadas = [
            {
                "label": nome_fantasia if nome_fantasia else nome,
                "lat": lat,
                "lon": lon
            }
            for nome, nome_fantasia, lat, lon in resultados
        ]
        return coordenadas

    def atualizar_notificacoes(self):
        # Limpa a lista
        self.lista_notificacoes.clear()
        self.checkboxes_notificacoes = []

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.id, c.nome, pc.maquina, pc.peca, pc.ultima_compra, 
                c.lembrete_dias, pc.proximo_lembrete
            FROM pecas_clientes pc
            JOIN clientes c ON c.id = pc.cliente_id
            WHERE pc.ultima_compra IS NOT NULL 
            AND c.lembrete_dias > 0
        """)

        hoje = datetime.today().date()
        notificacoes = []

        for cliente_id, nome, maquina, peca, ultima_compra, lembrete_dias, prox_lembrete in cursor.fetchall():
            try:
                data_base = datetime.strptime(ultima_compra, "%Y-%m-%d").date()
                data_lembrete = data_base + timedelta(days=lembrete_dias)
                if prox_lembrete:
                    data_lembrete = datetime.strptime(prox_lembrete, "%Y-%m-%d").date()

                if data_lembrete <= hoje:
                    dias_atraso = (hoje - data_lembrete).days
                    texto = f"{nome} precisa de atenção para a peça {peca}, da máquina {maquina}."
                    notificacoes.append((cliente_id, texto, maquina, peca, dias_atraso))
            except Exception as e:
                print(f"Erro ao processar notificação: {e}")

        # Ordena por dias de atraso (maior primeiro)
        notificacoes.sort(key=lambda x: x[4], reverse=True)

        for cliente_id, texto, maquina, peca, dias_atraso in notificacoes:
            # Checkbox individual
            cb = QCheckBox()
            cb.setProperty('id_cliente', cliente_id)
            cb.stateChanged.connect(self.on_notificacao_checkbox_state_changed)
            self.checkboxes_notificacoes.append(cb)

            # Texto da notificação
            lbl = QLabel(texto)
            lbl.setWordWrap(True)

            # === ÁREA DE LAYOUT SEPARADA (checkbox e texto) ===
            linha = QWidget()
            linha.setStyleSheet("""
                QWidget {
                    border: 1px solid #555;
                    border-radius: 6px;
                    background-color: #2b2b2b;
                }
            """)

            hbox = QHBoxLayout(linha)
            hbox.setContentsMargins(6, 6, 6, 6)
            hbox.setSpacing(10)

            # Área fixa da checkbox
            area_cb = QWidget()
            area_cb.setFixedWidth(40)
            layout_cb = QHBoxLayout(area_cb)
            layout_cb.setContentsMargins(0, 0, 0, 0)
            layout_cb.setAlignment(Qt.AlignCenter)
            frame_cb = QFrame()
            frame_cb.setStyleSheet("border: none; background: transparent;")
            layout_frame = QHBoxLayout(frame_cb)
            layout_frame.setContentsMargins(0, 0, 0, 0)
            layout_frame.setAlignment(Qt.AlignCenter)
            layout_frame.addWidget(cb)
            layout_cb.addWidget(frame_cb)

            # Área do texto
            area_texto = QWidget()
            layout_texto = QHBoxLayout(area_texto)
            layout_texto.setContentsMargins(0, 0, 0, 0)
            layout_texto.addWidget(lbl)

            hbox.addWidget(area_cb)
            hbox.addWidget(area_texto, stretch=1)

            # Adiciona item no QListWidget
            item = QListWidgetItem()
            item.setSizeHint(linha.sizeHint())
            self.lista_notificacoes.addItem(item)
            self.lista_notificacoes.setItemWidget(item, linha)

            # Dados extras
            item.setData(Qt.UserRole, (cliente_id, maquina, peca))

        self.lista_notificacoes.itemClicked.connect(self.abrir_cliente_via_notificacao)

    def excluir_notificacao(self):
        itens_selecionados = []
        for i in range(self.lista_notificacoes.count()):
            item = self.lista_notificacoes.item(i)
            widget = self.lista_notificacoes.itemWidget(item)
            cb = widget.findChild(QCheckBox) if widget else None
            if cb and cb.isChecked():
                itens_selecionados.append(item)

        if not itens_selecionados:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos uma notificação para excluir.")
            return

        confirmar = QMessageBox.question(
            self,
            "Excluir Notificações",
            f"Tem certeza que deseja excluir {len(itens_selecionados)} notificações?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirmar != QMessageBox.Yes:
            return

        cursor = self.conn.cursor()
        for item in itens_selecionados:
            cliente_id, maquina, peca = item.data(Qt.UserRole)
            cursor.execute("""
    DELETE FROM pecas_clientes
    WHERE cliente_id = %s AND maquina = %s AND peca = %s
""", (cliente_id, maquina, peca))

        self.conn.commit()
        self.contar_notificacoes()
        self.atualizar_notificacoes()
        self.atualizar_icone_notificacoes()
        QMessageBox.information(self, "Sucesso", "Notificações excluídas com sucesso!")

    def cb_notif_selecionar_todos_clicked(self):
        total = len(self.checkboxes_notificacoes)
        if total == 0:
            return

        marcados = sum(1 for cb in self.checkboxes_notificacoes if cb.isChecked())
        target = (marcados != total)  # se nem todos, marca todos; se todos, desmarca todos

        for cb in self.checkboxes_notificacoes:
            cb.blockSignals(True)
            cb.setChecked(target)
            cb.blockSignals(False)

        self.cb_notif_selecionar_todos.blockSignals(True)
        self.cb_notif_selecionar_todos.setCheckState(Qt.Checked if target else Qt.Unchecked)
        self.cb_notif_selecionar_todos.blockSignals(False)


    def on_notificacao_checkbox_state_changed(self, *args):
        total = len(self.checkboxes_notificacoes)
        marcados = sum(1 for cb in self.checkboxes_notificacoes if cb.isChecked())

        self.cb_notif_selecionar_todos.blockSignals(True)
        if marcados == 0:
            self.cb_notif_selecionar_todos.setCheckState(Qt.Unchecked)
        elif marcados == total:
            self.cb_notif_selecionar_todos.setCheckState(Qt.Checked)
        else:
            self.cb_notif_selecionar_todos.setCheckState(Qt.PartiallyChecked)
        self.cb_notif_selecionar_todos.blockSignals(False)
    
    def filtrar_clientes_por_maquina(self, nome_maquina):
        self.combo_maquina_filtro.setCurrentText(nome_maquina)
        self.stack.setCurrentIndex(1)  # Vai para aba Clientes
        self.carregar_clientes()       # Recarrega com filtro aplicado
    
            
    def filtrar_cliente_por_nome(self, texto_filtro):
        texto_filtro = texto_filtro.lower()  # Para não diferenciar maiúsculas/minúsculas
        for row in range(self.tabela_clientes.rowCount()):
            # Supondo que o nome do cliente esteja na coluna 1
            item = self.tabela_clientes.item(row, 1)
            if item:
                nome = item.text().lower()
                self.tabela_clientes.setRowHidden(row, texto_filtro not in nome)


    def abrir_cliente_por_id(self, cliente_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        if cliente:
            self.stacked_widget.setCurrentWidget(self.pagina_cadastro_clientes)
            self.preencher_formulario_cliente(cliente)


    def abrir_cliente_via_notificacao(self, item):
        cliente_id, _, _ = item.data(Qt.UserRole)
        self.editar_cliente(cliente_id)  # column fica None automaticamente


    def abrir_tela_cliente(self, cliente_id: int):
        # Vai para a aba de clientes
        self.stack.setCurrentIndex(1)

        # Garante que a tabela está populada
        self.carregar_clientes()

        tabela = self.tabela_clientes
        id_col = self._coluna_por_titulo(tabela, {"id", "código", "codigo"})
        if id_col is None:
            id_col = 0

        for r in range(tabela.rowCount()):
            cell_widget = tabela.cellWidget(r, 0)
            cb = cell_widget.findChild(QCheckBox) if cell_widget else None
            if cb and cb.property('id_cliente') == cliente_id:
                # Seleciona e rola até o cliente
                tabela.selectRow(r)
                tabela.scrollToItem(tabela.item(r, 1))
                # Chama edição como se tivesse dado duplo clique no nome
                self.editar_cliente(r, 1)
                return

    def _coluna_por_titulo(self, tabela, nomes_possiveis):
        nomes = {n.lower() for n in nomes_possiveis}
        try:
            for c in range(tabela.columnCount()):
                header = tabela.horizontalHeaderItem(c)
                if header and header.text().strip().lower() in nomes:
                    return c
        except Exception:
            pass
        return None


    def carregar_estados_filtro(self):
        cursor = self.conn.cursor()
        query = """
            SELECT DISTINCT estado FROM clientes
            WHERE estado IS NOT NULL AND estado != ''
        """
        params = []
        if self.combo_pais_filtro.currentText().strip():
            query += " AND pais = %s"
            params.append(self.combo_pais_filtro.currentText().strip())
        cursor.execute(query, params)
        estados = [row[0] for row in cursor.fetchall()]
        self.combo_estado_filtro.clear()
        self.combo_estado_filtro.addItem("")
        self.combo_estado_filtro.addItems(sorted(estados))


    def carregar_regioes_filtro(self):
        """Carrega as regiões disponíveis no combo_regiao_filtro."""
        self.combo_regiao_filtro.clear()
        self.combo_regiao_filtro.addItem("Todas")  # opção padrão

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT regiao
            FROM clientes
            WHERE regiao IS NOT NULL AND regiao != ''
            ORDER BY regiao
        """)
        regioes = [row[0] for row in cursor.fetchall()]
        self.combo_regiao_filtro.addItems(regioes)


    def carregar_cidades_filtro(self):
        cursor = self.conn.cursor()
        query = """
            SELECT DISTINCT municipio FROM clientes
            WHERE municipio IS NOT NULL AND municipio != ''
        """
        params = []
        if self.combo_pais_filtro.currentText().strip():
            query += " AND pais = %s"
            params.append(self.combo_pais_filtro.currentText().strip())
        if self.combo_estado_filtro.currentText().strip():
            query += " AND estado = %s"
            params.append(self.combo_estado_filtro.currentText().strip())
        cursor.execute(query, params)
        cidades = [row[0] for row in cursor.fetchall()]
        self.combo_municipio_filtro.clear()
        self.combo_municipio_filtro.addItem("")
        self.combo_municipio_filtro.addItems(sorted(cidades))


    def carregar_bairros_filtro(self):
        cursor = self.conn.cursor()
        query = """
            SELECT DISTINCT bairro FROM clientes
            WHERE bairro IS NOT NULL AND bairro != ''
        """
        params = []
        if self.combo_pais_filtro.currentText().strip():
            query += " AND pais = %s"
            params.append(self.combo_pais_filtro.currentText().strip())
        if self.combo_estado_filtro.currentText().strip():
            query += " AND estado = %s"
            params.append(self.combo_estado_filtro.currentText().strip())
        if self.combo_municipio_filtro.currentText().strip():
            query += " AND municipio = %s"
            params.append(self.combo_municipio_filtro.currentText().strip())
        cursor.execute(query, params)
        bairros = [row[0] for row in cursor.fetchall()]
        self.input_bairro_filtro.clear()
        self.input_bairro_filtro.addItem("")
        self.input_bairro_filtro.addItems(sorted(bairros))


    def carregar_ruas_filtro(self):
        cursor = self.conn.cursor()
        query = """
            SELECT DISTINCT rua FROM clientes
            WHERE rua IS NOT NULL AND rua != ''
        """
        params = []
        if self.combo_pais_filtro.currentText().strip():
            query += " AND pais = %s"
            params.append(self.combo_pais_filtro.currentText().strip())
        if self.combo_estado_filtro.currentText().strip():
            query += " AND estado = %s"
            params.append(self.combo_estado_filtro.currentText().strip())
        if self.combo_municipio_filtro.currentText().strip():
            query += " AND municipio = %s"
            params.append(self.combo_municipio_filtro.currentText().strip())
        if self.input_bairro_filtro.currentText().strip():
            query += " AND bairro = %s"
            params.append(self.input_bairro_filtro.currentText().strip())
        cursor.execute(query, params)
        ruas = [row[0] for row in cursor.fetchall()]
        self.input_rua_filtro.clear()
        self.input_rua_filtro.addItem("")
        self.input_rua_filtro.addItems(sorted(ruas))



    def adiar_notificacao(self):
        itens_selecionados = []
        for i in range(self.lista_notificacoes.count()):
            item = self.lista_notificacoes.item(i)
            widget = self.lista_notificacoes.itemWidget(item)
            cb = widget.findChild(QCheckBox) if widget else None
            if cb and cb.isChecked():
                itens_selecionados.append(item)

        if not itens_selecionados:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos uma notificação para adiar.")
            return

        dias, ok = QInputDialog.getInt(self, "Adiar lembrete", "Quantos dias deseja adiar?", 7, 1, 365)
        if not ok:
            return

        cursor = self.conn.cursor()
        for item in itens_selecionados:
            cliente_id, maquina, peca = item.data(Qt.UserRole)
            nova_data = (datetime.today().date() + timedelta(days=dias)).strftime("%Y-%m-%d")
            cursor.execute("""
    UPDATE pecas_clientes
    SET proximo_lembrete = %s
    WHERE cliente_id = %s AND maquina = %s AND peca = %s
""", (nova_data, cliente_id, maquina, peca))

        self.conn.commit()
        self.contar_notificacoes()
        self.atualizar_notificacoes()
        self.atualizar_icone_notificacoes()


    def contar_notificacoes(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.id, pc.ultima_compra, c.lembrete_dias, pc.proximo_lembrete
            FROM pecas_clientes pc
            JOIN clientes c ON c.id = pc.cliente_id
            WHERE pc.ultima_compra IS NOT NULL AND c.lembrete_dias > 0
        """)

        hoje = datetime.today().date()
        total = 0

        for _, ultima_compra, lembrete_dias, prox_lembrete in cursor.fetchall():
            try:
                data_base = datetime.strptime(ultima_compra, "%Y-%m-%d").date()
                data_lembrete = data_base + timedelta(days=lembrete_dias)
                if prox_lembrete:
                    data_lembrete = datetime.strptime(prox_lembrete, "%Y-%m-%d").date()
                if data_lembrete <= hoje:
                    total += 1
            except:
                continue
                
        return total

    # 1️⃣ Função para criar a página de notificações
    def criar_pagina_notificacoes(self):
        
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Notificações")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(label)


        # Campo de filtro
        linha_filtro = QHBoxLayout()

        self.input_filtro_notificacoes = QLineEdit()
        self.input_filtro_notificacoes.setPlaceholderText("Filtrar...")
        linha_filtro.addWidget(self.input_filtro_notificacoes)

        btn_adiar = QPushButton("Adiar")
        btn_adiar.setFixedWidth(80)  # ou outro valor menor
        btn_adiar.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #a33;
                        border-radius: 15px;
                        padding: 5px 10px;
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #a33;
                    }
                """)
        btn_adiar.clicked.connect(self.adiar_notificacao)
        linha_filtro.addWidget(btn_adiar)

        btn_excluir = QPushButton("Excluir")
        btn_excluir.setFixedWidth(80)
        btn_excluir.setStyleSheet("""
            QPushButton {
                border: 2px solid #a33;
                border-radius: 15px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #a33;
            }
        """)
        btn_excluir.clicked.connect(self.excluir_notificacao)
        linha_filtro.addWidget(btn_excluir)



        layout.addLayout(linha_filtro)
        # Conecta o filtro à função
        self.input_filtro_notificacoes.textChanged.connect(self.filtrar_notificacoes_por_nome)
        
        # Checkbox Selecionar todos
        self.cb_notif_selecionar_todos = QCheckBox("Selecionar todos")
        self.cb_notif_selecionar_todos.clicked.connect(self.cb_notif_selecionar_todos_clicked)
        layout.addWidget(self.cb_notif_selecionar_todos)
        
        # Lista de notificações
        self.lista_notificacoes = QListWidget()
        layout.addWidget(self.lista_notificacoes)
        # Container: neutro, sem borda nem fundo pintado
        self.lista_notificacoes.setFrameStyle(QFrame.NoFrame)
        self.lista_notificacoes.setStyleSheet("""
            QListWidget {
                background: transparent; /* herda a cor do widget pai */
            }
        """)
        self.lista_notificacoes.setSpacing(8)  # espaço entre os itens

        # Cartão: aqui sim entra o estilo completo
        linha = QWidget()
        linha.setStyleSheet("""
            QWidget {
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px;
                background-color: #2b2b2b;
            }
        """)





        return pagina
    
    
    
    def atualizar_checkbox_geral_notificacoes(self):
        total = self.lista_notificacoes.count()
        if total == 0:
            self.cb_notif_selecionar_todos.setCheckState(Qt.Unchecked)
            return

        marcados = 0
        for i in range(total):
            item = self.lista_notificacoes.item(i)
            widget = self.lista_notificacoes.itemWidget(item)
            cb = widget.findChild(QCheckBox) if widget else None
            if cb and cb.isChecked():
                marcados += 1

        if marcados == 0:
            self.cb_notif_selecionar_todos.setCheckState(Qt.Unchecked)
        elif marcados == total:
            self.cb_notif_selecionar_todos.setCheckState(Qt.Checked)
        else:
            self.cb_notif_selecionar_todos.setCheckState(Qt.PartiallyChecked)
    
    
    def obter_lat_lon(self, endereco: str):
        """Consulta Nominatim e retorna latitude e longitude"""
        params = {"q": endereco, "format": "json", "limit": 1}
        try:
            response = requests.get(
                NOMINATIM_URL,
                params=params,
                timeout=15,
                headers={"User-Agent": "PythonApp"}
            )
            response.raise_for_status()
            dados = response.json()
            if dados:
                return float(dados[0]["lat"]), float(dados[0]["lon"])
            return None, None
        except Exception as e:
            print(f"[ERRO] Geocoding falhou para '{endereco}': {e}")
            return None, None
    
    def marcar_todas_notificacoes(self, state):
        for i in range(self.lista_notificacoes.count()):
            item = self.lista_notificacoes.item(i)
            widget = self.lista_notificacoes.itemWidget(item)
            if not widget:
                continue
            cb = widget.findChild(QCheckBox)
            if cb:
                cb.setChecked(state == Qt.Checked)
            
    def on_dashboard_checkbox_changed(self):
        # Mostra o botão se pelo menos uma checkbox estiver marcada
        if self.cb_ativo.isChecked() or self.cb_prospect.isChecked() or self.cb_lead.isChecked():
            self.btn_relatorio.setVisible(True)
        else:
            self.btn_relatorio.setVisible(False)

    def filtrar_notificacoes_por_nome(self, texto_filtro):
        texto_filtro = texto_filtro.lower()
        for i in range(self.lista_notificacoes.count()):
            item = self.lista_notificacoes.item(i)
            widget = self.lista_notificacoes.itemWidget(item)
            if widget:
                lbl = widget.findChild(QLabel)
                if lbl:
                    texto = lbl.text().lower()
                    item.setHidden(texto_filtro not in texto)



    def filtrar_maquinas_por_categoria(self, categoria):
        """
        Mostra todas as máquinas como botões.
        Ao clicar em uma máquina, filtra clientes ativos daquela máquina
        no Estado/Região selecionado.
        """
        cursor = self.conn.cursor()

        # Busca todos os clientes ativos no estado ou região
        cursor.execute("""
            SELECT maquinas
            FROM clientes
            WHERE status = 'Cliente ativo'
            AND (estado = %s OR regiao = %s)
            AND maquinas IS NOT NULL
            AND maquinas <> ''
        """, (categoria, categoria))

        linhas = cursor.fetchall()

        # Quebra as máquinas separadas por ';' e conta
        todas_maquinas = []
        for (maquinas_str,) in linhas:
            maquinas = [m.strip() for m in maquinas_str.split(";") if m.strip()]
            todas_maquinas.extend(maquinas)

        contagem = Counter(todas_maquinas)

        # === Cria página dinâmica ===
        pagina = QWidget()
        layout = QVBoxLayout(pagina)

        titulo = QLabel(f"Máquinas em {categoria}")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Cria um botão para cada máquina encontrada
        for maq, qtd in contagem.most_common():
            btn = QPushButton(f"{maq} ({qtd} Vendas)")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border-radius: 8px;
                    padding: 6px 12px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #666;
                }
            """)

            # Conecta o clique do botão ao filtro
            btn.clicked.connect(lambda _, m=maq: self._filtrar_clientes_maquina_categoria(m, categoria))
            layout.addWidget(btn)

        # Adiciona a página no stack e navega até ela
        self.stack.addWidget(pagina)
        self.stack.setCurrentWidget(pagina)


    def _filtrar_clientes_maquina_categoria(self, maquina, categoria):
        """
        Aplica o filtro de clientes ativos por máquina + estado/região.
        """
        # Força status = Cliente ativo
        self.cb_ativo.setChecked(True)
        self.cb_prospect.setChecked(False)
        self.cb_lead.setChecked(False)
        if hasattr(self, "combo_status_filtro"):
            self.combo_status_filtro.setCurrentText("Cliente ativo")

        # Aplica categoria no combo certo
        if categoria in [self.combo_estado_filtro.itemText(i) for i in range(self.combo_estado_filtro.count())]:
            self.combo_estado_filtro.setCurrentText(categoria)
        elif categoria in [self.combo_regiao_filtro.itemText(i) for i in range(self.combo_regiao_filtro.count())]:
            self.combo_regiao_filtro.setCurrentText(categoria)

        # Aplica filtro de máquina
        self.combo_maquina_filtro.setCurrentText(maquina)

        # Vai para aba de clientes e recarrega
        self.stack.setCurrentIndex(1)
        self.carregar_clientes()

    def filtrar_clientes_por_categoria(self, categoria):
        """
        Filtra os clientes de acordo com a categoria (Estado ou Região),
        respeitando os status selecionados nas checkboxes.
        Se mais de um status estiver marcado, o filtro de status fica vazio.
        """
        # Conta quantos status estão selecionados
        status_selecionados = []
        if self.cb_ativo.isChecked():
            status_selecionados.append("Cliente ativo")
        if self.cb_prospect.isChecked():
            status_selecionados.append("Prospect qualificado")
        if self.cb_lead.isChecked():
            status_selecionados.append("Lead – interessado")

        # Se mais de um status estiver marcado → limpa todos (filtro vazio)
        if len(status_selecionados) > 1:
            self.cb_ativo.setChecked(False)
            self.cb_prospect.setChecked(False)
            self.cb_lead.setChecked(False)
            status_text = ""  # filtro vazio
        # Se apenas um status estiver marcado → garante que só ele fique marcado
        elif len(status_selecionados) == 1:
            status = status_selecionados[0]
            self.cb_ativo.setChecked(status == "Cliente ativo")
            self.cb_prospect.setChecked(status == "Prospect qualificado")
            self.cb_lead.setChecked(status == "Lead – interessado")
            status_text = status
        # Se nenhum estiver marcado → deixa todos desmarcados (sem filtro)
        else:
            self.cb_ativo.setChecked(False)
            self.cb_prospect.setChecked(False)
            self.cb_lead.setChecked(False)
            status_text = ""

        # Aplica categoria no combo certo
        if categoria in [self.combo_estado_filtro.itemText(i) for i in range(self.combo_estado_filtro.count())]:
            self.combo_estado_filtro.setCurrentText(categoria)
            self.combo_status_filtro.setCurrentText(status_text)
        elif categoria in [self.combo_regiao_filtro.itemText(i) for i in range(self.combo_regiao_filtro.count())]:
            self.combo_regiao_filtro.setCurrentText(categoria)
            self.combo_status_filtro.setCurrentText(status_text)

        # Vai para a aba de clientes e recarrega
        self.stack.setCurrentIndex(1)
        self.carregar_clientes()

    def criar_pagina_dashboard(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)

        # ===== Conteúdo interno (scrollável) =====
        conteudo_widget = QWidget()
        conteudo_layout = QVBoxLayout(conteudo_widget)
        conteudo_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Checkboxes de status ===
        linha_filtros = QHBoxLayout()

        self.cb_ativo = QCheckBox("Cliente ativo")
        self.cb_prospect = QCheckBox("Prospect qualificado")
        self.cb_lead = QCheckBox("Lead – interessado")

        # Nenhum marcado por padrão
        self.cb_ativo.setChecked(False)

        # Conectar eventos para atualizar mapa e visibilidade do botão
        for cb in [self.cb_ativo, self.cb_prospect, self.cb_lead]:
            cb.stateChanged.connect(self.atualizar_mapa_dashboard)
            cb.stateChanged.connect(self.on_dashboard_checkbox_changed)
            linha_filtros.addWidget(cb)

        conteudo_layout.addLayout(linha_filtros)

        # === Botão Visualizar Relatório (inicialmente escondido) ===
        self.btn_relatorio = QPushButton("Visualizar Relatório")
        self.btn_relatorio.setVisible(False)
        self.btn_relatorio.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        conteudo_layout.addWidget(self.btn_relatorio)
        self.btn_relatorio.clicked.connect(self.abrir_pagina_relatorio)

        # === WebEngineView para o mapa ===
        self.webview_dashboard = QWebEngineView()
        conteudo_layout.addWidget(self.webview_dashboard)

        # Carregar mapa inicial
        self.atualizar_mapa_dashboard()

        # === Dashboard de cards ===
        self.dashboard_widget = self.criar_dashboard()
        conteudo_layout.addWidget(self.dashboard_widget)
        self.atualizar_dashboard()

        # ===== Scroll Area =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(conteudo_widget)

        layout.addWidget(scroll)

        return pagina
    
    def closeEvent(self, event):
        try:
            if hasattr(self, "webview_dashboard") and self.webview_dashboard:
                self.webview_dashboard.deleteLater()
        except Exception as e:
            print("Erro ao liberar webview:", e)
        super().closeEvent(event)

    def atualizar_mapa_dashboard(self):
        # === Descobrir quais status estão selecionados ===
        status_selecionados = []
        if self.cb_ativo.isChecked():
            status_selecionados.append("Cliente ativo")
        if self.cb_prospect.isChecked():
            status_selecionados.append("Prospect qualificado")
        if self.cb_lead.isChecked():
            status_selecionados.append("Lead – interessado")

        # === Buscar coordenadas de todos os status selecionados ===
        coordenadas = []
        for status in status_selecionados:
            coordenadas.extend(self.obter_coordenadas_por_status(status))

        # === Gerar JS dos marcadores ===
        import json
        marcadores_js = "\n".join([
            f"L.marker([{p['lat']}, {p['lon']}]).addTo(map).bindPopup({json.dumps(p['label'])});"
            for p in coordenadas
        ])

        # === Montar HTML do mapa ===
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8" />
        <title>Dashboard - Mapa de Clientes</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            #map {{ height: 100vh; width: 100vw; margin: 0; padding: 0; }}
            html, body {{ margin: 0; padding: 0; }}
        </style>
        </head>
        <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([0, 0], 2);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
            }}).addTo(map);

            {marcadores_js}
        </script>
        </body>
        </html>
        """

        # Renderiza o mapa no QWebEngineView
        self.webview_dashboard.setHtml(html)

        # === Mostrar ou esconder o botão de relatório ===
        self.btn_relatorio.setVisible(len(coordenadas) > 0)

    def criar_pagina_relatorio(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Título ===
        titulo = QLabel("Relatório de Clientes")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 12px;")
        layout.addWidget(titulo)

        # === Container dinâmico para gráficos ===
        self.layout_relatorio = QVBoxLayout()
        self.layout_relatorio.setSpacing(30)  # espaço entre gráficos
        layout.addLayout(self.layout_relatorio)

        return pagina


    def abrir_pagina_relatorio(self):
        # Cria a página se ainda não existir
        if not hasattr(self, "pagina_relatorio"):
            self.pagina_relatorio = self.criar_pagina_relatorio()
            self.stack.addWidget(self.pagina_relatorio)

        # Atualiza os dados antes de mostrar
        self.atualizar_relatorio()

        # Vai para a página de relatório
        self.stack.setCurrentWidget(self.pagina_relatorio)


    def atualizar_relatorio(self):
        cursor = self.conn.cursor()

        # === Coleta os status selecionados ===
        status_selecionados = []
        if self.cb_ativo.isChecked():
            status_selecionados.append("Cliente ativo")
        if self.cb_prospect.isChecked():
            status_selecionados.append("Prospect qualificado")
        if self.cb_lead.isChecked():
            status_selecionados.append("Lead – interessado")

        # Se nenhum status estiver marcado → limpa e sai
        if not status_selecionados:
            for i in reversed(range(self.layout_relatorio.count())):
                widget = self.layout_relatorio.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            return

        # === Consulta: Clientes por Estado ===
        cursor.execute("""
            SELECT estado, COUNT(*)
            FROM clientes
            WHERE estado IS NOT NULL AND estado <> ''
            AND status = ANY(%s)
            GROUP BY estado
            ORDER BY COUNT(*) DESC
        """, (status_selecionados,))
        dados_estado = cursor.fetchall()

        # === Consulta: Clientes por Região ===
        cursor.execute("""
            SELECT regiao, COUNT(*)
            FROM clientes
            WHERE regiao IS NOT NULL AND regiao <> ''
            AND status = ANY(%s)
            GROUP BY regiao
            ORDER BY COUNT(*) DESC
        """, (status_selecionados,))
        dados_regiao = cursor.fetchall()

        # === Limpa gráficos antigos ===
        for i in reversed(range(self.layout_relatorio.count())):
            widget = self.layout_relatorio.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # === Adiciona gráficos novos ===
        if dados_estado:
            self.layout_relatorio.addWidget(
                self.criar_grafico_vertical("Clientes por Estado", dados_estado)
            )
        if dados_regiao:
            self.layout_relatorio.addWidget(
                self.criar_grafico_vertical("Clientes por Região", dados_regiao)
            )


    def criar_grafico_vertical(self, titulo, dados):
        series = QBarSeries()
        categorias = []
        valores = []

        barset = QBarSet(titulo)
        for categoria, valor in dados:
            categorias.append(categoria)
            valores.append(valor)
            barset << valor

        series.append(barset)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(titulo)
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # Eixo X = categorias
        axisX = QBarCategoryAxis()
        axisX.append(categorias)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        # Eixo Y = valores
        axisY = QValueAxis()
        axisY.setRange(0, max(valores) + 2)
        axisY.setTitleText("Quantidade de Clientes")
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

        chart.setTheme(QChart.ChartThemeDark)
        chart.legend().setVisible(False)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        # === Tooltip ao passar o mouse ===
        def mostrar_tooltip(status, index):
            if status:
                categoria = categorias[index]
                valor = valores[index]
                QToolTip.showText(QCursor.pos(), f"{categoria}: {valor} clientes")

        barset.hovered.connect(mostrar_tooltip)

        # === Menu de contexto ao clicar ===
        def abrir_menu_contexto(index):
            categoria = categorias[index]

            menu = QMenu(chart_view)
            ac_maquinas = QAction(f"Máquinas no {categoria}", chart_view)
            ac_clientes = QAction(f"Clientes no {categoria}", chart_view)

            ac_maquinas.triggered.connect(lambda: self.filtrar_maquinas_por_categoria(categoria))
            ac_clientes.triggered.connect(lambda: self.filtrar_clientes_por_categoria(categoria))

            menu.addAction(ac_maquinas)
            menu.addAction(ac_clientes)

            menu.exec(QCursor.pos())

        barset.clicked.connect(abrir_menu_contexto)

        return chart_view





    def criar_pagina_maquina(self, nome_maquina, cliente_id):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)

        titulo = QLabel(f"{nome_maquina} - Cliente ID: {cliente_id}")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(titulo)

        # 🔍 Campo de pesquisa
        pesquisa_input = QLineEdit()
        pesquisa_input.setPlaceholderText("Pesquisar componente...")
        layout.addWidget(pesquisa_input)

        # 🧾 Tabela de componentes
        tabela = QTableWidget()
        tabela.setColumnCount(2)
        tabela.setHorizontalHeaderLabels(["Peça", "Última Compra"])
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(tabela)

        cursor = self.conn.cursor()

        # Lista completa de componentes
        componentes_originais = COMPONENTES.get(nome_maquina.strip().lower(), [])




        def preencher_tabela():
            tabela.setRowCount(0)
            for item in componentes_originais:
                partes = item.split(";")
                descricao = partes[0] if len(partes) > 0 else ""
                link = partes[1] if len(partes) > 1 else ""
                codigo = partes[2] if len(partes) > 2 else ""

                cursor.execute("""
                    SELECT ultima_compra FROM pecas_clientes
                    WHERE cliente_id = %s AND maquina = %s AND peca = %s
                """, (cliente_id, nome_maquina, descricao))
                row_data = cursor.fetchone()
                ultima_compra = row_data[0] if row_data else ""

                row = tabela.rowCount()
                tabela.insertRow(row)

                # Coluna descrição (com dados extras guardados)
                item_desc = QTableWidgetItem(descricao)
                item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)
                item_desc.setData(Qt.UserRole, {"descricao": descricao, "link": link, "codigo": codigo})
                tabela.setItem(row, 0, item_desc)

                # Coluna data
                data_edit = QLineEdit()
                data_edit.setPlaceholderText("dd/mm/aaaa")
                data_edit.setMaxLength(10)
                if self.grupo == "cliente":
                    data_edit.setReadOnly(True)
                if ultima_compra:
                    qdate = QDate.fromString(ultima_compra, "yyyy-MM-dd")
                    if qdate.isValid():
                        data_edit.setText(qdate.toString("dd/MM/yyyy"))
                    else:
                        data_edit.setText(ultima_compra)
                else:
                    data_edit.clear()
                tabela.setCellWidget(row, 1, data_edit)


        # --- Função para abrir popup ---
        def mostrar_detalhes(item):
            dados = item.data(Qt.UserRole)
            if not dados:
                return

            descricao = dados["descricao"]
            link = dados["link"]
            codigo = dados["codigo"]

            dialog = QDialog()
            dialog.setWindowTitle(descricao)
            layout = QVBoxLayout(dialog)

            lbl_codigo = QLabel(f"Código: {codigo}")
            layout.addWidget(lbl_codigo)

            if link:
                lbl_img = QLabel()
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/124.0.0.0 Safari/537.36"
                    }

                    resp = requests.get(link, headers=headers, timeout=10)
                    resp.raise_for_status()
                    pixmap = QPixmap()
                    if pixmap.loadFromData(resp.content):
                        lbl_img.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
                    else:
                        lbl_img.setText("Formato de imagem não suportado")

                except Exception as e:
                    lbl_img.setText(f"Erro ao carregar imagem: {e}")
                layout.addWidget(lbl_img)

            btn_ok = QPushButton("Fechar")
            btn_ok.clicked.connect(dialog.accept)
            layout.addWidget(btn_ok)

            dialog.exec()


        # --- Conectar clique da tabela ---
        tabela.itemDoubleClicked.connect(mostrar_detalhes)


        # Inicializa a tabela
        preencher_tabela()

        # Conecta pesquisa ao filtro
        pesquisa_input.textChanged.connect(preencher_tabela)

        # --- Função interna para salvar ---
        def salvar_datas():
            for row in range(tabela.rowCount()):
                peca = tabela.item(row, 0).text()
                widget = tabela.cellWidget(row, 1)
                if isinstance(widget, QLineEdit):
                    texto = widget.text().strip()
                    if texto:
                        qdate = QDate.fromString(texto, "dd/MM/yyyy")
                        if not qdate.isValid():
                            QMessageBox.warning(
                                self,
                                "Data inválida",
                                f"A data da peça '{peca}' está inválida. Use o formato dd/mm/aaaa."
                            )
                            return
                        data = qdate.toString("yyyy-MM-dd")
                    else:
                        data = None
                else:
                    data = None

                cursor.execute("""
                    SELECT id FROM pecas_clientes
                    WHERE cliente_id = %s AND maquina = %s AND peca = %s
                """, (cliente_id, nome_maquina, peca))
                existe = cursor.fetchone()

                if existe:
                    cursor.execute("""
                        UPDATE pecas_clientes
                        SET ultima_compra = %s
                        WHERE cliente_id = %s AND maquina = %s AND peca = %s
                    """, (data, cliente_id, nome_maquina, peca))
                else:
                    cursor.execute("""
    INSERT INTO pecas_clientes (cliente_id, maquina, peca, ultima_compra)
    VALUES (%s, %s, %s, %s)
""", (cliente_id, nome_maquina, peca, data))

            self.conn.commit()
            QMessageBox.information(self, "Sucesso", "Datas salvas com sucesso!")
            self.contar_notificacoes()
            self.atualizar_notificacoes()
            self.atualizar_icone_notificacoes()
            self.stack.setCurrentIndex(4)

        # --- Botões de ação ---
        botoes_layout = QHBoxLayout()

        btn_salvar = QPushButton("Salvar Datas")
        btn_salvar.setStyleSheet("""
            QPushButton {
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        btn_salvar.clicked.connect(salvar_datas)
        botoes_layout.addWidget(btn_salvar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                border: 2px solid #a33;
                border-radius: 5px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #a33;
            }
        """)
        btn_cancelar.clicked.connect(lambda: self.editar_cliente(self.id_cliente_atual))
        botoes_layout.addWidget(btn_cancelar)
        if self.grupo == "cliente":
            btn_salvar.setVisible(False)
            btn_cancelar.setVisible(False)

        layout.addLayout(botoes_layout)

        return pagina




    def ordenar_clientes(self, logicalIndex):
        # 0 = checkbox, 1 = Nome, 2 = CNPJ, 3 = Status
        colunas = {1: "nome", 2: "cnpj", 3: "status"}
        if logicalIndex not in colunas:
            return

        coluna = colunas[logicalIndex]
        if self.coluna_ordem == coluna:
            # Alterna entre crescente e decrescente
            self.ordem_crescente = not self.ordem_crescente
        else:
            self.coluna_ordem = coluna
            self.ordem_crescente = True

        self.carregar_clientes()

    def filtrar_clientes_por_status(self, status):
        self.combo_status_filtro.setCurrentText(status)
        self.stack.setCurrentIndex(1)  # Vai para a aba de clientes
        self.carregar_clientes()       # Recarrega a lista com o filtro aplicado

    def criar_dashboard(self):
        dashboard = QWidget()
        layout = QHBoxLayout(dashboard)
        layout.setSpacing(20)

        # ----- Card 1: Total de clientes por status -----
        card_clientes = QGroupBox("Clientes")
        self.layout_clientes_status = QVBoxLayout(card_clientes)

        self.btn_clientes_ativos = QPushButton("Ativos: 0")
        self.btn_clientes_prospect = QPushButton("Prospect: 0")
        self.btn_clientes_lead = QPushButton("Lead: 0")

        status_botoes = [
            (self.btn_clientes_ativos, "Cliente ativo"),
            (self.btn_clientes_prospect, "Prospect qualificado"),
            (self.btn_clientes_lead, "Lead – interessado")
        ]

        for btn, status in status_botoes:
            btn.setStyleSheet("""
                QPushButton {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    color: #63BDFF;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, s=status: self.filtrar_clientes_por_status(s))
            self.layout_clientes_status.addWidget(btn)
            if self.grupo == "cliente":
                card_clientes.setVisible(False)  # Oculta se for cliente

        # ----- Card 2: Máquinas mais vendidas -----
        card_maquina = QGroupBox("Máquinas mais vendidas")
        layout_maquina = QVBoxLayout(card_maquina)

        self.lbl_maquina_mais_vendida = QLabel("Nenhuma")
        self.lbl_maquina_mais_vendida.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout_maquina.addWidget(self.lbl_maquina_mais_vendida)

        self.layout_maquinas_vendidas = QVBoxLayout()
        layout_maquina.addLayout(self.layout_maquinas_vendidas)

        # ----- Card 3: Cliente com mais máquinas -----
        card_cliente_maquinas = QGroupBox("Clientes com mais máquinas")
        self.layout_cliente_mais_maquinas = QVBoxLayout(card_cliente_maquinas)
        if self.grupo == "cliente":
            card_cliente_maquinas.setVisible(False)  # Oculta se for cliente

        # O conteúdo será atualizado dinamicamente no atualizar_dashboard
        self.lbl_cliente_mais_maquinas = QLabel("Nenhum")
        self.lbl_cliente_mais_maquinas.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout_cliente_mais_maquinas.addWidget(self.lbl_cliente_mais_maquinas)

        # ----- Adiciona os cards ao layout horizontal -----
        layout.addWidget(card_clientes)
        layout.addWidget(card_maquina)
        layout.addWidget(card_cliente_maquinas)

        # ----- Estilo para os cards -----
        for card in [card_clientes, card_maquina, card_cliente_maquinas]:
            card.setStyleSheet("""
                QGroupBox {
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    margin-top: 20px;
                    font-size: 16px;
                    padding-top: 20px;
                    background-color: #2c2c2c;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 12px;
                    background-color: transparent;
                    color: white;
                    font-weight: bold;
                }
            """)
            card.setMinimumWidth(200)

        return dashboard

    def atualizar_dashboard(self):
        cursor = self.conn.cursor()

        # ----- Contagem de clientes por status -----
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM clientes
            GROUP BY status
        """)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        self.btn_clientes_ativos.setText(f"Ativos: {status_counts.get('Cliente ativo', 0)}")
        self.btn_clientes_prospect.setText(f"Prospect: {status_counts.get('Prospect qualificado', 0)}")
        self.btn_clientes_lead.setText(f"Lead: {status_counts.get('Lead – interessado', 0)}")

        # ----- Máquinas mais vendidas -----
        cursor.execute("""
            SELECT maquinas 
            FROM clientes
            WHERE maquinas IS NOT NULL AND maquinas != ''
        """)

        maquinas = []
        for row in cursor.fetchall():
            if row[0]:
                maquinas.extend([m.strip() for m in row[0].split(";") if m.strip()])

        if maquinas:
            contagem_maquinas = Counter(maquinas)
            top_maquinas = contagem_maquinas.most_common(5)

            mais_vendida = top_maquinas[0][0]
            self.lbl_maquina_mais_vendida.setText(mais_vendida)

            # Limpa layout anterior
            for i in reversed(range(self.layout_maquinas_vendidas.count())):
                widget = self.layout_maquinas_vendidas.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            max_qtd = top_maquinas[0][1]

            for nome, qtd in top_maquinas:
                linha = QWidget()
                layout_linha = QVBoxLayout(linha)
                layout_linha.setContentsMargins(0, 0, 0, 0)
                layout_linha.setSpacing(4)

                btn_maquina = QPushButton(f"{nome}")
                btn_maquina.setStyleSheet("""
                    QPushButton {
                        background: none;
                        border: none;
                        color: #63BDFF;
                        text-decoration: underline;
                        font-weight: bold;
                        text-align: left;
                    }
                    QPushButton:hover {
                        color: #00aaff;
                    }
                """)
                btn_maquina.setCursor(Qt.PointingHandCursor)
                btn_maquina.clicked.connect(lambda _, m=nome: self.filtrar_clientes_por_maquina(m))
                btn_maquina.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")

                barra = QProgressBar()
                barra.setMaximum(max_qtd)
                barra.setValue(qtd)
                barra.setTextVisible(False)
                barra.setFixedHeight(12)
                barra.setStyleSheet("""
                    QProgressBar {
                        background-color: #1e1e1e;
                        border: 1px solid #555;
                        border-radius: 5px;
                    }
                    QProgressBar::chunk {
                        background-color: #3daee9;
                        border-radius: 5px;
                    }
                """)
                barra.setToolTip(f"{qtd} vendas")
                barra.setTextVisible(False)
                
                layout_linha.addWidget(btn_maquina)
                layout_linha.addWidget(barra)

                self.layout_maquinas_vendidas.addWidget(linha)

        if self.grupo == "cliente":
            btn_maquina.setVisible(False)
            barra.setVisible(False)


        # ----- Cliente com mais máquinas -----
        # ----- Top 5 clientes com mais máquinas -----
        cursor.execute("""
            SELECT id, nome, maquinas 
            FROM clientes
            WHERE maquinas IS NOT NULL AND maquinas != ''
        """)

        clientes_maquinas = []

        for cliente_id, nome, maquinas_str in cursor.fetchall():
            if maquinas_str:
                total_maquinas = len([m for m in maquinas_str.split(";") if m.strip()])
                clientes_maquinas.append((cliente_id, nome, total_maquinas))

        # Ordena e pega os 5 com mais máquinas
        top_clientes = sorted(clientes_maquinas, key=lambda x: x[2], reverse=True)[:5]

        # Limpa layout anterior
        for i in reversed(range(self.layout_cliente_mais_maquinas.count())):
            widget = self.layout_cliente_mais_maquinas.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Adiciona os 5 clientes ao layout
        for cliente_id, nome, qtd in top_clientes:
            btn_cliente = QPushButton(f"{nome}")
            btn_cliente.setStyleSheet("""
                QPushButton {
                    background: none;
                    border: none;
                    color: #63BDFF;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    color: #00aaff;
                }
            """)
            btn_cliente.setCursor(Qt.PointingHandCursor)
            btn_cliente.setToolTip(f"{qtd} máquinas")

            btn_cliente.clicked.connect(lambda _, cid=cliente_id: self.editar_cliente(cid))
            self.layout_cliente_mais_maquinas.addWidget(btn_cliente)


    def log_acao(self, acao, dados):
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {acao} - {dados}\n")


    # Adicione estas linhas ao final do seu método __init__ para inicializar os componentes
    # self.carousel_stack = QStackedWidget()
    # self.legenda_label = QLabel()
    # self.timer_carrossel = QTimer(self)
    # self.imagens = []
    # self.legendas = []

    def criar_carrossel(self):
        """Método que cria o carrossel completo."""
        # Widget container que agrupará todos os elementos do carrossel
        container = QWidget()
        layout_principal = QVBoxLayout(container)

        # --- Definição das imagens e legendas ---
        # É uma boa prática definir isso no __init__ se for constante,
        # mas mantendo aqui para seguir a estrutura original.
        self.imagens = [
            "https://raw.githubusercontent.com/Dvic9/imagens/refs/heads/main/boleadora.png",
            "https://raw.githubusercontent.com/Dvic9/imagens/refs/heads/main/embaladora.png",
            "https://raw.githubusercontent.com/Dvic9/imagens/refs/heads/main/fatiadora.png",
            "https://raw.githubusercontent.com/Dvic9/imagens/refs/heads/main/fitilhador.png",
            "https://raw.githubusercontent.com/Dvic9/imagens/refs/heads/main/pms80.png"
        ]
        self.legendas = [
            "- Capacidade de até 4800 ciclos por hora e 80 ciclos por minuto;\n"
            "- Não necessita de farinhadores;\n"
            "- Equipamento de fabricação nacional;\n"
            "- Baixo custo de manutenção;\n"
            "- Equipamento adequado a norma NR 12;\n"
            "- Estrutura em aço inox AISI 304;",

            "- Capacidade de até 3900 ciclos por hora e 65 ciclos por minuto;\n"
            "- Equipamento de fabricação nacional;\n"
            "- Ajustes operacionais simplificados;\n"
            "- Duplo Magazine com troca automática de embalagem;\n"
            "- Baixo custo de manutenção;\n"
            "- Equipamento adequado a norma NR 12;\n"
            "- Estrutura em aço inox AISI 304;",

            "- Capacidade de até 3900 ciclos por hora e 65 ciclos por minuto;\n"
            "- Pantógrafo com guias de maior durabilidade para serras;\n"
            "- Alimentador sincronizado inteligente para todos os tipos de pães;\n"
            "- Equipamento de fabricação nacional;\n"
            "- Baixo custo de manutenção;\n"
            "- Equipamento adequado a norma NR 12;\n"
            "- Estrutura em aço inox AISI 304;",

            "- Capacidade de até 3900 ciclos por hora e 65 ciclos por minuto;\n"
            "- Equipamento de fabricação nacional;\n"
            "- Estrutura do Fitilhador em alumínio;\n"
            "- Quadro elétrico em aço inox AISI 304;\n"
            "- Aplicação com servo motores, eliminando os motores de escova;\n"
            "- Não possui placas eletrônicas dedicas no painel;\n"
            "- Baixo custo de manutenção;\n"
            "- Equipamento adequado a norma NR 10 e 12;\n",

            "- Capacidade de até 4800 ciclos por hora e 80 ciclos por minuto;\n"
            "- Não necessita de farinhadores;\n"
            "- Equipamento de fabricação nacional;\n"
            "- Baixo custo de manutenção;\n"
            "- Equipamento adequado a norma NR 12;\n"
            "- Estrutura em aço inox AISI 304;"
        ]

        # --- Montagem dos Widgets ---
        # Adiciona as imagens ao QStackedWidget (pilha de widgets)
        # CORREÇÃO: Remove widgets existentes um por um
        while self.carousel_stack.count() > 0:
            widget = self.carousel_stack.widget(0)
            self.carousel_stack.removeWidget(widget)
            widget.deleteLater()

        for img_path in self.imagens:
            label_imagem = QLabel("Carregando imagem...")
            label_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = self.carregar_imagem(img_path)
            if pixmap:
                label_imagem.setPixmap(pixmap.scaled(
                    600, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                label_imagem.setText("Imagem não encontrada")
            
            self.carousel_stack.addWidget(label_imagem)

        # Configura o QLabel para as legendas
        self.legenda_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.legenda_label.setStyleSheet("font-size: 14px; margin-top: 5px;") # Cor herdada do tema
        self.legenda_label.setWordWrap(True)
        self.atualizar_legenda(0)

        # Botões de navegação
        btn_prev = QPushButton("◀")
        btn_next = QPushButton("▶")
        btn_prev.setFixedSize(50, 40)
        btn_next.setFixedSize(50, 40)
        btn_prev.setStyleSheet("font-size: 20px;")
        btn_next.setStyleSheet("font-size: 20px;")
        btn_prev.clicked.connect(self.imagem_anterior)
        btn_next.clicked.connect(self.imagem_proxima)

        # Timer para a troca automática de imagens
        self.timer_carrossel.timeout.connect(self.imagem_proxima)
        self.timer_carrossel.start(5000)  # Intervalo de 5000 ms (5 segundos)

        # --- Organização no Layout ---
        layout_principal.addWidget(self.carousel_stack)
        layout_principal.addWidget(self.legenda_label)

        # Layout para os botões, para que fiquem centralizados
        layout_botoes = QHBoxLayout()
        layout_botoes.addStretch()
        layout_botoes.addWidget(btn_prev)
        layout_botoes.addWidget(btn_next)
        layout_botoes.addStretch()
        layout_principal.addLayout(layout_botoes)

        return container

    def carregar_imagem(self, caminho):
        """Carrega imagem local ou remota com cache."""
        try:
            if caminho.startswith("http://") or caminho.startswith("https://"):
                cache_dir = "cache"
                os.makedirs(cache_dir, exist_ok=True)
                nome_arquivo = hashlib.md5(caminho.encode()).hexdigest() + ".png"
                caminho_cache = os.path.join(cache_dir, nome_arquivo)
                
                if os.path.exists(caminho_cache):
                    return QPixmap(caminho_cache)

                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(caminho, timeout=10, headers=headers)
                
                if resp.status_code == 200:
                    with open(caminho_cache, "wb") as f:
                        f.write(resp.content)
                    return QPixmap(caminho_cache)
                else:
                    print(f"Erro ao baixar {caminho}: {resp.status_code}")
                    return None
            elif os.path.exists(caminho):
                return QPixmap(caminho)
            else:
                print(f"Arquivo não encontrado: {caminho}")
                return None
        except Exception as e:
            print(f"Erro ao carregar {caminho}: {e}")
            return None

    def imagem_proxima(self):
        """Avança para a próxima imagem no carrossel."""
        if self.carousel_stack.count() == 0:
            return
        index = (self.carousel_stack.currentIndex() + 1) % self.carousel_stack.count()
        self.carousel_stack.setCurrentIndex(index)
        self.atualizar_legenda(index)

    def imagem_anterior(self):
        """Retorna para a imagem anterior no carrossel."""
        if self.carousel_stack.count() == 0:
            return
        # A adição de self.carousel_stack.count() evita resultados negativos
        index = (self.carousel_stack.currentIndex() - 1 + self.carousel_stack.count()) % self.carousel_stack.count()
        self.carousel_stack.setCurrentIndex(index)
        self.atualizar_legenda(index)

    def atualizar_legenda(self, index):
        """Atualiza o texto da legenda com base no índice da imagem atual."""
        if 0 <= index < len(self.legendas):
            self.legenda_label.setText(self.legendas[index])
        else:
            self.legenda_label.setText("")

    def criar_pagina_inicio(self):
        """Cria a página inicial da aplicação, incluindo o dashboard e o carrossel."""
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Conteúdo interno (o que será scrollável)
        conteudo_widget = QWidget()
        conteudo_layout = QVBoxLayout(conteudo_widget)
        conteudo_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título
        titulo = QLabel("🚀 Bem-vindo ao Sistema Option")
        titulo.setStyleSheet("font-size: 20px; padding: 8px; font-weight: bold;")
        conteudo_layout.addWidget(titulo)

        # Linha divisória
        conteudo_layout.addWidget(self.criar_linha_divisoria())

        
        # Cria e adiciona o widget do carrossel ao layout
        carrossel_widget = self.criar_carrossel()
        conteudo_layout.addWidget(carrossel_widget)

        # ===== Scroll Area =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(conteudo_widget)

        layout.addWidget(scroll)
        return pagina



    def criar_pagina_clientes(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)

        # ===== Campos de pesquisa principais =====
        self.input_nome_filtro = QLineEdit()
        self.input_nome_filtro.setPlaceholderText("Nome")

        self.input_cnpj_filtro = QLineEdit()
        self.input_cnpj_filtro.setPlaceholderText("CNPJ")

        # ===== Botão filtro avançado =====
        btn_filtro = QPushButton("∇")
        btn_filtro.setFixedWidth(30)
        btn_filtro.setToolTip("Filtros avançados")
        btn_filtro.setStyleSheet("""
            QPushButton {
                border: 1px solid #888;
                border-radius: 4px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)

        # ===== Layout da primeira linha =====
        form_layout = QHBoxLayout()
        form_layout.addWidget(self.input_nome_filtro)
        form_layout.addWidget(self.input_cnpj_filtro)
        form_layout.addWidget(btn_filtro)

        # ===== Área de filtros avançados =====
        self.filtros_avancados = QWidget()
        filtros_layout = QGridLayout(self.filtros_avancados)
        filtros_layout.setContentsMargins(0, 0, 0, 0)
        filtros_layout.setSpacing(8)

        def configurar_combo(combo):
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return combo

        # ===== Combos de filtros =====
        self.combo_pais_filtro = configurar_combo(QComboBox())
        self.combo_pais_filtro.currentIndexChanged.connect(self.carregar_estados_filtro)

        self.combo_estado_filtro = configurar_combo(QComboBox())
        self.combo_estado_filtro.currentIndexChanged.connect(self.carregar_cidades_filtro)

        self.combo_municipio_filtro = configurar_combo(QComboBox())
        self.combo_municipio_filtro.currentIndexChanged.connect(self.carregar_bairros_filtro)

        self.input_bairro_filtro = configurar_combo(QComboBox())
        self.input_bairro_filtro.currentIndexChanged.connect(self.carregar_ruas_filtro)

        self.input_rua_filtro = configurar_combo(QComboBox())

        self.combo_status_filtro = configurar_combo(QComboBox())
        self.combo_status_filtro.addItem("")
        self.combo_status_filtro.addItems([
            "Cliente ativo",
            "Prospect qualificado",
            "Lead – interessado"
        ])

        # ===== Combo de máquinas com autocomplete =====
        self.combo_maquina_filtro = configurar_combo(QComboBox())
        self.combo_maquina_filtro.setEditable(True)  # necessário para autocomplete
        self.combo_maquina_filtro.addItem("")
        self.combo_maquina_filtro.addItems(MAQUINAS)

        # Criar QCompleter
        completer = QCompleter(MAQUINAS)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.combo_maquina_filtro.setCompleter(completer)

        # ===== FILTRO DE REGIÃO =====
        self.combo_regiao_filtro = configurar_combo(QComboBox())
        self.carregar_regioes_filtro()  # Popula o combo de regiões

        # ===== Layout dos filtros avançados =====
        filtros_layout.addWidget(QLabel("País:"), 0, 0)
        filtros_layout.addWidget(self.combo_pais_filtro, 0, 1)
        filtros_layout.addWidget(QLabel("Estado:"), 0, 2)
        filtros_layout.addWidget(self.combo_estado_filtro, 0, 3)
        filtros_layout.addWidget(QLabel("Cidade:"), 0, 4)
        filtros_layout.addWidget(self.combo_municipio_filtro, 0, 5)

        filtros_layout.addWidget(QLabel("Bairro:"), 1, 0)
        filtros_layout.addWidget(self.input_bairro_filtro, 1, 1)
        filtros_layout.addWidget(QLabel("Rua:"), 1, 2)
        filtros_layout.addWidget(self.input_rua_filtro, 1, 3)
        filtros_layout.addWidget(QLabel("Status:"), 1, 4)
        filtros_layout.addWidget(self.combo_status_filtro, 1, 5)

        filtros_layout.addWidget(QLabel("Máquina:"), 2, 0)
        filtros_layout.addWidget(self.combo_maquina_filtro, 2, 1)
        filtros_layout.addWidget(QLabel("Região:"), 2, 2)
        filtros_layout.addWidget(self.combo_regiao_filtro, 2, 3)

        for col in range(6):
            filtros_layout.setColumnStretch(col, 1)

        self.filtros_avancados.setVisible(False)
        btn_filtro.clicked.connect(
            lambda: self.filtros_avancados.setVisible(not self.filtros_avancados.isVisible())
        )

        # ===== Botões de ação =====
        btn_cadastrar = QPushButton("Cadastrar Cliente")
        btn_cadastrar.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        btn_cadastrar.clicked.connect(lambda: self.stack.setCurrentIndex(4))

        btn_excluir = QPushButton("Excluir Cliente")
        btn_excluir.setStyleSheet("""
            QPushButton {
                border: 2px solid #a33;
                border-radius: 15px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #a33;
            }
        """)
        btn_excluir.clicked.connect(self.excluir_cliente)

        botoes_layout = QHBoxLayout()
        botoes_layout.addWidget(btn_cadastrar)
        botoes_layout.addWidget(btn_excluir)

        if self.grupo == "cliente":
            btn_cadastrar.setVisible(False)
            btn_excluir.setVisible(False)

        # ===== Botões de pesquisa e limpar =====
        btn_pesquisar = QPushButton("Pesquisar")
        btn_pesquisar.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        btn_pesquisar.clicked.connect(self.carregar_clientes)
        self.input_nome_filtro.returnPressed.connect(self.carregar_clientes)
        self.input_cnpj_filtro.returnPressed.connect(self.carregar_clientes)

        btn_limpar = QPushButton("Limpar filtros")
        btn_limpar.setStyleSheet("""
            QPushButton {
                border: 2px solid #888;
                border-radius: 12px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        btn_limpar.clicked.connect(self.limpar_filtros)

        botoes_layout.addWidget(btn_pesquisar)
        botoes_layout.addWidget(btn_limpar)

        # ===== Tabela =====
        self.tabela_clientes = QTableWidget()
        self.tabela_clientes.setColumnCount(3)
        self.tabela_clientes.setHorizontalHeaderLabels(["", "Nome", "CNPJ"])
        self.tabela_clientes.horizontalHeader().setStretchLastSection(True)
        self.tabela_clientes.cellDoubleClicked.connect(self.editar_cliente)
        self.tabela_clientes.horizontalHeader().sectionClicked.connect(self.ordenar_clientes)
        self.coluna_ordem = None
        self.ordem_crescente = True

        # ===== Montagem final =====
        layout.addLayout(form_layout)
        layout.addWidget(self.filtros_avancados)
        layout.addLayout(botoes_layout)

        # ===== Label de quantidade de resultados =====
        self.label_resultados = QLabel("Resultado: 0")
        self.label_resultados.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(self.label_resultados)

        layout.addWidget(self.tabela_clientes)

        # Carregar filtros iniciais
        self.carregar_paises_filtro()
        self.carregar_clientes()

        return pagina



    def limpar_filtros(self):
        self.input_nome_filtro.clear()
        self.input_cnpj_filtro.clear()
        self.combo_pais_filtro.setCurrentIndex(0)
        self.combo_estado_filtro.setCurrentIndex(0)
        self.combo_municipio_filtro.setCurrentIndex(0)
        self.input_bairro_filtro.setCurrentIndex(0)
        self.input_rua_filtro.setCurrentIndex(0)
        self.combo_status_filtro.setCurrentIndex(0)
        self.combo_maquina_filtro.setCurrentIndex(0)
        self.combo_regiao_filtro.setCurrentIndex(0)
        self.carregar_clientes()  # recarrega todos os clientes



    def editar_cliente_por_cnpj(self, cnpj):
        try:
            cnpj_formatado = formatar_cnpj(cnpj)

            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM clientes WHERE cnpj = %s;", (cnpj_formatado,))
            resultado = cursor.fetchone()
            cursor.close()

            if resultado:
                id_cliente = resultado[0]
                self.editar_cliente(id_cliente)
            else:
                QMessageBox.warning(self, "Erro", "Cliente com esse CNPJ não encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar cliente: {e}")
    






    def criar_pagina_boleadora(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)

        titulo = QLabel("Boleadora - RB80")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(titulo)

        # Exemplo de conteúdo
        descricao = QLabel("Informações e configurações específicas da Boleadora RB80.")
        layout.addWidget(descricao)

        # Aqui você pode colocar tabelas, relatórios ou controles específicos dessa máquina
        layout.addStretch()

        return pagina


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Procura o botão focado
            widget_focado = self.focusWidget()
            if isinstance(widget_focado, QPushButton):
                widget_focado.click()
        else:
            super().keyPressEvent(event)
            
    def ir_para_maquina(self, nome_maquina):
        # Pega o ID do cliente atualmente selecionado
        cliente_id = self.id_cliente_atual

        # Cria a página da máquina com as datas específicas desse cliente
        pagina = self.criar_pagina_maquina(nome_maquina, cliente_id)

        # Adiciona a página no stack e muda para ela
        self.stack.addWidget(pagina)
        self.stack.setCurrentWidget(pagina)


    def criar_tabela_clientes(self):
        cursor = self.conn.cursor()

        cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    pais TEXT,
    estado TEXT,
    municipio TEXT,
    bairro TEXT,
    rua TEXT,
    numero TEXT,
    cnpj TEXT,
    contato TEXT,
    email TEXT,
    maquinas TEXT,
    producao TEXT,
    quantidade INTEGER,
    status TEXT,              -- <=== CAMPO NOVO
    ultima_compra DATE,
    lembrete_dias INTEGER
)
""")


        self.conn.commit()
    # === Métodos de carregamento de localização ===




    def carregar_municipios(self):
        pais = self.combo_pais.currentText()
        if pais == "Brasil":
            self.carregar_municipios_brasil()
        elif pais == "Argentina":
            self.carregar_municipios_argentina()


    def criar_linha_divisoria(self):
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setFrameShadow(QFrame.Sunken)
        linha.setStyleSheet("""
            color: #888;
            border: 1px solid #555;
        """)
        return linha
    
    def carregar_por_cnpj(self):
        cnpj_formatado = self.input_cnpj.text().strip()
        if not cnpj_formatado:
            QMessageBox.warning(self, "Aviso", "Digite um CNPJ válido antes de carregar.")
            return

        # Remove máscara para usar apenas números
        cnpj = ''.join(filter(str.isdigit, cnpj_formatado))

        try:
            url = f"https://publica.cnpj.ws/cnpj/{cnpj}"
            resp = requests.get(url, headers={"Accept": "*/*"}, timeout=10)
            if resp.status_code != 200:
                QMessageBox.warning(self, "Erro", "Não foi possível consultar o CNPJ.")
                return

            dados = resp.json()
            est = dados.get("estabelecimento", {})

            # Dados principais
            self.input_nome.setText(dados.get("razao_social", ""))
            telefone = est.get("telefone1") or est.get("telefone2") or ""
            # self.input_contato.setText(telefone)
            # self.input_email.setText(est.get("email", ""))

            # Endereço
            logradouro = est.get("tipo_logradouro", "") + " " + (est.get("logradouro") or "")
            self.input_rua.setText(logradouro.strip())
            self.input_numero.setText(est.get("numero", ""))
            self.input_bairro.setText(est.get("bairro", ""))

            # Estado e Município
            estado_sigla = est.get("estado", {}).get("sigla", "")
            municipio = est.get("cidade", {}).get("nome", "")

            # 1) Seleciona País
            self.combo_pais.setCurrentText("Brasil")




            self.input_estado.setText(estado_sigla)

            self.input_municipio.setText(municipio)
            # Monta endereço para geolocalização
            endereco_completo = f"{self.input_municipio.text()}, {self.input_estado.text()}, Brasil"

            # Consulta latitude e longitude
            lat, lon = self.obter_lat_lon(endereco_completo)

            # Se quiser exibir ou armazenar
            if lat and lon:
                # Se tiver campos na interface:
                self.input_lat.setText(str(lat))
                self.input_lon.setText(str(lon))
            else:
                QMessageBox.warning(self, "Aviso", "Não foi possível obter a localização geográfica.")
                
            QMessageBox.information(self, "Sucesso", "Dados carregados com sucesso!")
            

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar CNPJ: {e}")

    # Função para criar login
    def criar_login(self):
        nome = self.input_nome.text().strip()
        documento = self.input_cnpj.text().strip()
        email = self.input_email.text().strip()

        if not nome or not documento or not email:
            QMessageBox.warning(self, "Erro", "Preencha Nome, CNPJ e E-mail antes de criar o login.")
            return

        # 🔥 Mantém só os números no documento
        documento_numeros = re.sub(r'\D', '', documento)

        try:
            resp = requests.post(
                f"{API_URL}/usuarios/convite",
                json={"nome": nome, "documento": documento_numeros, "email": email},
                timeout=50
            )

            if resp.status_code == 200:
                data = resp.json()
                QMessageBox.information(
                    self,
                    "Convite enviado",
                    f"Convite enviado com sucesso!\n\nLink: {data.get('link')}"
                )
                # opcional: esconder o botão depois de criar
                self.btn_criar_login.setVisible(False)

            else:
                erro = resp.json().get("detail", "Erro desconhecido")
                QMessageBox.critical(self, "Erro", f"Falha ao criar login: {erro}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro de conexão: {e}")



    def atualizar_mascara_cpf_cnpj(self, text):
        numeros = ''.join(filter(str.isdigit, text))

        if len(numeros) <= 11:  # CPF
            mascara = '000.000.000-00'
            tamanho_max = 11
        else:  # CNPJ
            mascara = '00.000.000/0000-00'
            tamanho_max = 14

        numeros = numeros[:tamanho_max]

        # Posição do cursor original
        cursor_pos = self.input_cnpj.cursorPosition()

        # Conta quantos números existiam antes do cursor original
        numeros_antes_cursor = len([c for c in text[:cursor_pos] if c.isdigit()])

        # Reconstrói o texto com máscara
        resultado = ''
        j = 0
        for m in mascara:
            if m == '0':
                if j < len(numeros):
                    resultado += numeros[j]
                    j += 1
                else:
                    break
            else:
                if j < len(numeros):
                    resultado += m

        # Nova posição do cursor: imediatamente após o último número antes do cursor
        pos = 0
        numeros_contados = 0
        while numeros_contados < numeros_antes_cursor and pos < len(resultado):
            if resultado[pos].isdigit():
                numeros_contados += 1
            pos += 1

        self.input_cnpj.blockSignals(True)
        self.input_cnpj.setText(resultado)
        self.input_cnpj.setCursorPosition(pos)
        self.input_cnpj.blockSignals(False)


    def alterar_status_usuario(self):
        import re, requests
        from PySide6.QtWidgets import QMessageBox

        documento = re.sub(r'\D', '', self.input_cnpj.text().strip())
        novo_status = self.combo_status_usuario.currentText()

        if not documento:
            QMessageBox.warning(self, "Erro", "Informe o CNPJ antes de alterar o status.")
            return

        API_KEY = "7X9L2Q0M8R5Z1Y4H6C3D8N0K5W2T9V1"  

        try:
            resp = requests.put(
                f"{API_URL}/usuarios/{documento}/status?key={API_KEY}",
                json={"novo_status": novo_status},
                timeout=10
            )
            if resp.status_code == 200:
                QMessageBox.information(None, "Sucesso", f"Status alterado para {novo_status}")
            else:
                erro = resp.json().get("detail", "Erro desconhecido")
                QMessageBox.critical(None, "Erro", f"Falha ao alterar status: {erro}")
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro de conexão: {e}")

    def verificar_usuario_existente(self, documento):
        import re, requests

        documento_numeros = re.sub(r'\D', '', documento)
        API_KEY = "7X9L2Q0M8R5Z1Y4H6C3D8N0K5W2T9V1"  

        try:
            resp = requests.get(f"{API_URL}/usuarios/{documento_numeros}?key={API_KEY}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("existe"):
                    status = data.get("status")

                    if status in ["ativo", "inativo"]:
                        self.btn_criar_login.setVisible(False)
                        self.combo_status_usuario.setCurrentText(status)
                        self.combo_status_usuario.setEnabled(True)
                        self.btn_alterar_status.setEnabled(True)
                    elif status == "pendente":
                        self.btn_criar_login.setVisible(False)
                        self.combo_status_usuario.setCurrentText("pendente")
                        self.combo_status_usuario.setEnabled(False)
                        self.btn_alterar_status.setEnabled(False)
                else:
                    self.btn_criar_login.setVisible(True)
                    self.combo_status_usuario.setEnabled(False)
                    self.btn_alterar_status.setEnabled(False)
            else:
                self.btn_criar_login.setVisible(True)
                self.combo_status_usuario.setEnabled(False)
                self.btn_alterar_status.setEnabled(False)

        except Exception as e:
            print("Erro ao verificar usuário:", e)
            self.btn_criar_login.setVisible(True)
            self.combo_status_usuario.setEnabled(False)
            self.btn_alterar_status.setEnabled(False)




    def criar_pagina_cadastro_cliente(self):
        pagina_scroll = QScrollArea()
        pagina_scroll.setWidgetResizable(True)
        pagina_scroll.setStyleSheet("border: none;")  

        conteudo = QWidget()
        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(8)

        titulo = QLabel("Cadastro de Cliente")
        layout.addWidget(titulo)

        # ------------------- Endereço -------------------
        group_endereco = QGroupBox("")
        layout_endereco = QGridLayout(group_endereco)

        # Combo País
        self.combo_pais = QComboBox()
        self.combo_pais.addItem("")  # item vazio
        self.combo_pais.addItems(["Brasil", "Argentina"])
        self.combo_pais.setCurrentIndex(0)

        # Estado e Região
        self.input_estado = QLineEdit()
        self.input_regiao = QLineEdit()
        self.input_regiao.setReadOnly(True)
        self.input_regiao.setPlaceholderText("Região")
        
        def atualizar_regiao(texto_estado):
            estado = texto_estado.strip().upper()
            regioes = {
                "Norte": ['AC','AP','AM','PA','RO','RR','TO'],
                "Nordeste": ['AL','BA','CE','MA','PB','PE','PI','RN','SE'],
                "Centro-Oeste": ['DF','GO','MT','MS'],
                "Sudeste": ['ES','MG','RJ','SP'],
                "Sul": ['PR','RS','SC']
            }
            for regiao, estados in regioes.items():
                if estado in estados:
                    self.input_regiao.setText(regiao)
                    return
            self.input_regiao.clear()


            

        self.input_estado.textChanged.connect(atualizar_regiao)
        self.input_municipio = QLineEdit()

        # Campos extras
        self.input_bairro = QLineEdit()
        self.input_rua = QLineEdit()
        self.input_numero = QLineEdit()

        self.input_lat = QLineEdit()
        self.input_lon = QLineEdit()

        self.input_lat.setPlaceholderText("Latitude")
        self.input_lon.setPlaceholderText("Longitude")

        layout_endereco.addWidget(QLabel("País:"), 0, 0)
        layout_endereco.addWidget(self.combo_pais, 0, 1)
        layout_endereco.addWidget(QLabel("Estado/Província:"), 0, 2)
        layout_endereco.addWidget(self.input_estado, 0, 3)
        layout_endereco.addWidget(QLabel("Município:"), 1, 0)
        layout_endereco.addWidget(self.input_municipio, 1, 1)
        layout_endereco.addWidget(QLabel("Bairro:"), 1, 2)
        layout_endereco.addWidget(self.input_bairro, 1, 3)
        layout_endereco.addWidget(QLabel("Rua:"), 2, 0)
        layout_endereco.addWidget(self.input_rua, 2, 1)
        layout_endereco.addWidget(QLabel("Número:"), 2, 2)
        layout_endereco.addWidget(self.input_numero, 2, 3)
        layout_endereco.addWidget(QLabel("Latitude:"), 3, 0)
        layout_endereco.addWidget(self.input_lat, 3, 1)
        layout_endereco.addWidget(QLabel("Longitude:"), 3, 2)
        layout_endereco.addWidget(self.input_lon, 3, 3)
        layout_endereco.addWidget(QLabel("Região:"), 4, 0)
        layout_endereco.addWidget(self.input_regiao, 4, 1, 1, 3)


        self.input_lat.setReadOnly(True)
        self.input_lon.setReadOnly(True)
        self.input_regiao.setReadOnly(True)
        
        if self.grupo == "admin":
            self.input_lat.setVisible(True)
            self.input_lon.setVisible(True)
            self.input_regiao.setVisible(True)
        else:
            self.input_lat.setVisible(False)
            self.input_lon.setVisible(False)
            self.input_regiao.setVisible(False)

        # ------------------- Dados da Empresa -------------------
        group_empresa = QGroupBox("")
        layout_empresa = QGridLayout(group_empresa)

        self.input_nome = QLineEdit()
        self.input_cnpj = QLineEdit()
        self.input_contato = QLineEdit()
        self.input_email = QLineEdit()
        regex_email = QRegularExpression(r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$")
        self.input_email.setValidator(QRegularExpressionValidator(regex_email))
        # Campo para e-mails adicionais
        self.input_emails_adicionais = QLineEdit()
        self.input_emails_adicionais.setPlaceholderText("Digite outros e-mails, um por linha")
        self.input_emails_adicionais.setFixedHeight(60)


        layout_empresa.addWidget(QLabel("Nome:"), 0, 0)
        layout_empresa.addWidget(self.input_nome, 0, 1)
        layout_empresa.addWidget(QLabel("CNPJ:"), 0, 2)
        layout_empresa.addWidget(self.input_cnpj, 0, 3)
        self.input_cnpj.textChanged.connect(self.atualizar_mascara_cpf_cnpj)
        self.input_cnpj.textChanged.connect(
    lambda: self.verificar_usuario_existente(self.input_cnpj.text())
)
        




        btn_carregar_cnpj = QPushButton("Carregar")
        btn_carregar_cnpj.setStyleSheet("""
            QPushButton {
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        btn_carregar_cnpj.clicked.connect(self.carregar_por_cnpj)
        if self.grupo == "cliente":
            btn_carregar_cnpj.setVisible(False)
        
        layout_empresa.addWidget(btn_carregar_cnpj, 0, 4)  # fica ao lado do campo de CNPJ




        layout_empresa.addWidget(QLabel("Contato:"), 1, 0)
        layout_empresa.addWidget(self.input_contato, 1, 1)
        layout_empresa.addWidget(QLabel("E-mail:"), 1, 2)
        layout_empresa.addWidget(self.input_email, 1, 3)
        # Nova linha para e-mails adicionais
        layout_empresa.addWidget(QLabel("E-mails adicionais:"), 2, 0)
        layout_empresa.addWidget(self.input_emails_adicionais, 2, 1, 1, 3)







        # Botão criar login (apenas se status for Cliente ativo)
        self.btn_criar_login = QPushButton("Criar login")
        self.btn_criar_login.setStyleSheet("""
            QPushButton {
                border: 1px solid #28a745;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
                background-color: #28a745;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)

        self.btn_criar_login.setVisible(True)  
        # Conecta ao botão
        self.btn_criar_login.clicked.connect(self.criar_login)
        layout_empresa.addWidget(self.btn_criar_login, 1, 4)  # abaixo do botão Carregar
        # 🔥 Novo bloco: alterar status
        self.combo_status_usuario = QComboBox()
        self.combo_status_usuario.addItems(["ativo", "inativo"])
        layout_empresa.addWidget(QLabel("Status do usuário:"), 3, 0)
        layout_empresa.addWidget(self.combo_status_usuario, 3, 1)

        self.btn_alterar_status = QPushButton("Alterar Status")
        self.btn_alterar_status.setStyleSheet("""
            QPushButton {
                border: 1px solid #ffc107;
                border-radius: 4px;
                padding: 4px 8px;
                color: black;
                background-color: #ffc107;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.btn_alterar_status.clicked.connect(self.alterar_status_usuario)
        layout_empresa.addWidget(self.btn_alterar_status, 3, 2)





        # ------------------- Produção -------------------
        group_producao = QGroupBox("")
        layout_producao = QGridLayout(group_producao)

        # Combo de máquinas
        self.input_maquinas = QComboBox()
        self.input_maquinas.addItems(MAQUINAS)
        self.input_maquinas.setEditable(True)



        # Criar QCompleter para autocomplete
        completer = QCompleter(MAQUINAS)
        completer.setCaseSensitivity(Qt.CaseInsensitive)   # ignora maiúsculas/minúsculas
        completer.setFilterMode(Qt.MatchContains)          # sugere mesmo se o texto estiver no meio
        self.input_maquinas.setCompleter(completer)

        # Botão para adicionar máquina
        btn_add_maquina = QPushButton("Adicionar máquina")
        btn_add_maquina.setStyleSheet("""
            QPushButton {
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        btn_add_maquina.clicked.connect(self.adicionar_maquina)


        # Layout horizontal para combo + botão
        linha_maquinas = QHBoxLayout()
        linha_maquinas.addWidget(self.input_maquinas)
        linha_maquinas.addWidget(btn_add_maquina)

        # Lista de máquinas adicionadas (altura fixa + rolagem + seleção simples)
        self.lista_maquinas = QListWidget()

        self.lista_maquinas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista_maquinas.customContextMenuRequested.connect(self._maquina_context_menu)

        # deixa a lista crescer naturalmente e rolar
        self.lista_maquinas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lista_maquinas.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.lista_maquinas.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lista_maquinas.setSelectionMode(QAbstractItemView.SingleSelection)
        # Montagem na grid
        layout_producao.addWidget(QLabel("Máquinas:"), 0, 0)
        layout_producao.addLayout(linha_maquinas, 0, 1, 1, 2)
        layout_producao.addWidget(self.lista_maquinas, 1, 0, 1, 3)

        # Garante que as linhas da grade não sejam esticadas indevidamente
        layout_producao.setRowStretch(0, 0)
        layout_producao.setRowStretch(1, 0)
        layout_producao.setRowStretch(2, 0)
        layout_producao.setRowStretch(3, 0)

        # Campos restantes
        self.input_producao = QLineEdit()
        self.input_quantidade = QSpinBox()
        self.input_quantidade.setMaximum(999999)

        layout_producao.addWidget(QLabel("O que produz:"), 2, 0)
        layout_producao.addWidget(self.input_producao, 2, 1, 1, 2)
        layout_producao.addWidget(QLabel("Quantidade produzida:"), 3, 0)
        layout_producao.addWidget(self.input_quantidade, 3, 1)

        # ------------------- Histórico -------------------
        group_historico = QGroupBox("")
        layout_historico = QGridLayout(group_historico)

        # Substituindo o QDateEdit por um QComboBox de status
        self.input_status_cliente = QComboBox()
        self.input_status_cliente.addItems([
            "Cliente ativo",
            "Prospect qualificado",
            "Lead – interessado"
        ])

        self.input_lembrete = QSpinBox()
        self.input_lembrete.setMaximum(365)

        layout_historico.addWidget(QLabel("Status do cliente:"), 0, 0)
        layout_historico.addWidget(self.input_status_cliente, 0, 1)
        layout_historico.addWidget(QLabel("Lembrete em (dias):"), 0, 2)
        layout_historico.addWidget(self.input_lembrete, 0, 3)

        # Depois, você pode mostrar o botão dependendo do status do cliente ao editar
        def atualizar_botao_login():
            if self.input_status_cliente.currentText() == "Cliente ativo":
                self.btn_criar_login.setVisible(True)
            else:
                self.btn_criar_login.setVisible(False)

        self.input_status_cliente.currentIndexChanged.connect(atualizar_botao_login)

        # ------------------- Botão Salvar -------------------
        btn_salvar = QPushButton("Salvar Cliente")
        btn_salvar.setStyleSheet("""
    QPushButton {
        border: 2px solid #3498db;
        border-radius: 5px;
        padding: 5px 10px;
        color: white;
    }
    QPushButton:hover {
        background-color: #3498db;
    }
    """)
        btn_salvar.clicked.connect(self.salvar_cliente)
        if self.grupo == "cliente":
            btn_salvar.setVisible(False)

        # Adiciona tudo no layout principal
        layout.addWidget(self.criar_linha_divisoria())
        layout.addWidget(group_empresa)

        layout.addWidget(self.criar_linha_divisoria())
        layout.addWidget(group_endereco)

        layout.addWidget(self.criar_linha_divisoria())
        layout.addWidget(group_producao)

        layout.addWidget(self.criar_linha_divisoria())
        layout.addWidget(group_historico)

        layout.addWidget(btn_salvar, alignment=Qt.AlignRight)

        conteudo.setStyleSheet("""
        QLineEdit, QComboBox, QSpinBox, QDateEdit, QListWidget {
            border: 1px solid #888;
            border-radius: 4px;
            padding: 4px;
            background-color: #222;
            color: white;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QListWidget:focus {
            border: 1px solid #00aaff;
            background-color: #333;
        }
        QComboBox::drop-down {
            border-left: 1px solid #888;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: #333;
        }
        """)

        # ------------------- Botão Cancelar -------------------
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
        QPushButton {
            border: 2px solid #a33;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
        }
        QPushButton:hover {
            background-color: #a33;
        }
        """)
        btn_cancelar.clicked.connect(self.cancelar_edicao)
        if self.grupo == "cliente":
            btn_cancelar.setVisible(False)

        # Layout para alinhar salvar e cancelar lado a lado
        botoes_layout = QHBoxLayout()
        botoes_layout.addWidget(btn_salvar)
        botoes_layout.addWidget(btn_cancelar)
        layout.addLayout(botoes_layout)

        pagina_scroll.setWidget(conteudo)
        pagina_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        return pagina_scroll



    def cancelar_edicao(self):
        # Limpa campos de texto
        self.input_nome.clear()
        self.combo_pais.setCurrentIndex(0)     # volta para o primeiro item
        self.input_estado.clear()              # limpa estados
        self.input_regiao.clear()        # Limpa região
        self.input_municipio.clear()           # limpa municípios
        self.input_bairro.clear()
        self.input_rua.clear()
        self.input_numero.clear()
        self.input_cnpj.clear()
        self.input_contato.clear()
        self.input_email.clear()
        self.input_lat.clear()
        self.input_lon.clear()
        self.lista_maquinas.clear()
        self.input_producao.clear()
        self.input_quantidade.setValue(0)
        self.input_lembrete.setValue(0)
        
        # Sai do modo edição
        self.cliente_em_edicao = None
        self.stack.setCurrentIndex(1)  # volta para a tela de listagem

        
        # Volta para a aba de clientes
        self.stack.setCurrentIndex(1)


    def salvar_cliente(self):
        nome = self.input_nome.text()
        pais = self.combo_pais.currentText()
        estado = self.input_estado.text()
        regiao = self.input_regiao.text()  # inclui região
        municipio = self.input_municipio.text()
        bairro = self.input_bairro.text()
        rua = self.input_rua.text()
        numero = self.input_numero.text()
        cnpj = self.input_cnpj.text()
        contato = self.input_contato.text()
        email = self.input_email.text()
        lat = self.input_lat.text()
        lon = self.input_lon.text()
        maquinas = []
        for i in range(self.lista_maquinas.count()):
            widget = self.lista_maquinas.itemWidget(self.lista_maquinas.item(i))
            if isinstance(widget, QPushButton):
                maquinas.append(widget.text())
            else:
                maquinas.append(self.lista_maquinas.item(i).text())
        maquinas = ";".join(maquinas)

        producao = self.input_producao.text()
        quantidade = self.input_quantidade.value()
        status = self.input_status_cliente.currentText()
        lembrete_dias = self.input_lembrete.value()

        if not nome or not cnpj:
            QMessageBox.warning(self, "Aviso", "Preencha pelo menos Nome e CNPJ!")
            return

        try:
            cursor = self.conn.cursor()
            if self.cliente_em_edicao:
                cursor.execute("""
                    UPDATE clientes
                    SET nome=%s, pais=%s, estado=%s, regiao=%s, municipio=%s, bairro=%s, rua=%s, numero=%s, cnpj=%s, contato=%s, email=%s,
                        maquinas=%s, producao=%s, quantidade=%s, status=%s, ultima_compra=%s, lembrete_dias=%s, lat=%s, lon=%s, nome_fantasia=%s
                    WHERE id=%s
                """, (
                    nome, pais, estado, regiao, municipio, bairro, rua, numero, cnpj, contato, email,
                    maquinas, producao, quantidade, status, None, lembrete_dias, lat, lon, None, self.cliente_em_edicao
                ))
            else:
                cursor.execute("""
                    INSERT INTO clientes 
                    (nome, pais, estado, regiao, municipio, bairro, rua, numero, cnpj, contato, email, maquinas, producao, quantidade, status, ultima_compra, lembrete_dias, lat, lon, nome_fantasia)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    nome, pais, estado, regiao, municipio, bairro, rua, numero, cnpj, contato, email,
                    maquinas, producao, quantidade, status, None, lembrete_dias, lat, lon, None
                ))

            self.conn.commit()
    
            QMessageBox.information(self, "Sucesso", "Cliente salvo com sucesso!")

            # Limpa campos
            self.input_nome.clear()
            self.combo_pais.setCurrentIndex(0)
            self.input_estado.clear()
            self.input_municipio.clear()
            self.input_bairro.clear()
            self.input_rua.clear()
            self.input_numero.clear()
            self.input_cnpj.clear()
            self.input_contato.clear()
            self.input_email.clear()
            self.input_lat.clear()
            self.input_lon.clear()
            self.lista_maquinas.clear()
            self.input_producao.clear()
            self.input_quantidade.setValue(0)
            self.input_lembrete.setValue(0)
            
            self.cliente_em_edicao = None
            


            self.stack.setCurrentIndex(1)
            # Atualiza tabela de clientes
            self.carregar_clientes()

            # Atualiza combos de filtro de forma incremental
            p = pais.strip()
            if p and self.combo_pais_filtro.findText(p) == -1:
                self.combo_pais_filtro.addItem(p)

            e = estado.strip()
            if e and self.combo_estado_filtro.findText(e) == -1:
                self.combo_estado_filtro.addItem(e)

            m = municipio.strip()
            if m and self.combo_municipio_filtro.findText(m) == -1:
                self.combo_municipio_filtro.addItem(m)

            s = status.strip()
            if s and self.combo_status_filtro.findText(s) == -1:
                self.combo_status_filtro.addItem(s)

            self.stack.setCurrentIndex(1)
            self.atualizar_dashboard()


        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar cliente: {e}")


    def editar_cliente(self, row, column=None):
        # --- Caso 1: veio de uma notificação ---
        if column is None:
            id_cliente = row  # aqui "row" é o próprio id_cliente

        # --- Caso 2: veio de um clique na tabela ---
        else:
            cb_widget = self.tabela_clientes.cellWidget(row, 0)
            if not cb_widget:
                return
            cb = cb_widget.findChild(QCheckBox)
            if not cb:
                return
            id_cliente = cb.property('id_cliente')
            if not id_cliente:
                return

        # Armazena cliente atual para edição
        self.id_cliente_atual = id_cliente
        self.cliente_em_edicao = id_cliente

        # Busca no banco
        cursor = self.conn.cursor()
        cursor.execute("""
    SELECT id, nome, pais, estado, regiao, municipio, bairro, rua, numero, cnpj, contato, email,
           maquinas, producao, quantidade, status, ultima_compra, lembrete_dias, lat, lon, nome_fantasia
    FROM clientes WHERE id = %s
""", (id_cliente,))
        cliente = cursor.fetchone()

        if not cliente:
            QMessageBox.warning(self, "Erro", "Cliente não encontrado.")
            return

        _, nome, pais, estado, regiao, municipio, bairro, rua, numero, cnpj, contato, email, maquinas, producao, quantidade, status, ultima_compra, lembrete_dias, lat, lon, nome_fantasia = cliente

        # Preenche campos
        self.input_nome.setText(nome or "")

        index_pais = self.combo_pais.findText(pais or "")
        if index_pais != -1:
            self.combo_pais.setCurrentIndex(index_pais)


        self.input_estado.setText(estado or "")
        self.input_regiao.setText(regiao or "")
        self.input_municipio.setText(municipio or "")
        self.input_bairro.setText(bairro or "")
        self.input_rua.setText(rua or "")
        self.input_numero.setText(numero or "")
        self.input_cnpj.setText(cnpj or "")
        self.input_contato.setText(contato or "")
        self.input_email.setText(email or "")
        self.input_lat.setText(str(lat) if lat is not None else "")
        self.input_lon.setText(str(lon) if lon is not None else "")


        # Lista máquinas
        self.lista_maquinas.clear()
        if maquinas:
            for maq in maquinas.split(";"):
                maq_nome = maq.strip()
                if not maq_nome:
                    continue
                btn = QPushButton(maq_nome)
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        background: none;
                        border: none;
                        color: #7AAEFF;
                        text-decoration: underline;
                        font-weight: bold;
                    }
                """)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda _, m=maq_nome: self.ir_para_maquina(m))
                item = QListWidgetItem()
                self.lista_maquinas.addItem(item)
                self.lista_maquinas.setItemWidget(item, btn)

        self.input_producao.setText(producao or "")
        self.input_quantidade.setValue(int(quantidade or 0))

        index = self.input_status_cliente.findText(status)
        if index >= 0:
            self.input_status_cliente.setCurrentIndex(index)

        self.input_lembrete.setValue(int(lembrete_dias or 0))

        # Vai para aba de edição
        self.stack.setCurrentIndex(4)



    def _maquina_context_menu(self, pos):
        item = self.lista_maquinas.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        remover = menu.addAction("Remover")
        acao = menu.exec(self.lista_maquinas.mapToGlobal(pos))
        if acao == remover:
            row = self.lista_maquinas.row(item)
            self.lista_maquinas.takeItem(row)




    def adicionar_maquina(self):
        nome_maquina = self.input_maquinas.currentText().strip()
        if not nome_maquina:
            return

        # Adiciona na lista se ainda não estiver
        for i in range(self.lista_maquinas.count()):
            if self.lista_maquinas.item(i).text() == nome_maquina:
                return  # já existe
        self.lista_maquinas.addItem(nome_maquina)

        # --- Setar data de hoje para os componentes ---
        cursor = self.conn.cursor()
        componentes = COMPONENTES.get(nome_maquina.lower(), [])
        hoje = QDate.currentDate().toString("yyyy-MM-dd")

        for item in componentes:
            partes = item.split(";")
            descricao = partes[0] if len(partes) > 0 else ""

            # Verifica se já existe no banco
            cursor.execute("""
                SELECT id FROM pecas_clientes
                WHERE cliente_id=%s AND maquina=%s AND peca=%s
            """, (self.id_cliente_atual, nome_maquina, descricao))
            existe = cursor.fetchone()

            if existe:
                cursor.execute("""
                    UPDATE pecas_clientes
                    SET ultima_compra=%s
                    WHERE cliente_id=%s AND maquina=%s AND peca=%s
                """, (hoje, self.id_cliente_atual, nome_maquina, descricao))
            else:
                cursor.execute("""
                    INSERT INTO pecas_clientes (cliente_id, maquina, peca, ultima_compra)
                    VALUES (%s, %s, %s, %s)
                """, (self.id_cliente_atual, nome_maquina, descricao, hoje))

        self.conn.commit()

        # Atualiza tabela para mostrar as datas
        self.criar_pagina_maquina(nome_maquina, self.id_cliente_atual)



    def carregar_clientes(self):
        # Coleta dos filtros
        filtros = {
            "nome": self.input_nome_filtro.text().strip(),
            "cnpj": self.input_cnpj_filtro.text().strip(),
            "pais": self.combo_pais_filtro.currentText().strip(),
            "estado": self.combo_estado_filtro.currentText().strip(),
            "municipio": self.combo_municipio_filtro.currentText().strip(),
            "bairro": self.input_bairro_filtro.currentText().strip(),
            "rua": self.input_rua_filtro.currentText().strip(),
            "status": self.combo_status_filtro.currentText().strip(),
            "maquina": self.combo_maquina_filtro.currentText().strip(),
            "regiao": self.combo_regiao_filtro.currentText().strip()
        }

        cursor = self.conn.cursor()
        condicoes = []
        params = []

        # Filtro por máquina (ignora "Todas")
        if filtros["maquina"] and filtros["maquina"].lower() != "":
            condicoes.append("maquinas LIKE %s")
            params.append(f"%{filtros['maquina']}%")

        # Filtros gerais (ignora vazios)
        if filtros["nome"]:
            condicoes.append("(LOWER(nome) LIKE %s OR LOWER(nome_fantasia) LIKE %s)")
            params.append(f"%{filtros['nome'].lower()}%")
            params.append(f"%{filtros['nome'].lower()}%")
        if filtros["cnpj"]:
            condicoes.append("cnpj LIKE %s")
            params.append(f"%{filtros['cnpj']}%")
        if filtros["pais"] and filtros["pais"].lower() != "todas":
            condicoes.append("pais = %s")
            params.append(filtros["pais"])
        if filtros["estado"] and filtros["estado"].lower() != "todas":
            condicoes.append("estado = %s")
            params.append(filtros["estado"])
        if filtros["municipio"] and filtros["municipio"].lower() != "todas":
            condicoes.append("municipio = %s")
            params.append(filtros["municipio"])
        if filtros["bairro"]:
            condicoes.append("bairro LIKE %s")
            params.append(f"%{filtros['bairro']}%")
        if filtros["rua"]:
            condicoes.append("rua LIKE %s")
            params.append(f"%{filtros['rua']}%")
        if filtros["status"] and filtros["status"].lower() != "todas":
            condicoes.append("status = %s")
            params.append(filtros["status"])
        if filtros["regiao"] and filtros["regiao"].lower() != "todas":
            condicoes.append("regiao = %s")
            params.append(filtros["regiao"])

        # Montagem da query
        query = "SELECT id, nome, cnpj, status FROM clientes"
        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)

        # Ordenação
        if hasattr(self, "coluna_ordem") and self.coluna_ordem:
            direcao = "ASC" if self.ordem_crescente else "DESC"
            query += f" ORDER BY {self.coluna_ordem} {direcao}"

        # Execução da query
        cursor.execute(query, params)
        dados = cursor.fetchall()

        # Atualiza o label de resultados
        self.label_resultados.setText(f"Resultado: {len(dados)}")


        # Configuração da tabela
        self.tabela_clientes.clearContents()
        self.tabela_clientes.setRowCount(len(dados))
        self.tabela_clientes.setColumnCount(4)
        self.tabela_clientes.setHorizontalHeaderLabels(["", "Nome", "CNPJ", "Status"])
        self.tabela_clientes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabela_clientes.setColumnWidth(1, 1000)
        self.tabela_clientes.setColumnWidth(2, 300)
        self.tabela_clientes.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)

        self.checkboxes_linhas = []

        for i, (id_cliente, nome, cnpj, status) in enumerate(dados):
            # Checkbox
            cb = QCheckBox()
            cb.setProperty('id_cliente', id_cliente)
            cb.stateChanged.connect(self.on_row_checkbox_state_changed)
            self.checkboxes_linhas.append(cb)

            cell_widget = QWidget()
            layout_cb = QHBoxLayout(cell_widget)
            layout_cb.addWidget(cb)
            layout_cb.setAlignment(Qt.AlignCenter)
            layout_cb.setContentsMargins(0, 0, 0, 0)
            self.tabela_clientes.setCellWidget(i, 0, cell_widget)

            # Nome
            item_nome = QTableWidgetItem(nome)
            item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)
            self.tabela_clientes.setItem(i, 1, item_nome)

            # CNPJ
            item_cnpj = QTableWidgetItem(cnpj)
            item_cnpj.setFlags(item_cnpj.flags() & ~Qt.ItemIsEditable)
            self.tabela_clientes.setItem(i, 2, item_cnpj)

            # Status
            item_status = QTableWidgetItem(status if status else "")
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            self.tabela_clientes.setItem(i, 3, item_status)



        self.add_header_checkbox()
        self.on_row_checkbox_state_changed()



    def add_header_checkbox(self):
        header = self.tabela_clientes.horizontalHeader()

        # Remove checkbox antiga (se existir)
        if hasattr(self, "header_checkbox") and isinstance(self.header_checkbox, QCheckBox):
            try:
                header.sectionResized.disconnect(self.position_header_checkbox)
            except Exception:
                pass
            try:
                self.tabela_clientes.horizontalScrollBar().valueChanged.disconnect(self.position_header_checkbox)
            except Exception:
                pass
            try:
                self.header_checkbox.deleteLater()
            except Exception:
                pass

        # Cria checkbox no cabeçalho
        self.header_checkbox = QCheckBox(header)
        self.header_checkbox.setToolTip("Marcar/Desmarcar todos")
        self.header_checkbox.setTristate(True)     # permite mostrar parcial programaticamente
        self.header_checkbox.setFocusPolicy(Qt.NoFocus)
        self.header_checkbox.setChecked(False)

        # Conecta no clique do usuário (não em stateChanged)
        # assim garantimos que a ação do usuário sempre alternará corretamente
        try:
            if self.header_checkbox.receivers(self.header_checkbox.clicked) > 0:
                self.header_checkbox.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass


        self.header_checkbox.clicked.connect(self.header_clicked)
        self.header_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px; border-radius: 4px;
            }
            QCheckBox::indicator {
               width: 16px;
               height: 16px;
           }
        """)


        self.header_checkbox.show()
        self.header_checkbox.raise_()

        header.sectionResized.connect(self.position_header_checkbox)
        self.tabela_clientes.horizontalScrollBar().valueChanged.connect(self.position_header_checkbox)
        self.position_header_checkbox()

    def header_clicked(self, checked):
        """Chamado quando o usuário clica na checkbox do cabeçalho.
        Decide se marca ou desmarca todas as linhas com base no estado atual."""
        total = len(getattr(self, "checkboxes_linhas", []))
        if total == 0:
            return

        marcados = sum(1 for cb in self.checkboxes_linhas if cb.isChecked())

        # Se todas já estavam marcadas -> vamos desmarcar.
        # Caso contrário -> marcar todas.
        target = False if marcados == total else True

        for cb in self.checkboxes_linhas:
            cb.blockSignals(True)
            cb.setChecked(target)
            cb.blockSignals(False)

        # atualiza visual do header para refletir a nova situação
        self.header_checkbox.blockSignals(True)
        self.header_checkbox.setCheckState(Qt.Checked if target else Qt.Unchecked)
        self.header_checkbox.blockSignals(False)

        self.tabela_clientes.viewport().update()



    def position_header_checkbox(self, *args):
        """Mantém o checkbox centralizado no cabeçalho da primeira coluna.
        Aceita *args porque alguns sinais emitem parâmetros."""
        header = self.tabela_clientes.horizontalHeader()
        if hasattr(self, "header_checkbox"):
            x = header.sectionPosition(0) - self.tabela_clientes.horizontalScrollBar().value()
            x += (header.sectionSize(0) - self.header_checkbox.width()) // 2
            x -= 4
            y = (header.height() - self.header_checkbox.height()) // 2
            self.header_checkbox.move(x, y)
            self.header_checkbox.raise_()


    def marcar_todos(self, state):
        """Marca ou desmarca todos os checkboxes das linhas de acordo com a checkbox do cabeçalho."""
        # Trata Partial como Checked quando o usuário clica
        checado = (state != Qt.Unchecked)
        for cb in getattr(self, "checkboxes_linhas", []):
            cb.blockSignals(True)
            cb.setChecked(checado)
            cb.blockSignals(False)
        self.tabela_clientes.viewport().update()



    def on_row_checkbox_state_changed(self, *args):
        """Atualiza o estado da checkbox do cabeçalho conforme checkboxes das linhas."""
        if not getattr(self, "checkboxes_linhas", None):
            return

        total = len(self.checkboxes_linhas)
        marcados = sum(1 for cb in self.checkboxes_linhas if cb.isChecked())

        if hasattr(self, "header_checkbox"):
            self.header_checkbox.blockSignals(True)
            if marcados == 0:
                self.header_checkbox.setCheckState(Qt.Unchecked)
            elif marcados == total:
                self.header_checkbox.setCheckState(Qt.Checked)
            else:
                self.header_checkbox.setCheckState(Qt.PartiallyChecked)
            self.header_checkbox.blockSignals(False)



    def excluir_cliente(self):
        ids_para_excluir = []
        for i in range(self.tabela_clientes.rowCount()):
            cell_widget = self.tabela_clientes.cellWidget(i, 0)
            if not cell_widget:
                continue
            cb = cell_widget.findChild(QCheckBox)
            if cb and cb.isChecked():
                ids_para_excluir.append(cb.property('id_cliente'))

        if not ids_para_excluir:
            QMessageBox.warning(self, "Erro", "Selecione pelo menos um cliente para excluir.")
            return

        confirmar = QMessageBox(self)
        confirmar.setWindowTitle("Confirmar Exclusão")
        confirmar.setText(f"Tem certeza que deseja excluir {len(ids_para_excluir)} cliente(s)?")
        confirmar.setIcon(QMessageBox.Question)

        # Botões em português
        btn_sim = confirmar.addButton("Sim", QMessageBox.YesRole)
        btn_nao = confirmar.addButton("Não", QMessageBox.NoRole)

        confirmar.exec()

        if confirmar.clickedButton() != btn_sim:
            return


        cursor = self.conn.cursor()
        cursor.executemany("DELETE FROM clientes WHERE id = %s", [(i,) for i in ids_para_excluir])
        self.conn.commit()
        for i in ids_para_excluir:
            self.log_acao("Exclusão", f"ID {i}")
        self.carregar_clientes()




    def criar_pagina_configuracoes(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setAlignment(Qt.AlignCenter)

        titulo = QLabel("⚙ Configurações")
        titulo.setStyleSheet("color: #e6faff; font-size: 20px; padding: 8px;")
        layout.addWidget(titulo)

        tema_escuro_btn = QRadioButton("Tema escuro")
        tema_claro_btn = QRadioButton("Tema claro")


        grupo_temas = QButtonGroup(pagina)
        grupo_temas.addButton(tema_escuro_btn)
        grupo_temas.addButton(tema_claro_btn)


        if self.tema_atual == "escuro":
            tema_escuro_btn.setChecked(True)
        elif self.tema_atual == "claro":
            tema_claro_btn.setChecked(True)


        layout.addWidget(tema_escuro_btn)
        layout.addWidget(tema_claro_btn)


        salvar = QPushButton("💾 Salvar")
        salvar.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
                border: 1px solid #aaa;
            }
        """)
        salvar.clicked.connect(lambda: self.set_tema(
            "escuro" if tema_escuro_btn.isChecked() else
            "claro" if tema_claro_btn.isChecked() else
            "transparente"
        ))

        layout.addWidget(salvar)
        return pagina

    def criar_pagina_sair(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setAlignment(Qt.AlignCenter)

        titulo = QLabel("⚠ Deseja realmente sair?")
        titulo.setStyleSheet("color: #ff8080; font-size: 20px; padding: 8px;")
        layout.addWidget(titulo)

        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(40)

        btn_confirmar = QPushButton("Sim, sair")
        btn_confirmar.setStyleSheet("background-color: red; color: white; font-size: 16px;")
        btn_confirmar.clicked.connect(QApplication.quit)
        botoes_layout.addWidget(btn_confirmar)
        btn_confirmar.setShortcut(Qt.Key_Return)
        btn_confirmar.setAutoDefault(True)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: gray; color: white; font-size: 16px;")
        btn_cancelar.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        botoes_layout.addWidget(btn_cancelar)

        layout.addLayout(botoes_layout)
        return pagina

    # ===== Temas =====
    def set_tema(self, tema):
        if tema == "escuro":
            style = """
            QWidget {
                background-color: #222;
                color: white;
            }
            QPushButton {
                background-color: #444;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QLineEdit, QSpinBox, QDateEdit {
                border: 1px solid #888;
                border-radius: 4px;
                padding: 4px;
                background-color: #1c1c1c;
                color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QDateEdit:focus {
                border: 1px solid #00aaff;
                background-color: #2b2b2b;
            }
            /* QComboBox com seta ∇ */
            QComboBox {
                border: 1px solid #888;
                border-radius: 4px;
                padding: 4px;
                padding-right: 25px;
                background-color: #1c1c1c;
                color: white;
            }
            QComboBox:focus {
                border: 1px solid #00aaff;
                background-color: #2b2b2b;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #555;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                color: white;
                font-size: 14px;
                width: 12px;
                height: 12px;
            }
            /* Remove botões do QSpinBox */
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
            }
            QTableWidget {
                gridline-color: #555;
                background-color: #333;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
            }
            QLabel {
                padding-right: 5px;
            }
            /* Estilo base para CheckBox */
            QCheckBox {
                border: none;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #005a9e;
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
                border: 1px solid #555;
            }
            /* Checkbox do cabeçalho */
            QTableView::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
            }
            QTableView::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #005a9e;
            }
            QTableView::indicator:unchecked {
                background-color: transparent;
                border: 1px solid #555;
            }
            """
        else:  # tema claro
            style = """
            QWidget {
                background-color: #f0f0f0;
                color: black;
            }
            QPushButton {
                background-color: #ddd;
                border: 1px solid #888;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #ccc;
            }
            QLineEdit, QSpinBox, QDateEdit {
                border: 1px solid #888;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus, QSpinBox:focus, QDateEdit:focus {
                border: 1px solid #00aaff;
                background-color: #e6f2ff;
            }
            /* QComboBox com seta ∇ */
            QComboBox {
                border: 1px solid #888;
                border-radius: 4px;
                padding: 4px;
                padding-right: 25px;
                background-color: white;
                color: black;
            }
            QComboBox:focus {
                border: 1px solid #00aaff;
                background-color: #e6f2ff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #aaa;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                color: black;
                font-size: 14px;
                width: 12px;
                height: 12px;
            }
            /* Remove botões do QSpinBox */
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
            }
            QTableWidget {
                gridline-color: #ccc;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #ddd;
                color: black;
            }
            QLabel {
                padding-right: 5px;
            }
            /* Estilo base para CheckBox */
            QCheckBox {
                border: none;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #005a9e;
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
                border: 1px solid #555;
            }
            /* Checkbox do cabeçalho */
            QTableView::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
            }
            QTableView::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #005a9e;
            }
            QTableView::indicator:unchecked {
                background-color: transparent;
                border: 1px solid #555;
            }
            """
        self.setStyleSheet(style)




    def iniciar_barra(self, mensagem, caminho):
        pagina = self.stack.currentWidget()

        self.barra = QProgressBar(pagina)
        largura = 250
        altura = 25
        y_pos = 150
        x_pos = (pagina.width() - largura) // 2
        self.barra.setGeometry(x_pos, y_pos, largura, altura)
        self.barra.setRange(0, 0)
        self.barra.setFormat(mensagem)
        self.barra.show()

        exe_name = caminho.split("\\")[-1].lower()

        def rodar():
            subprocess.Popen([caminho])
            # Aguarda até o processo estar na lista
            for _ in range(50):  # até ~5 segundos
                if any(proc.info["name"] and proc.info["name"].lower() == exe_name
                    for proc in psutil.process_iter(["name"])):
                    break
                time.sleep(0.1)
            QTimer.singleShot(100, self.barra.deleteLater)

        threading.Thread(target=rodar, daemon=True).start()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    sistema = SistemaOption()
    sistema.show()
    sys.exit(app.exec())