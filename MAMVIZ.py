from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import pandas as pd
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import os
import logging
from rapidfuzz import process, fuzz
import re
from collections import defaultdict
import customtkinter as ctk
import win32com.client
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import sys
import subprocess
import shutil
import requests
import threading

# Função 1 - cria janela

# Janela principal oculta
janela_principal = ctk.CTk()
janela_principal.withdraw()

# Criar a barra de progresso como Toplevel
def criar_janela_progresso():
    global progresso_win, status_label, progress_bar, log_frame

    progresso_win = ctk.CTkToplevel(janela_principal)
    progresso_win.title("MAMVIZ - Progresso")
    progresso_win.geometry("200x300+0+0")
    progresso_win.resizable(False, False)
    progresso_win.attributes("-topmost", True)

    status_label = ctk.CTkLabel(progresso_win, text="Iniciando...", font=("Bahnschrift", 14), wraplength=260)
    status_label.pack(pady=5, fill="x")

    progress_bar = ctk.CTkProgressBar(progresso_win, width=250)
    progress_bar.pack(pady=5)
    progress_bar.set(0)

    log_frame = ctk.CTkFrame(progresso_win, fg_color="transparent")
    log_frame.pack(pady=5, fill="x")

# Função de limpar log
def limpar_log():
    for widget in log_frame.winfo_children():
        widget.destroy()
    progresso_win.update_idletasks()

# Função de atualizar status
def atualizar_status(texto, progresso=None):
    status_label.configure(text=texto)
    if progresso is not None:
        progress_bar.set(progresso)
    msg = ctk.CTkLabel(log_frame, text=texto, font=("Bahnschrift", 12), anchor="w", justify="left")
    msg.pack(anchor="w", fill="x", pady=1)
    progresso_win.update_idletasks()



def fluxo():
    limpar_log()

    # Substitua com o número que AUTORIZOU o CallMeBot (com DDI)
    phone_number = "+5527995074681"  
    # Substitua com a API Key que o bot te respondeu
    api_key = "8928305"  
    root = ctk.CTk()

    def conectar_inventor():
        try:
            inventor = win32com.client.Dispatch("Inventor.Application")
            return inventor
        except Exception as e:
            print("Erro ao conectar com o Inventor:", e)
            return None
        
    def extrair_linhas_bom(bom_rows, dados):
        for linha in bom_rows:
            try:
                if hasattr(linha, "ComponentDefinitions") and linha.ComponentDefinitions and linha.ComponentDefinitions.Count > 0:
                    props = linha.ComponentDefinitions(1).Document.PropertySets
                    num_estoque = props("Design Tracking Properties").Item("Stock Number").Value
                    num_peca = props("Design Tracking Properties").Item("Part Number").Value
                else:
                    num_estoque = "N/A"
                    num_peca = "N/A"

                unidade = getattr(linha.UnitOfMeasure, "Value", "N/A") if hasattr(linha, "UnitOfMeasure") else "N/A"
                qtde = linha.ItemQuantity if hasattr(linha, 'ItemQuantity') else "N/A"

                print(f"{num_peca} | Unidade: {unidade} | QTDE: {qtde}")
                dados.append([num_estoque, num_peca, unidade, qtde])
            except Exception as e:
                print(f"⚠️ Erro ao processar linha: {e}")
                dados.append(["N/A", "N/A", "N/A", "N/A"])

            if hasattr(linha, "ChildRows") and linha.ChildRows and linha.ChildRows.Count > 0:
                extrair_linhas_bom(linha.ChildRows, dados)
                
    def extrair_bom(inventor, caminho_iam):
        try:
            pasta_iam = os.path.dirname(caminho_iam)
            nome_base = os.path.splitext(os.path.basename(caminho_iam))[0]
            pasta_destino = os.path.join(pasta_iam, nome_base)
            os.makedirs(pasta_destino, exist_ok=True)

            caminho_excel = os.path.join(pasta_destino, "planilha_atualizada.xlsx")
            caminho_log_txt = os.path.join(pasta_destino, "caminho_atualizada.txt")

            with open(caminho_log_txt, "w", encoding="utf-8") as log:
                log.write(caminho_excel)
            print(f"📝 Caminho da planilha registrado em: {caminho_log_txt}")

            # Abre a montagem no Inventor
            doc = inventor.Documents.Open(caminho_iam)
            bom = doc.ComponentDefinition.BOM

            # Garantir que a vista "Somente peças" está ativada
            bom.StructuredViewEnabled = False  # Desativa a estruturada
            bom.PartsOnlyViewEnabled = True    # Garante que a "Somente peças" está ativa

            # Tenta pegar a vista pelo nome em português ou inglês
            try:
                parts_only_view = bom.BOMViews.Item("Somente peças")
            except:
                parts_only_view = bom.BOMViews.Item("Parts Only")

            dados = []
            extrair_linhas_bom(parts_only_view.BOMRows, dados)

            # Salvar no Excel
            df = pd.DataFrame(dados, columns=["Número de estoque", "Nº da peça", "Unidade da QTDE", "QTDE"])
            df.to_excel(caminho_excel, index=False)
            doc.Close()

            print("✅ Planilha salva em:", caminho_excel)

        except Exception as e:
            print("Erro ao extrair BOM:", e)

        return caminho_iam
            
    def executar_processo():
        Tk().withdraw()
        atualizar_status("Selecionando montagem IAM...", 0.10)
        
        inventor = conectar_inventor()
        if inventor:
            caminho_iam = askopenfilename(
                title="Selecione o arquivo de montagem (.iam)",
                filetypes=[("Montagem do Inventor", "*.iam")]
            )
            if caminho_iam:
                atualizar_status("Extraindo BOM...", 0.20)
                extrair_bom(inventor, caminho_iam)
                inventor.Quit()
                return caminho_iam  # 🔥 Adicionado aqui!
        return None  # Também útil se nada for selecionado

    def confirmar_salvamento_outra_maquina():
        janela = ctk.CTk()
        janela.title("MAMVIZ")

        largura, altura = 500, 300
        pos_x = (janela.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = (janela.winfo_screenheight() // 2) - (altura // 2)
        janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

        resposta = ctk.BooleanVar(value=False)
        frame = ctk.CTkFrame(janela)
        frame.pack(expand=True, pady=20, padx=20)

        mensagem = (
            "Você deseja atualizar\n"
            "outra máquina neste momento?\n\n"
            "Essa ação irá repetir o processo completo."
        )
        ctk.CTkLabel(frame, text=mensagem, font=("Bahnschrift", 14), wraplength=420, justify="center").pack(pady=10)

        def confirmar():
            resposta.set(True)
            janela.quit()
            janela.destroy()

        def cancelar():
            resposta.set(False)
            janela.quit()
            janela.destroy()

        botoes = ctk.CTkFrame(frame)
        botoes.pack(pady=10)
        ctk.CTkButton(botoes, text="✅ Sim!", command=confirmar).pack(side="left", padx=15)
        ctk.CTkButton(botoes, text="❌ Não, encerrar!", command=cancelar).pack(side="left", padx=15)

        janela.mainloop()
        return resposta.get()

    def obter_caminho_planilha_atualizada_por_iam(caminho_iam):
        nome_base = os.path.splitext(os.path.basename(caminho_iam))[0]
        pasta_destino = os.path.join(os.path.dirname(caminho_iam), nome_base)
        caminho_log = os.path.join(pasta_destino, "caminho_atualizada.txt")

        if not os.path.exists(caminho_log):
            print(f"⚠️ Log 'caminho_atualizada.txt' não encontrado em: {caminho_log}")
            return None

        try:
            with open(caminho_log, "r", encoding="utf-8") as f:
                caminho_planilha = f.read().strip()
                print(f"📄 Planilha atualizada localizada em: {caminho_planilha}")
                return caminho_planilha
        except Exception as e:
            print(f"❌ Erro ao ler o log: {e}")
            logger_erros.error(f"Falha ao ler o log: → {str(e)}")
            return None

    def obter_caminho_planilha_original_por_iam(caminho_iam):
        nome_base = os.path.splitext(os.path.basename(caminho_iam))[0]
        pasta_destino = os.path.join(os.path.dirname(caminho_iam), nome_base)
        caminho_log = os.path.join(pasta_destino, "caminho_original.txt")

        if not os.path.exists(caminho_log):
            print(f"⚠️ Log 'caminho_original.txt' não encontrado em: {caminho_log}")
            return None

        try:
            with open(caminho_log, "r", encoding="utf-8") as f:
                caminho_planilha = f.read().strip()
                print(f"📄 Planilha original localizada em: {caminho_planilha}")
                return caminho_planilha
        except Exception as e:
            print(f"❌ Erro ao ler o log: {e}")
            logger_erros.error(f"Falha ao ler o log: → {str(e)}")
            return None
    
    caminho_iam = executar_processo()
    if caminho_iam:
        pasta_destino = os.path.join(os.path.dirname(caminho_iam), os.path.splitext(os.path.basename(caminho_iam))[0])

    pasta_logs = os.path.join(pasta_destino, "MAMVIZ")
    os.makedirs(pasta_logs, exist_ok=True)

    planilha_atualizada = obter_caminho_planilha_atualizada_por_iam(caminho_iam)
    planilha_original = obter_caminho_planilha_original_por_iam(caminho_iam)

    #CONFIRMAÇÃO DE EXCLUSÃO
    def perguntar_confirmacao_exclusao(lista_codigos):
        # 🧱 Inicializa janela
        janela_exclusao = ctk.CTk()
        janela_exclusao.title("MAMVIZ")

        # 📐 Tamanho e posição centralizada
        largura_janela = 500
        altura_janela = 300
        largura_tela = janela_exclusao.winfo_screenwidth()
        altura_tela = janela_exclusao.winfo_screenheight()
        pos_x = int((largura_tela / 2) - (largura_janela / 2))
        pos_y = int((altura_tela / 2) - (altura_janela / 2))
        janela_exclusao.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

        # 📝 Texto de confirmação
        mensagem = "Deseja realmente excluir os seguintes itens?\n\n" + "\n".join(lista_codigos)
        resposta = ctk.BooleanVar(value=False)

        frame = ctk.CTkFrame(janela_exclusao)
        frame.pack(expand=True, pady=20)

        ctk.CTkLabel(frame, text=mensagem, font=("Bahnschrift", 14), wraplength=400, justify="left").pack(pady=10)

        def confirmar_exclusao():
            resposta.set(True)
            janela_exclusao.quit()
            janela_exclusao.destroy()

        def cancelar_exclusao():
            resposta.set(False)
            janela_exclusao.quit()
            janela_exclusao.destroy()

        botoes_frame = ctk.CTkFrame(frame)
        botoes_frame.pack(pady=10)

        ctk.CTkButton(botoes_frame, text="✅ Sim, excluir", command=confirmar_exclusao).pack(side="left", padx=10)
        ctk.CTkButton(botoes_frame, text="❌ Cancelar", command=cancelar_exclusao).pack(side="left", padx=10)

        janela_exclusao.mainloop()
        return resposta.get()
    #CONFIRMAÇÃO DE CODIGO BASE
    def confirmar_codigo_base(parent, descricao_nova, codigo_sugerido, mais_parecido, score):
        janela_confirmacao = ctk.CTkToplevel(parent)
        janela_confirmacao.title("MAMVIZ")
        janela_confirmacao.grab_set()
        janela_confirmacao.transient(parent)

        largura_janela, altura_janela = 500, 300
        largura_tela = janela_confirmacao.winfo_screenwidth()
        altura_tela = janela_confirmacao.winfo_screenheight()
        pos_x = int((largura_tela / 2) - (largura_janela / 2))
        pos_y = int((altura_tela / 2) - (altura_janela / 2))
        janela_confirmacao.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

        resultado = ctk.StringVar(value=codigo_sugerido)

        texto = (
            f"Descrição: '{descricao_nova}'\n"
            f"Produto mais parecido: '{mais_parecido}'\n"
            f"Código sugerido: '{codigo_sugerido}'\n"
            "Deseja confirmar ou corrigir?"
        )

        frame = ctk.CTkFrame(janela_confirmacao)
        frame.pack(expand=True, pady=20)

        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 14)).pack(pady=10)
        entrada = ctk.CTkEntry(frame, placeholder_text="Confirme ou insira novo código base", textvariable=resultado)
        entrada.pack(pady=10)

        def confirmar():
            janela_confirmacao.destroy()

        janela_confirmacao.bind("<Return>", lambda event: confirmar())
        ctk.CTkButton(frame, text="✅ Confirmar", command=confirmar).pack(pady=10)

        parent.wait_window(janela_confirmacao)
        return resultado.get()
    #EXTRAÇÃO ADICIONADOS
    def extrair_adicionado(descricao_tag):
        padrao = r"\([^)]+\)\s+(.+?)\s+[^\s]+$"
        resultado = re.search(padrao, descricao_tag)
        return resultado.group(1) if resultado else None

    def mostrar_mensagem_sem_alteracao(parent):
        janela_alerta = ctk.CTkToplevel(parent)
        janela_alerta.title("MAMVIZ")
        janela_alerta.grab_set()
        janela_alerta.transient(parent)

        largura, altura = 400, 200
        pos_x = (janela_alerta.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = (janela_alerta.winfo_screenheight() // 2) - (altura // 2)
        janela_alerta.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

        frame = ctk.CTkFrame(janela_alerta)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        texto = "NENHUMA ALTERAÇÃO IDENTIFICADA!\nENCERRANDO PROGRAMA."
        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 16), justify="center").pack(pady=20)

        def fechar():
            janela_alerta.destroy()
            parent.quit()

        ctk.CTkButton(frame, text="OK", command=fechar).pack(pady=10)
        parent.wait_window(janela_alerta)

    def perguntar_possui_sigla(parent, adicionado):
        janela = ctk.CTkToplevel(parent)
        janela.title("MAMVIZ")

        largura_janela, altura_janela = 500, 180
        largura_tela, altura_tela = janela.winfo_screenwidth(), janela.winfo_screenheight()
        pos_x = int((largura_tela - largura_janela) / 2)
        pos_y = int((altura_tela - altura_janela) / 2)
        janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        janela.resizable(False, False)
        janela.grab_set()
        janela.transient(parent)

        resposta_sigla = ctk.BooleanVar(master=janela, value=False)

        frame = ctk.CTkFrame(janela)
        frame.pack(expand=True, pady=20)

        texto = f"O item '{adicionado}' possui algum tipo de trabalho?"
        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 15)).pack(pady=10)

        def confirmar(valor):
            resposta_sigla.set(valor)
            janela.destroy()

        botoes = ctk.CTkFrame(frame)
        botoes.pack(pady=10)
        ctk.CTkButton(botoes, text="✅ Sim", command=lambda: confirmar(True)).pack(side="left", padx=10)
        ctk.CTkButton(botoes, text="❌ Não", command=lambda: confirmar(False)).pack(side="left", padx=10)

        janela.wait_window()
        return resposta_sigla.get()




    def identificar_diferencas(planilha_original, planilha_atualizada, parent):
        # Leitura dos dados
        original = pd.read_excel(planilha_original)
        atualizada = pd.read_excel(planilha_atualizada)

        # Remover a coluna inútil (índice 2 → terceira coluna)
        original_util = original.drop(original.columns[2], axis=1)
        atualizada_util = atualizada.drop(atualizada.columns[2], axis=1)

        # Criar uma chave única por linha com as colunas úteis
        original_util["chave"] = original_util.astype(str).agg(" | ".join, axis=1)
        atualizada_util["chave"] = atualizada_util.astype(str).agg(" | ".join, axis=1)

        # Conjuntos para comparar
        original_set = set(original_util["chave"])
        atualizada_set = set(atualizada_util["chave"])

        removidos = original_set - atualizada_set
        adicionados = atualizada_set - original_set

        # 🛑 Se nenhuma diferença, exibir janela e encerrar
        if not removidos and not adicionados:
            mostrar_mensagem_sem_alteracao(root)
            sys.exit()

        # Exibir resultados
        print("🟥 Linhas REMOVIDAS da planilha original:")
        for linha in sorted(removidos):
            print(" -", linha)

        print("\n🟩 Linhas ADICIONADAS na planilha atualizada:")
        for linha in sorted(adicionados):
            print(" +", linha)
    #FUNCAO EXTRATORA DE ITENS REMOVIDOS
    def extrair_itens_removidos(planilha_original, planilha_atualizada):
        # Leitura das planilhas
        original = pd.read_excel(planilha_original)
        atualizada = pd.read_excel(planilha_atualizada)

        # Remover a coluna inútil (índice 2)
        original_util = original.drop(original.columns[2], axis=1)
        atualizada_util = atualizada.drop(atualizada.columns[2], axis=1)

        # Criar chave única por linha com colunas úteis
        original_util["chave"] = original_util.astype(str).agg(" | ".join, axis=1)
        atualizada_util["chave"] = atualizada_util.astype(str).agg(" | ".join, axis=1)

        # Conjuntos
        original_set = set(original_util["chave"])
        atualizada_set = set(atualizada_util["chave"])

        # Identificar removidos
        removidos = original_set - atualizada_set

        # Obter coluna 0 dos itens removidos
        valores_coluna_0_removidos = original_util[
            original_util["chave"].isin(removidos)
        ][original.columns[0]].tolist()

        # Mostrar e armazenar
        print("🟥 Itens removidos (coluna 0):")
        for valor in valores_coluna_0_removidos:
            print(" -", valor)

        return valores_coluna_0_removidos
    #FUNCAO EXTRAIR CODIGOS REMOVIDOS
    def extrair_codigos_removidos(planilha_original, planilha_atualizada):
        original = pd.read_excel(planilha_original)
        atualizada = pd.read_excel(planilha_atualizada)

        original_util = original.drop(original.columns[2], axis=1)
        atualizada_util = atualizada.drop(atualizada.columns[2], axis=1)

        original_util["chave"] = original_util.astype(str).agg(" | ".join, axis=1)
        atualizada_util["chave"] = atualizada_util.astype(str).agg(" | ".join, axis=1)

        removidos = set(original_util["chave"]) - set(atualizada_util["chave"])

        codigos_removidos = original_util[original_util["chave"].isin(removidos)][original.columns[0]].tolist()

        print("📦 Códigos removidos:")
        for codigo in codigos_removidos:
            mensagem = f"🟥 Código removido: '{codigo}'"
            print(mensagem)
            logger_removidos.info(mensagem)  # grava no log dedicado

        return codigos_removidos
    #FUNCAO EXTRATORA DE ITENS ADICIONADOS
    def extrair_itens_adicionados(planilha_original, planilha_atualizada):
        # Leitura das planilhas
        original = pd.read_excel(planilha_original)
        atualizada = pd.read_excel(planilha_atualizada)

        # Remover a coluna inútil (índice 2)
        original_util = original.drop(original.columns[2], axis=1)
        atualizada_util = atualizada.drop(atualizada.columns[2], axis=1)

        # Criar chave única por linha com colunas úteis
        original_util["chave"] = original_util.astype(str).agg(" | ".join, axis=1)
        atualizada_util["chave"] = atualizada_util.astype(str).agg(" | ".join, axis=1)

        # Conjuntos
        original_set = set(original_util["chave"])
        atualizada_set = set(atualizada_util["chave"])

        # Identificar adicionados
        adicionados = atualizada_set - original_set

        # Obter coluna 1 dos itens adicionados
        valores_coluna_1_adicionados = atualizada_util[
            atualizada_util["chave"].isin(adicionados)
        ][atualizada.columns[1]].tolist()

        # Mostrar e armazenar
        print("🟩 Itens adicionados (coluna 1):")
        for valor in valores_coluna_1_adicionados:
            print(" +", valor)

        return valores_coluna_1_adicionados
    # FUNCAO LOGIN
    def login():

        wait = WebDriverWait(chrome, 5)
        while True:          
            campo_login = wait.until(EC.presence_of_element_located((By.ID, "campologin")))
            campo_login.clear()
            campo_login.send_keys("mamviz.option")
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "senha"))).clear()
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "senha"))).send_keys("Mamviz2025")
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "metodo"))).click()
            # Verifica se há mensagem de erro
            try:
                erro_login = chrome.find_element(By.CLASS_NAME, "mensagem-erro-login")
                print("MAMVIZ: Erro detectado na autenticação. Tentando novamente...")
            except:
                print("MAMVIZ: Identificação válida. Avançando no protocolo.")
                break
    #FUNCAO IDENTIFICADORA E EXTRATORA DE FINALIDADES
    def extrair_finalidade_por_codigo(codigos):
        mapa_finalidade = {
            "FT": "Fitilhador", "EB": "Embaladora", "BL": "Boleadora", "GN": "Granulador",
            "MD": "Modeladora", "TR": "Transportes", "DV": "Divisora", "ES": "Ensacadora",
            "CE": "Cortador Elevador", "UC": "Uso e consumo", "IN": "Insumo", "GR": "Geral",
            "MP": "Matéria - prima", "EQ": "Equipamento", "FD": "Fatiadora", "FR": "Ferramenta"
        }

        resultado = []
        for codigo in codigos:
            # Detecta prefixo (parte antes do "-") ou marca como sem prefixo
            prefixo = codigo.split("-")[0] if "-" in codigo else "ND"
            finalidade = mapa_finalidade.get(prefixo, "GR") if prefixo != "ND" else "Geral"
            resultado.append({"Código": codigo, "Finalidade": finalidade})

        return resultado

    mapa_finalidade_por_tag = {
        215: "Boleadora",
        305: "Cortador Elevador",
        306: "Cortador Elevador",
        402: "Divisora",
        422: "Divisora",
        502: "Embaladora",
        505: "Embaladora",
        506: "Embaladora",
        514: "Ensacadora",
        515: "Ensacadora",
        517: "Transportes",
        519: "Ensacadora",
        525: "Transportes",
        526: "Transportes",
        527: "Transportes",
        528: "Transportes",
        529: "Transportes",
        530: "Transportes",
        531: "Transportes",
        532: "Transportes",
        533: "Transportes",
        534: "Transportes",
        538: "Transportes",
        540: "Transportes",
        541: "Transportes",
        543: "Transportes",
        544: "Transportes",
        545: "Transportes",
        546: "Transportes",
        547: "Transportes",
        548: "Transportes",
        549: "Transportes",
        550: "Transportes",
        551: "Transportes",
        552: "Transportes",
        553: "Transportes",
        554: "Transportes",
        604: "Fatiadora",
        607: "Fatiadora",
        608: "Fatiadora",
        609: "Fitilhador",
        610: "Fitilhador",
        611: "Fitilhador",
        612: "Fitilhador",
        620: "Fatiadora",
        718: "Granulador",
        719: "Granulador",
        720: "Granulador",
        721: "Granulador",
        722: "Granulador",
        1314: "Modeladora",
        1315: "Modeladora",
        1316: "Modeladora",
        1317: "Modeladora",
        1607: "Granulador",
        1914: "Ensacadora"
    }

    def extrair_finalidade_por_tag_embutido(codigo_tag):
        # Caso seja uma TAG "C-..." → finalidade Geral
        if isinstance(codigo_tag, str) and codigo_tag.startswith("C-"):
            return "Geral"
        
        # Filtra se é uma TAG reconhecida
        if not codigo_tag.startswith(("05-", "08-", "09-", "06-", "07", "PAINEL 02-", "02-")):
            return extrair_finalidade_por_codigo([codigo_tag])[0]["Finalidade"]  # Plano B imediato

        # Extrai todos os números da TAG e prioriza os últimos
        numeros_tag = re.findall(r"\d{3,4}", codigo_tag)
        for numero in reversed(numeros_tag):
            corpo_tag = int(numero.lstrip("0"))  # remove zero à esquerda
            if corpo_tag in mapa_finalidade_por_tag:
                return mapa_finalidade_por_tag[corpo_tag]
        
        # Se não achou no mapa, tenta pelo código
        return extrair_finalidade_por_codigo([codigo_tag])[0]["Finalidade"]


    #FUNCAO ARQUIVO CÓDIGO DO ITEM MAIS PARECIDO
    def mapear_codigos_parecidos(lista_adicionados, df_original):
        descricoes_originais = df_original.iloc[:, 1].dropna().tolist()
        mapa_codigos = {}
        codigos_usados_por = {}

        for descricao_nova in lista_adicionados:
            if descricao_nova.startswith(("05-", "C-05")):
                # 🎯 Código fixo para TAG 05
                codigo_confirmado = "FD-004992"
                print(f"Código fixo atribuído: {codigo_confirmado}")
                mapa_codigos[descricao_nova] = {
                    "codigo": codigo_confirmado,
                    "mais_parecido": "TAG prefixo 05",
                    "score": "manual"
                }
                codigos_usados_por.setdefault(codigo_confirmado, []).append(descricao_nova)
                continue  # 🧭 pula para o próximo item

            # 🧠 Lógica de similaridade original
            parecido, score, index = process.extractOne(
                descricao_nova, descricoes_originais, scorer=fuzz.ratio
            )
            linha_parecida = df_original[df_original.iloc[:, 1] == parecido]

            if not linha_parecida.empty:
                codigo_sugerido = linha_parecida.iloc[0, 0]
                codigo_confirmado = confirmar_codigo_base(root, descricao_nova, codigo_sugerido, parecido, score)
                print(f"{codigo_confirmado} digitado")

                mapa_codigos[descricao_nova] = {
                    "codigo": codigo_confirmado,
                    "mais_parecido": parecido,
                    "score": score
                }

                codigos_usados_por.setdefault(codigo_confirmado, []).append(descricao_nova)
            else:
                mapa_codigos[descricao_nova] = {
                    "codigo": None,
                    "mais_parecido": None,
                    "score": None
                }

        return mapa_codigos, codigos_usados_por
    #FUNCAO JANELA PARAMETRO
    def obter_parametro_do_item(parent, item_nome):
        janela = ctk.CTkToplevel(parent)
        janela.title("MAMVIZ")

        largura_janela, altura_janela = 500, 300
        largura_tela, altura_tela = janela.winfo_screenwidth(), janela.winfo_screenheight()
        pos_x = int((largura_tela - largura_janela) / 2)
        pos_y = int((altura_tela - altura_janela) / 2)
        janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        janela.resizable(False, False)
        janela.grab_set()
        janela.transient(parent)

        resultado = ctk.StringVar(master=janela)

        frame = ctk.CTkFrame(janela)
        frame.pack(expand=True, pady=20, padx=20)

        ctk.CTkLabel(
            frame,
            text=(f"Qual material e espessura?\nEx.: 304 2B 1,50MM\n"
                f"PS: Não precisa os parênteses\n📦 Item: {item_nome}"),
            font=("Bahnschrift", 16),
            justify="left"
        ).pack(pady=(0, 10))

        entrada = ctk.CTkEntry(frame, placeholder_text="Digite o parâmetro...", textvariable=resultado)
        entrada.pack(pady=10, fill="x")
        entrada.focus_set()

        def confirmar():
            janela.destroy()

        entrada.bind("<Return>", lambda e: confirmar())
        ctk.CTkButton(frame, text="✅ Confirmar", command=confirmar).pack(pady=10)

        janela.wait_window()  # espera fechar
        return resultado.get()


    def obter_sigla_final_do_item(parent, item_nome):
        janela = ctk.CTkToplevel(parent)
        janela.title("MAMVIZ")

        largura_janela, altura_janela = 500, 300
        largura_tela, altura_tela = janela.winfo_screenwidth(), janela.winfo_screenheight()
        pos_x = int((largura_tela - largura_janela) / 2)
        pos_y = int((altura_tela - altura_janela) / 2)
        janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        janela.resizable(False, False)
        janela.grab_set()
        janela.transient(parent)
        janela.focus_force()
        resultado = ctk.StringVar(master=janela)

        frame = ctk.CTkFrame(janela)
        frame.pack(expand=True, pady=20, padx=20)

        ctk.CTkLabel(
            frame,
            text=f"Tipo de trabalho? Ex.: CA; CD; WA\n🔤 Item: {item_nome}",
            font=("Bahnschrift", 16)
        ).pack(pady=(0, 10))

        entrada = ctk.CTkEntry(frame, placeholder_text="Ex.: CA; CD; WA", textvariable=resultado)
        entrada.pack(pady=10, fill="x")
        entrada.focus_set()

        def confirmar():
            janela.destroy()

        entrada.bind("<Return>", lambda e: confirmar())
        ctk.CTkButton(frame, text="✅ Confirmar", command=confirmar).pack(pady=10)

        janela.wait_window()
        return resultado.get()


    #FUNCAO OBTER CODIGO PRODUTO PAI
    def obter_codigo_pai(inventor, caminho_iam):

        doc = inventor.Documents.Open(caminho_iam)

        propriedades = doc.PropertySets
        numero_estoque = propriedades("Design Tracking Properties").Item("Stock Number").Value

        doc.Close()
        print(f"🆔 Número de estoque da máquina (aba Projeto): {numero_estoque}")
        return numero_estoque
    #FUNCAO CLONAR PRODUTO COM BASE NA DESCRIÇÃO MAIS PARECIDA
    def criando_novo_produto_com_parecidos(chrome, lista_removidos, lista_adicionados, df_original, codigos_relacionados_para_clonar):
        atualizar_status("Clonando produtos no Nomus...", 0.45)
        chrome.get("https://optionbakery.nomus.com.br/optionbakery/Produto.do?metodo=Pesquisar")
        itens_com_tag_zero_nove = verificar_tags_em_adicionados_zero_nove(lista_adicionados)
        itens_com_tag_zero_oito = verificar_tags_em_adicionados_zero_oito(lista_adicionados)
        lista_descricoes_com_tag = []
        mapa_clonagem = {}

        def clonar_produto(codigo_base, descricao_final, finalidade_texto):
            
            campo_pesquisa = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "nomePesquisa")))
            campo_pesquisa.clear()
            campo_pesquisa.send_keys(str(codigo_para_clonar))
            campo_pesquisa.send_keys(Keys.RETURN)
            time.sleep(0.5)

            xpath = f"//span[normalize-space(text())='{codigo_base}']"
            try:
                span_item = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", span_item)
                span_item.click()
            except:
                print(f"⚠️⛔ Não foi possível encontrar o span para '{codigo_base}'")
                return

            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "produtoAtivoLiberado_itemSubMenu_clonarProduto"))).click()
            Select(WebDriverWait(chrome, 10).until(
                EC.presence_of_element_located((By.ID, "idTipoCodigoEstruturado"))
            )).select_by_visible_text("Novo código")
            time.sleep(0.5)

            descrição = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "descricao")))
            descrição.clear()
            descrição.send_keys(descricao_final)

            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "ui-id-27"))).click()
            time.sleep(1)
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "valoresAtributos_0"))).clear() #limpando endereço
            finalidade_element = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "valoresAtributos[1]")))
            Select(finalidade_element).select_by_visible_text(finalidade_texto)
            chrome.find_element(By.ID, "ui-id-26").click()
            padrao_supr = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "idPadraoSuprimento")))
            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", padrao_supr)
            Select(padrao_supr).select_by_visible_text("Como padrão comprado")
            ativo = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "ativoId")))
            try:
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", ativo)
                if not ativo.is_selected():
                    ativo.click()
            except Exception as e:
                print(f"⚠️ Erro ao marcar checkbox: {e}")
                logger_erros.error(f"Falha ao marcar checkbox: → {str(e)}")

            save_clone_produto = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar")))
            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_clone_produto)
            save_clone_produto.click()

            print(f"✅ Produto clonado com descrição: '{descricao_final}'")
        relacionamento_tag_por_item_base = {}
        for i, adicionado in enumerate(lista_adicionados):
            codigo_para_clonar = codigos_relacionados_para_clonar[i]
            finalidade_texto = extrair_finalidade_por_tag_embutido(adicionado) or "Geral"
            
            print(f"\n🚀 Processando '{adicionado}' com código base: {codigo_para_clonar}")



            if adicionado in itens_com_tag_zero_nove:
                parametros = obter_parametro_do_item(janela_principal, adicionado)
                print(f"{parametros} definido como parametro")

                # 🧬 Monta descrição com ou sem sigla
                if perguntar_possui_sigla(janela_principal, adicionado):
                    sigla = obter_sigla_final_do_item(janela_principal, adicionado)
                    descricao_tag = f"({parametros}) {adicionado} {sigla}"
                else:
                    descricao_tag = f"({parametros}) {adicionado}"

                logger_tag_09.info(
                    f"🔁 TAG 09 → '{adicionado}' → conversao:'{descricao_tag}' | Código base: {codigo_para_clonar}"
                )
                lista_descricoes_com_tag.append(descricao_tag)
                print(f"🔖 Clonando com TAG (09): '{descricao_tag}'")
                # Adiciona a nova descrição clonada associada ao item base
                if adicionado not in mapa_clonagem:
                    mapa_clonagem[adicionado] = []

                mapa_clonagem[adicionado].append(descricao_tag)
                clonar_produto(codigo_para_clonar, descricao_tag, finalidade_texto)

            elif adicionado in itens_com_tag_zero_oito:
                print(f"🔁 TAG 08 identificada. Clonando duas vezes para '{adicionado}'")

                # Clonagem simples
                primeiro_item_clonado = adicionado.strip()
                clonar_produto(codigo_para_clonar, adicionado, finalidade_texto)

                # Clonagem com TAG
                parametros = obter_parametro_do_item(janela_principal, adicionado)
                print(f"{parametros} definido como parametro")


                # 🧬 Monta descrição com ou sem sigla
                if perguntar_possui_sigla(janela_principal, adicionado):
                    sigla = obter_sigla_final_do_item(janela_principal, adicionado)
                    descricao_tag = f"({parametros}) {adicionado} {sigla}"
                else:
                    descricao_tag = f"({parametros}) {adicionado}"


                lista_descricoes_com_tag.append(descricao_tag)
                segundo_item_clonado = descricao_tag

                relacionamento_tag_por_item_base[primeiro_item_clonado] = segundo_item_clonado

                clonar_produto(codigo_para_clonar, descricao_tag, finalidade_texto)

                campo_pesquisa = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "descricaoPesquisa")))
                campo_pesquisa.clear()
                campo_pesquisa.send_keys(primeiro_item_clonado)
                campo_pesquisa.send_keys(Keys.RETURN)
                time.sleep(0.5)

                xpath_primeiro = f"//span[normalize-space(text())='{primeiro_item_clonado}']"
                try:
                    span_primeiro = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_primeiro)))
                    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", span_primeiro)
                    span_primeiro.click()
                    print(f"📂 Produto original reaberto: '{primeiro_item_clonado}'")
                except:
                    print(f"⚠️⛔ Não foi possível encontrar o produto '{primeiro_item_clonado}'")
                lista_materiais = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "produtoAtivoLiberado_itemSubMenu_acessarListaMateriais")))
                lista_materiais.click()
                save_incluir_material = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar")))
                save_incluir_material.click()
                time.sleep(1)
                add_item_estrutura = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_acessaradicionaritemestrutura")))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_item_estrutura)
                add_item_estrutura.click()
                time.sleep(1)
                search_produto = chrome.find_element(By.ID, "nome_produto")
                search_produto.send_keys(segundo_item_clonado)

                WebDriverWait(chrome, 10).until(EC.invisibility_of_element_located((By.ID, "ui-id-2")))
                WebDriverWait(chrome, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-menu-item-wrapper")))
                suspensao = chrome.find_elements(By.CLASS_NAME, "ui-menu-item-wrapper")
                for item in suspensao:
                    texto = item.text.strip()
                    if segundo_item_clonado in texto:
                        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                        item.click()
                        print(f"🟢 Item clicado na suspensão: '{texto}'")
                        break

                campo_qnt_necess = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "qtdeNecessaria_id")))
                campo_qnt_necess.send_keys("1")
                time.sleep(0.7)
                save_incluir = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar")))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_incluir)
                save_incluir.click()
                time.sleep(1)
                list_botao = chrome.find_elements(By.ID, "botao_pesquisar")
                for botao in list_botao:
                    if botao.get_attribute("value") == "Voltar":
                        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                        botao.click()
                        print("🔙 Botão 'Voltar' clicado com sucesso.")
                        time.sleep(1)
                        break
                exibir_todos = chrome.find_element(By.ID, "botao_exibir_todos")
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", exibir_todos)
                exibir_todos.click()
                time.sleep(1)

                # Adiciona a nova descrição clonada associada ao item base
                if adicionado not in mapa_clonagem:
                    mapa_clonagem[adicionado] = []

                mapa_clonagem[adicionado].append(descricao_tag)

            else:
                clonar_produto(codigo_para_clonar, adicionado, finalidade_texto)

        time.sleep(1.8)
        exibir_todos = chrome.find_element(By.ID, "botao_exibir_todos")
        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", exibir_todos)
        exibir_todos.click()



        return lista_descricoes_com_tag, mapa_clonagem, relacionamento_tag_por_item_base
    #FUNCAO EXTRAIR CODIIGO DA WEB (ITENS NORMAIS)        
    def extrair_codigo_por_descricao_web_normal(planilha_path, lista_adicionados):
        tabela = chrome.find_element(By.XPATH, "//table[starts-with(@class, 'tabelasDados tablesorter tablesorter-default')]")
        linhas = tabela.find_elements(By.XPATH, ".//tr")

        df = pd.read_excel(planilha_path)
        codigos_encontrados = []

        descricoes_planilha = df.iloc[:, 1].dropna().str.strip().tolist()

        for descricao_clonada in lista_adicionados:
            descricao_clonada = descricao_clonada.strip()
            quantidade = ''

            # Tenta encontrar uma descrição da planilha contida dentro da descrição clonada
            for i, linha_planilha in enumerate(descricoes_planilha):
                if linha_planilha in descricao_clonada:
                    quantidade = str(df.iat[i, 3]).strip()
                    break

            # Busca o código no site para a descrição clonada
            for linha in linhas:
                try:
                    celula_coluna_5 = linha.find_element(By.XPATH, ".//td[5]")
                    texto_site = celula_coluna_5.text.strip()

                    if descricao_clonada == texto_site:
                        celula_coluna_3 = linha.find_element(By.XPATH, ".//td[3]")
                        codigo = celula_coluna_3.text.strip()
                        codigos_encontrados.append(codigo)

                        print(f"📦 Descrição (site): '{descricao_clonada}' → Código: '{codigo}' → Quantidade: {quantidade}")
                        logging.info(f"📦 Descrição (site): '{descricao_clonada}' → Codigo_gerado: '{codigo}' → Quantidade: {quantidade}")
                        break
                except:
                    continue

        return codigos_encontrados
    #FUNCAO EXTRAIR CODIIGO DA WEB (ITENS COM TAG)  
    def extrair_codigo_por_descricao_web_tag(lista_adicionados, lista_descricoes_com_tag):
        tabela = chrome.find_element(By.XPATH, "//table[starts-with(@class, 'tabelasDados tablesorter tablesorter-default')]")
        linhas = tabela.find_elements(By.XPATH, ".//tr")

        mapa_codigos = {}

        for linha in linhas:
            try:
                celula_coluna_5 = linha.find_element(By.XPATH, ".//td[5]")
                texto_coluna_5 = celula_coluna_5.text

                celula_coluna_3 = linha.find_element(By.XPATH, ".//td[3]")
                texto_coluna_3 = celula_coluna_3.text.strip()

                if texto_coluna_5 in lista_descricoes_com_tag:
                    mapa_codigos[texto_coluna_5] = texto_coluna_3
                    print(f"📦 Descrição: '{texto_coluna_5}' → Código (coluna 3): '{texto_coluna_3}'")
            except:
                continue

        # Monta a lista final com base na ordem da lista_descricoes_com_tag
        codigos_encontrados = [
            mapa_codigos.get(descricao, '') for descricao in lista_descricoes_com_tag
        ]

        return codigos_encontrados
    #FUNCAO ATUALIZAR SOMENTE DESCRICOES NA PLANILHA
    def atualizar_somente_descricoes(planilha_path, lista_adicionados, lista_descricoes_com_tag, relacionamento_tag_por_item_base):
        df = pd.read_excel(planilha_path)

        for descricao_original in lista_adicionados:
            descricoes_possiveis = [descricao_original] + [
                desc for desc in lista_descricoes_com_tag if descricao_original in desc
            ]
            descricao_completa = next(
                (desc for desc in descricoes_possiveis if desc in lista_descricoes_com_tag),
                descricao_original
            )

            # ⚠️ Só atualiza se não for um item que originou uma clonagem com TAG
            if descricao_original not in relacionamento_tag_por_item_base.keys():
                linhas_encontradas = df[df.iloc[:, 1].isin(descricoes_possiveis)]
                for idx in linhas_encontradas.index:
                    if df.iat[idx, 1] != descricao_completa:
                        df.iat[idx, 1] = descricao_completa
                        print(f"📝 Descrição atualizada na linha {idx}: '{descricao_completa}'")
            else:
                print(f"⏩ Protegendo item TAG com duplicata: '{descricao_original}'")

        df.to_excel(planilha_path, index=False)
        print("✅ Descrições atualizadas com base no mapeamento, preservando originais de TAGs clonadas.")
    #FUNCAO ATUALIZAR CODIGOS PELA DESCRICAO PLANILHA
    def atualizar_codigos_via_log(planilha_path, log_path):
        atualizar_status("Atualizando planilha final...", 0.85)
        df = pd.read_excel(planilha_path)

        with open(log_path, 'r', encoding='latin1') as log:
            linhas_log = log.readlines()

        for idx in df.index:
            descricao = str(df.iat[idx, 1]).strip()
            codigo_atual = str(df.iat[idx, 0]).strip()

            if not codigo_atual or pd.isna(df.iat[idx, 0]):
                for linha in linhas_log:
                    if f"'{descricao}'" in linha and "Codigo_gerado:" in linha:
                        match_codigo = re.search(r"Codigo_gerado:\s*'([^']+)'", linha)
                        if match_codigo:
                            codigo_encontrado = match_codigo.group(1).strip()
                            df.iat[idx, 0] = codigo_encontrado
                            print(f"🧩 Linha {idx}: Código '{codigo_encontrado}' preenchido para '{descricao}'")
                            break  # interrompe a busca após encontrar

        df.to_excel(planilha_path, index=False)
        print("📦 Planilha atualizada com códigos extraídos do log.")
    #FUNCAO OBTER CÓDIGO DO ITEM MAIS PARECIDO
    def obter_codigo_do_item_parecido(descricao_nova, df_original):
        # Extrai lista de descrições da coluna correta
        descricoes_originais = df_original.iloc[:, 1].dropna().tolist()

        # Encontra a descrição mais parecida
        parecido, score, index = process.extractOne(descricao_nova, descricoes_originais, scorer=fuzz.ratio)

        # Localiza a linha do item mais parecido
        linha_parecida = df_original[df_original.iloc[:, 1] == parecido]

        if not linha_parecida.empty:
            codigo = linha_parecida.iloc[0, 0]  # Coluna 0 = código
            return {"novo_item": descricao_nova, "mais_parecido": parecido, "score": score, "codigo": codigo}
        else:
            return {"novo_item": descricao_nova, "mais_parecido": None, "score": None, "codigo": None}
    #FUNCAO VERIFICAR TAGS 09
    def verificar_tags_em_adicionados_zero_nove(lista_adicionados):
        # Tags válidas
        tags_validas = ["09-", "C-09"]
        
        # Lista que armazenará resultados
        itens_com_tag_zero_nove = []

        for descricao in lista_adicionados:
            if any(descricao.startswith(tag) for tag in tags_validas):
                print(f"🔖 TAG encontrada em: '{descricao}'")
                itens_com_tag_zero_nove.append(descricao)
            else:
                print(f"🚫 Sem TAG em: '{descricao}'")

        return itens_com_tag_zero_nove
    #FUNCAO VERIFICAR TAGS 08
    def verificar_tags_em_adicionados_zero_oito(lista_adicionados):
        # Tags válidas
        tags_validas = ["08-", "C-08"]
        
        # Lista que armazenará resultados
        itens_com_tag_zero_oito = []

        for descricao in lista_adicionados:
            if any(descricao.startswith(tag) for tag in tags_validas):
                print(f"🔖 TAG encontrada em: '{descricao}'")
                itens_com_tag_zero_oito.append(descricao)
            else:
                print(f"🚫 Sem TAG em: '{descricao}'")

        return itens_com_tag_zero_oito

    #FUNCAO OBTER QUANTIDADE VIA PLANILHA
    def obter_quantidade_por_descricao_original(planilha_path, descricao_original):
        df = pd.read_excel(planilha_path)

        descricao_original = descricao_original.strip()
        linha = df[df.iloc[:, 1].str.strip() == descricao_original]

        if not linha.empty:
            idx = linha.index[0]
            quantidade = str(df.iat[idx, 3]).strip()
            return quantidade
        else:
            print(f"❌ Descrição original '{descricao_original}' não encontrada na planilha.")
            return ''
    #FUNCAO REGISTRAR NO LOG
    def registrar_resultados_finais(planilha_path, lista_descricoes_clonadas, codigos_encontrados, mapa_clonagem, relacionamento_tag_por_item_base):
        df = pd.read_excel(planilha_path)

        for i, descricao_clonada in enumerate(lista_descricoes_clonadas):
            descricao_clonada = descricao_clonada.strip()
            codigo = codigos_encontrados[i]
            quantidade = ''

            # Tenta achar a quantidade pela descrição original via mapa_clonagem
            descricao_original = None
            for base, clonadas in mapa_clonagem.items():
                if descricao_clonada in clonadas:
                    descricao_original = base
                    break

            if descricao_original:
                linha = df[df.iloc[:, 1].str.strip() == descricao_original]
                if not linha.empty:
                    idx = linha.index[0]
                    quantidade = str(df.iat[idx, 3]).strip()
            else:
                # Se não é TAG/clonado, tenta bater direto com a descrição
                linha = df[df.iloc[:, 1].str.strip() == descricao_clonada]
                if not linha.empty:
                    idx = linha.index[0]
                    quantidade = str(df.iat[idx, 3]).strip()

            # Monta mensagem
            if quantidade != '':
                mensagem = f"📦 Descrição: '{descricao_clonada}' → Codigo_gerado: '{codigo}' → Quantidade: {quantidade}"
            else:
                mensagem = f"📦 Descrição: '{descricao_clonada}' → Código: '{codigo}'"

            print(mensagem)
            # Verifica se é um segundo item clonado derivado de TAG 08
            if descricao_clonada in relacionamento_tag_por_item_base.values():
                continue  # pula este item, não salva no log
            logging.info(mensagem)
        
        for descricao in lista_adicionados:
            info = mapa_codigos.get(descricao)
            if info:
                codigo_base = info.get("codigo")
                quantidade = obter_quantidade_por_descricao_original(planilha_atualizada, descricao)
                if codigo_base and quantidade:
                    mensagem = f"📦 (BASE) Descrição: '{descricao}' → Código BASE: '{codigo_base}' → Quantidade: {quantidade}"
                    print(mensagem)
                    logging.info(mensagem)
    #EXTRAIR CODIGOS E QUANTIDADE DO LOG
    def extrair_codigos_e_quantidades_do_log(log_path):
        codigos_quantidades = []

        with open(log_path, 'r', encoding='latin1') as arquivo:
            for linha in arquivo:
                # Tenta extrair código
                match_codigo = re.search(r"Código.*?:\s*'([^']+)'", linha)

                # Tenta extrair quantidade (se existir)
                match_quantidade = re.search(r"(?:→\s*)?Quantidade:\s*(\d+)", linha)

                if match_codigo:
                    codigo = match_codigo.group(1)
                    quantidade = match_quantidade.group(1) if match_quantidade else ''
                    codigos_quantidades.append((codigo, quantidade))

        return codigos_quantidades
    #FUNCAO NOVA LISTA
    def incluir_nova_lista(resultado, chrome, caminho_planilha):

        # 🪪 Captura o código pai

        inventor = conectar_inventor()
        codigo_pai = obter_codigo_pai(inventor, caminho_iam)
        print(codigo_pai)
        if not codigo_pai:
            print("⛔ Nenhum código informado. A operação foi cancelada.")
            return
        # 🔄 Carrega a planilha
        df = pd.read_excel(caminho_planilha)

        # 🧠 Garante que todas as colunas necessárias existam
        colunas_necessarias = [
            "Código do produto pai", "Nome da lista", "Descrição da lista", "Qtde base",
            "Código do produto filho", "Qtde de peças", "Posição", "Recebe componente de terceiros para industrialização sob encomenda", 
            "Remete componente para industrialização em terceiros", "Informações complementares"
        ]
        for col in colunas_necessarias:
            if col not in df.columns:
                df[col] = ""

        # 📐 Ajusta a quantidade de linhas
        quant_linhas = len(resultado)
        linhas_atual = len(df)
        if linhas_atual > quant_linhas:
            df = df.iloc[:quant_linhas]
        elif linhas_atual < quant_linhas:
            faltam = quant_linhas - linhas_atual
            linhas_vazias = pd.DataFrame([[""] * len(df.columns)] * faltam, columns=df.columns)
            df = pd.concat([df, linhas_vazias], ignore_index=True)

        # 🧹 Limpa colunas
        df.loc[:, "Código do produto filho"] = ""
        df.loc[:, "Qtde de peças"] = ""

        # ✍️ Preenche os dados
        df["Código do produto pai"] = df["Código do produto pai"].astype("object")
        df["Código do produto filho"] = df["Código do produto filho"].astype("object")
        df.loc[:, "Código do produto pai"] = codigo_pai
        df.loc[:, "Nome da lista"] = "Lista padrão"
        df.loc[:, "Descrição da lista"] = "Lista padrão"
        df.loc[:, "Qtde base"] = "1"
        df.loc[:, "Posição"] = "1"
        df.loc[:, "Recebe componente de terceiros para industrialização sob encomenda"] = "0"
        df.loc[:, "Remete componente para industrialização em terceiros"] = "0"
        df.loc[:, "Informações complementares"] = ""

        # 🧮 Preenche os códigos e quantidades extraídos
        for i, (codigo, quantidade) in enumerate(resultado):
            df.loc[i, "Código do produto filho"] = str(codigo)
            df.loc[i, "Qtde de peças"] = str(quantidade)

        # 💾 Salva a planilha
        df.to_excel(caminho_planilha, index=False)
        print("✅ Planilha preenchida com sucesso usando loc e colunas nomeadas.")


        # 🌐 Envia ao Nomus
        chrome.get("https://optionbakery.nomus.com.br/optionbakery/ArquivoImportado.do?metodo=pesquisar")
        WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_acessarcriar"))).click()

        campo_arquivo = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "arquivo_id")))
        campo_arquivo.send_keys(caminho_planilha)

        tipo_importacao = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "tipoImportacao_id")))
        Select(tipo_importacao).select_by_visible_text("Importação de listas de materiais")

        comportamento = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "comportamentoListaDuplicada")))
        Select(comportamento).select_by_visible_text("Substituir a lista")

        save_importacao = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar")))
        save_importacao.click()


        nome_arquivo = "GABARITO FICHA TÉCNICA (BIM).xlsx"
        xpath = f"//span[normalize-space(text())='{nome_arquivo}']"

        elementos = WebDriverWait(chrome, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, xpath))
        )

        primeiro_elemento = elementos[0]
        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", primeiro_elemento)
        primeiro_elemento.click()

        WebDriverWait(chrome, 10).until(
            EC.presence_of_element_located((By.ID, "arquivoNaoProcessado_itemSubMenu_processarArquivoImportado"))
        ).click()
    #FUNCAO PARTE EXCLUIR
    def marcar_checkboxes_por_codigo_removido(chrome, planilha_original, planilha_atualizada):
        # 🟥 Extrai o código pai da planilha


        codigos_removidos = extrair_codigos_removidos(planilha_original, planilha_atualizada)
        if not codigos_removidos:
            print("📭 Nenhum código removido encontrado na comparação. Pulando exclusão.")
            return

        itens = WebDriverWait(chrome, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "tr-item-lista-materiais"))
        )

        codigos_visiveis_na_pagina = []

        for item in itens:
            texto_linha = item.text.strip()
            for cod in codigos_removidos:
                if cod in texto_linha:
                    codigos_visiveis_na_pagina.append(texto_linha)
                    try:
                        checkbox = item.find_element(By.XPATH, ".//input[@type='checkbox']")
                        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                        checkbox.click()
                        print(f"☑️ Marcado: {texto_linha}")
                    except Exception as e:
                        print(f"⚠️ Não foi possível marcar: {texto_linha} — {str(e)}")
                    break

        if not codigos_visiveis_na_pagina:
            print("📭 Nenhum dos códigos removidos está presente na página. Pulando ação de exclusão.")
            return

        # 🔔 Janela gráfica de confirmação
        if not perguntar_confirmacao_exclusao(codigos_visiveis_na_pagina):
            print("🚫 Exclusão cancelada pelo usuário.")
            return

        # 🧹 Ação de exclusão
        bt_acoes = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_Acoes")))
        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", bt_acoes)
        bt_acoes.click()

        bt_excluir_componentes = WebDriverWait(chrome, 10).until(
            EC.presence_of_element_located((By.ID, "botao_botao.excluir.componentes"))
        )
        bt_excluir_componentes.click()
    #FUNCAO ADICIONAR ITEM EM LISTA DE MATERIAIS
    def adicionar_item_lista_material_code_pai(chrome, caminho_log):
        # 📜 Extrai os códigos e quantidades registrados no log
        resultado = []
        codigos_processados = set()  # 🧩 Evita duplicidade

        with open(caminho_log, 'r', encoding='latin1') as log:
            for linha in log:
                match_codigo = re.search(r"Codigo_gerado:\s*'([^']+)'", linha)
                match_qtd = re.search(r"Quantidade:\s*(\d+)", linha)
                if match_codigo:
                    codigo = match_codigo.group(1).strip()
                    quantidade = match_qtd.group(1) if match_qtd else "1"
                    if codigo not in codigos_processados:
                        resultado.append((codigo, quantidade))
                        codigos_processados.add(codigo)  # 🧠 Marca como já processado
                    else:
                        print(f"⏩ Código '{codigo}' já processado anteriormente. Pulando.")
        atualizar_status("Obtendo código pai...", 0.65)
        # 🧭 Continua o processo normalmente
        inventor = conectar_inventor()
        codigo_pai = obter_codigo_pai(inventor, caminho_iam)
        print(f"🔗 Código Pai: {codigo_pai}")

        pesquisa_code = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "nomePesquisa")))
        pesquisa_code.clear()
        pesquisa_code.send_keys(codigo_pai)
        pesquisa_code.send_keys(Keys.RETURN)
        time.sleep(1)
        xpath_codigo_pai = f"//span[normalize-space(text())='{codigo_pai}']"
        span_codigo = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_codigo_pai)))
        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", span_codigo)
        span_codigo.click()

        WebDriverWait(chrome, 10).until(
            EC.presence_of_element_located((By.ID, "produtoAtivoLiberado_itemSubMenu_acessarListaMateriais"))
        ).click()
        time.sleep(1)

        for codigo, quantidade in resultado:
            print(f"🔄 Incluindo: {codigo} → Qtd: {quantidade}")
            try:
                add_item = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "botao_acessaradicionaritemestrutura")))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_item)
                add_item.click()
                time.sleep(0.8)
                WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "nome_produto"))).send_keys(codigo)

                WebDriverWait(chrome, 10).until(EC.invisibility_of_element_located((By.ID, "ui-id-2")))
                WebDriverWait(chrome, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-menu-item-wrapper")))
                suspensao = chrome.find_elements(By.CLASS_NAME, "ui-menu-item-wrapper")
                for item in suspensao:
                    texto = item.text.strip()
                    if codigo in texto:
                        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                        item.click()
                        print(f"🟢 Item selecionado: '{texto}'")
                        break

                WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "qtdeNecessaria_id"))).send_keys(quantidade)
                save_add_item = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar")))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_add_item)
                save_add_item.click()
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Falha ao incluir '{codigo}': {e}")


        marcar_checkboxes_por_codigo_removido(chrome, planilha_original, planilha_atualizada)
        time.sleep(1)
        # 🔙 Retorno à tela anterior
        list_botao = chrome.find_elements(By.ID, "botao_pesquisar")
        for botao in list_botao:
            if botao.get_attribute("value") == "Voltar":
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                botao.click()
                print("🔙 Retorno ao menu anterior concluído.")
                time.sleep(2)
                break
    #FUNCAO EXCLUIR           
    def excluir_itens_lista_materiais(chrome, planilha_original, planilha_atualizada, log_adicionados_path):
        
        if os.path.exists(log_adicionados_path) and os.path.getsize(log_adicionados_path) == 0:
            print("📭 Nenhum código adicionado encontrado. Iniciando exclusão via códigos removidos.")
            inventor = conectar_inventor()
            codigo_pai = obter_codigo_pai(inventor, caminho_iam)
            print(codigo_pai)
            chrome.find_element(By.NAME, "nomePesquisa").send_keys(codigo_pai)
            chrome.find_element(By.NAME, "nomePesquisa").send_keys(Keys.RETURN)

            xpath_codigo_pai = f"//span[normalize-space(text())='{codigo_pai}']"
            span_codigo = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_codigo_pai)))
            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", span_codigo)
            time.sleep(1)
            span_codigo.click()

            WebDriverWait(chrome, 10).until(
                EC.presence_of_element_located((By.ID, "produtoAtivoLiberado_itemSubMenu_acessarListaMateriais"))
            ).click()
            time.sleep(2)

            # 🔍 Carrega e exibe os códigos de itens removidos

            marcar_checkboxes_por_codigo_removido(chrome, planilha_original, planilha_atualizada)
            time.sleep(1)
            list_botao = chrome.find_elements(By.ID, "botao_pesquisar")
            for botao in list_botao:
                if botao.get_attribute("value") == "Voltar":
                    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                    botao.click()
                    print("🔙 Botão 'Voltar' clicado com sucesso.")
                    time.sleep(1)
                    break
        else:
            print("🟩 Códigos adicionados encontrados no log. Nenhuma exclusão automática será realizada.")
    #FUNCAO JANELA MENU PRINCIPAL
    def janela_selecionar_funcao():
        # 🎨 Estilo visual
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # 🪟 Criar janela centralizada
        janela_funcao = ctk.CTk()
        largura, altura = 600, 450
        x = int((janela_funcao.winfo_screenwidth() / 2) - (largura / 2))
        y = int((janela_funcao.winfo_screenheight() / 2) - (altura / 2))
        janela_funcao.geometry(f"{largura}x{altura}+{x}+{y}")
        janela_funcao.title("MAMVIZ")
        janela_funcao.resizable(False, False)

        # Valor a ser retornado
        resultado_escolhido = ctk.StringVar(value="")
        def selecionar(funcao):
            resultado_escolhido.set(funcao)
            print(f"MAMVIZ: Escolha → {funcao}")
            janela_funcao.withdraw()
            janela_funcao.quit()
            janela_funcao.destroy()  # 💥 Aqui você garante que a janela realmente se encerrou

        # 🔲 Layout visual
        frame = ctk.CTkFrame(janela_funcao)
        frame.pack(expand=True, pady=30)

        # Título
        ctk.CTkLabel(frame, text="✨ O que deseja fazer?", font=("Bahnschrift", 24, "bold")).pack(pady=(10, 20))

        # Botões
        ctk.CTkButton(frame, text="📋 Substituição em componente", width=300, height=60, corner_radius=15,
                    fg_color="#bb3500", hover_color="#ee6910", font=("Agency FB", 20),
                    command=lambda: selecionar("Componentes")).pack(pady=8)

        ctk.CTkButton(frame, text="📋 Alterar em lista existente", width=300, height=60, corner_radius=15,
                    fg_color="#1070ff", hover_color="#80b3ff", font=("Agency FB", 20),
                    command=lambda: selecionar("Alterar")).pack(pady=8)
        
        ctk.CTkButton(frame, text="📋 Nova lista", width=300, height=60, corner_radius=15,
                    fg_color="#21a300", hover_color="#66e25b", font=("Agency FB", 20),
                    command=lambda: selecionar("Novo")).pack(pady=8)

        ctk.CTkButton(frame, text="🗑️ Excluir itens da lista", width=300, height=60, corner_radius=15,
                    fg_color="#FD1024", hover_color="#ff6a7e", font=("Agency FB", 20),
                    command=lambda: selecionar("Excluir")).pack(pady=8)

        # 🧭 Executa interface
        janela_funcao.mainloop()
        return resultado_escolhido.get()
    #FUNCAO PERGUNTA MAQUINA VIA CODIGO BASE / GERADO
    def pergunta_maquina_por_vinculo(codigo_base, codigo_gerado):
        janela = ctk.CTk()
        janela.title("MAMVIZ")
        janela.geometry("500x300")
        janela.resizable(False, False)

        x = (janela.winfo_screenwidth() - 400) // 2
        y = (janela.winfo_screenheight() - 200) // 2
        janela.geometry(f"400x300+{x}+{y}")

        resultado = ctk.StringVar()

        frame = ctk.CTkFrame(janela)
        frame.pack(expand=True, pady=20)

        texto = f"📦 Item: '{codigo_base}'\n🔄 Gerando: '{codigo_gerado}'\nDigite o código da máquina:"
        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 15)).pack(pady=(0, 10))
        entrada = ctk.CTkEntry(frame, placeholder_text="Código da máquina", textvariable=resultado)
        entrada.pack(pady=10, padx=20)

        def confirmar():
            janela.quit()
            janela.destroy()

        janela.bind("<Return>", lambda event: confirmar())
        ctk.CTkButton(frame, text="✅ Confirmar", command=confirmar, font=("Agency FB", 18)).pack(pady=10)

        janela.mainloop()
        return resultado.get()
    #FUNCAO SELECIONAR ITEM (EM CASO DE MAIS DE 1 ITEM CLONADO COM UM CODIGO BASE)
    def selecione_item(codigo_base, opcoes):
        selecao_item = ctk.CTk()
        selecao_item.title("MAMVIZ")
        selecao_item.geometry("500x300")
        selecao_item.resizable(False, False)

        # Centralizar na tela
        largura_tela = selecao_item.winfo_screenwidth()
        altura_tela = selecao_item.winfo_screenheight()
        x = int((largura_tela / 2) - (400 / 2))
        y = int((altura_tela / 2) - (200 / 2))
        selecao_item.geometry(f"500x300+{x}+{y}")

        resultado = ctk.StringVar()  # valor padrão

        frame = ctk.CTkFrame(selecao_item)
        frame.pack(expand=True, pady=20)

        texto = f"📦 Item '{codigo_base}' foi usado para clonar mais de um produto.\nSelecione o produto destino:"
        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 15)).pack(pady=(0, 10))

        menu = ctk.CTkOptionMenu(frame, values=opcoes, variable=resultado)
        menu.pack(pady=10, padx=20)

        def confirmar():
            selecao_item.quit()
            selecao_item.destroy()

        selecao_item.bind("<Return>", lambda event: confirmar())
        ctk.CTkButton(frame, text="✅ Confirmar", command=confirmar, font=("Agency FB", 18)).pack(pady=10)

        selecao_item.mainloop()
        return resultado.get()
    #FUNCAO REPETIÇÃO 
    def deseja_repetir_substituicao(codigo_base, codigo_gerado):
        janela = ctk.CTk()
        janela.title("MAMVIZ")
        janela.geometry("500x180")
        janela.resizable(False, False)

        x = (janela.winfo_screenwidth() - 400) // 2
        y = (janela.winfo_screenheight() - 180) // 2
        janela.geometry(f"500x180+{x}+{y}")

        resultado = ctk.StringVar(value="Não")

        frame = ctk.CTkFrame(janela)
        frame.pack(expand=True, pady=20)

        texto = f"⚙️ Deseja repetir o processo de substituição\npara o item '{codigo_base}' → '{codigo_gerado}'?"
        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 14)).pack(pady=(0, 10))

        botoes_frame = ctk.CTkFrame(frame)
        botoes_frame.pack(pady=10)

        def confirmar(opcao):
            resultado.set(opcao)
            janela.quit()
            janela.destroy()

        ctk.CTkButton(botoes_frame, text="✅ Sim", width=100, command=lambda: confirmar("Sim")).pack(side="left", padx=10)
        ctk.CTkButton(botoes_frame, text="❌ Não", width=100, command=lambda: confirmar("Não")).pack(side="right", padx=10)

        janela.mainloop()
        return resultado.get()
    # Função que busca no log os códigos gerado/base a partir da descrição
    def extrair_mapeamento_por_descricao(caminho_log, lista_adicionados, mapa_clonagem, debug=False):
        mapeamento = {}

        # 📜 Carrega log principal
        with open(caminho_log, 'r', encoding='latin1') as log:
            linhas = log.readlines()

        for descricao in lista_adicionados:
            codigos_gerados = set()
            codigos_base = set()
            descricao_clonada = None  # ✅ Inicializa fora do if

            # 🎯 Se for TAG 09, usa a descrição clonada
            if descricao.startswith("09-") or descricao.startswith("C-09"):
                descricao_clonada = mapa_clonagem.get(descricao, [""])[0]

                if debug:
                    print(f"\n🔍 TAG 09: '{descricao}' → usando descrição clonada: '{descricao_clonada}'")

                for linha in linhas:
                    if f"'{descricao_clonada}'" in linha and "Codigo_gerado:" in linha:
                        match_gerado = re.search(r"Codigo_gerado: '([^']+)'", linha)
                        if match_gerado:
                            codigo_encontrado = match_gerado.group(1).strip()
                            codigos_gerados.add(codigo_encontrado)

                            if debug:
                                print(f"✅ Código gerado encontrado com descrição clonada: '{descricao_clonada}' → Código: '{codigo_encontrado}'")

                    if f"'{descricao}'" in linha and "codigo_base:" in linha:
                        match_base = re.search(r"codigo_base: ([0-9]+)", linha)
                        if match_base:
                            codigos_base.add(match_base.group(1).strip())

            else:
                # 🔍 Busca tradicional
                if debug:
                    print(f"\n🔍 Tradicional: buscando para '{descricao}'")

                for linha in linhas:
                    if f"Descrição (site): '{descricao}'" in linha and "Codigo_gerado:" in linha:
                        match_gerado = re.search(r"Codigo_gerado: '([^']+)'", linha)
                        if match_gerado:
                            codigos_gerados.add(match_gerado.group(1).strip())

                    if f"'{descricao}'" in linha and "codigo_base:" in linha:
                        match_base = re.search(r"codigo_base: ([0-9]+)", linha)
                        if match_base:
                            codigos_base.add(match_base.group(1).strip())

            # 🔧 Monta o dicionário do mapeamento
            mapeamento[descricao] = {
                "Codigo_gerado": list(codigos_gerados) if codigos_gerados else ["❌ Não encontrado"],
                "codigo_base": list(codigos_base) if codigos_base else ["❌ Não encontrado"],
                "descricao_clonada": descricao_clonada
            }

        return mapeamento
    #FUNCAO QUE DETECTA ITEM CLONADO
    def detectar_clonagem_multipla_e_selecionar(mapeamento_clonagem, codigos_removidos):
        mapa_base_para_gerados = defaultdict(list)

        with open(mapeamento_clonagem, 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                match = re.search(r"Codigo Base:\s*(\d+)\s*→ Codigo Gerado:\s*([^\s]+)", linha)
                if match:
                    codigo_base = match.group(1)
                    codigo_gerado = match.group(2)
                    mapa_base_para_gerados[codigo_base].append(codigo_gerado)

        escolhas = {}
        for removido in codigos_removidos:
            gerados = mapa_base_para_gerados.get(removido, [])
            print(f"🔍 Removido '{removido}' tem gerados: {gerados}")
            if len(gerados) > 1:
                escolha = selecione_item(removido, gerados)
                escolhas[removido] = escolha
            elif len(gerados) == 1:
                escolhas[removido] = gerados[0]
            else:
                print(f"⚠️ Nenhum gerado encontrado para '{removido}'")

        return escolhas, mapa_base_para_gerados
    #FUNCAO CONFIRMAÇÃO DE ITEM RESTANTE
    def confirmar_inclusao_manual(codigo_gerado):
        janela_confirmacao = ctk.CTk()
        janela_confirmacao.title("MAMVIZ")
        janela_confirmacao.geometry("500x180")
        janela_confirmacao.resizable(False, False)

        x = (janela_confirmacao.winfo_screenwidth() - 400) // 2
        y = (janela_confirmacao.winfo_screenheight() - 180) // 2
        janela_confirmacao.geometry(f"500x180+{x}+{y}")

        resultado = ctk.StringVar(value="")

        frame = ctk.CTkFrame(janela_confirmacao)
        frame.pack(expand=True, pady=20)

        texto = f"Ainda restou o código '{codigo_gerado}' que não foi substituído.\nDeseja incluir manualmente?"
        ctk.CTkLabel(frame, text=texto, font=("Bahnschrift", 14), wraplength=360).pack(pady=(0, 10))

        def escolher_sim():
            resultado.set("sim")
            janela_confirmacao.quit()
            janela_confirmacao.destroy()

        def escolher_nao():
            resultado.set("nao")
            janela_confirmacao.quit()
            janela_confirmacao.destroy()

        botoes_frame = ctk.CTkFrame(frame)
        botoes_frame.pack(pady=10)

        ctk.CTkButton(botoes_frame, text="✅ Sim", command=escolher_sim, width=100).pack(side="left", padx=10)
        ctk.CTkButton(botoes_frame, text="❌ Não", command=escolher_nao, width=100).pack(side="right", padx=10)

        janela_confirmacao.mainloop()
        return resultado.get()
    #FUNCAO CORPO PRINCIPAL MAMVIZ
    def executar_substituicao(chrome, codigo_base, codigo_gerado, quantidade):
        mapa_qtd_por_codigo = extrair_mapa_codigo_para_quantidade(log_path)
        quantidade = mapa_qtd_por_codigo.get(codigo_gerado, "1")  # fallback defensivo

        # toda aquela lógica de substituição vai aqui
        while True:
            
            resposta_maquina = pergunta_maquina_por_vinculo(codigo_base, f"{codigo_gerado} (Qtd: {quantidade})")
            # Substituição no Nomus
            chrome.find_element(By.NAME, "nomeProdutoComponentePesquisa").clear()
            chrome.find_element(By.NAME, "nomeProdutoComponentePesquisa").send_keys(codigo_base)
            chrome.find_element(By.NAME, "nomeProdutoPesquisa").clear()
            chrome.find_element(By.NAME, "nomeProdutoPesquisa").send_keys(resposta_maquina)
            chrome.find_element(By.NAME, "nomeProdutoPesquisa").send_keys(Keys.RETURN)
            time.sleep(0.5)
            checkboxes = WebDriverWait(chrome, 10).until(
                EC.presence_of_all_elements_located((By.ID, "marcaredesmarcar"))
            )
            time.sleep(0.5)
            checkboxes[0].click()
            print("☑️ Checkbox marcada!")

            # Ações Nomus
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_Acoes"))).click()
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_botao.substituir"))).click()
            time.sleep(1)
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "nome_produto"))).send_keys(codigo_gerado)
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "modificaQtdeComponentes_id"))).click()
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "qtdeNecessaria_id"))).send_keys(quantidade)
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar"))).click()

            # 🔁 Pergunta se deseja repetir
            deseja_repetir = deseja_repetir_substituicao(codigo_base, codigo_gerado)
            if deseja_repetir != "Sim":
                break  # Só repete se for “Sim”
    #FUNCAO AMARRA QUANTIDADE AO CÓDIGO
    def obter_quantidade_por_codigo(log_path, codigo_alvo):
        with open(log_path, 'r', encoding='latin1') as log:
            for linha in log:
                if f"→ Codigo_gerado: '{codigo_alvo}'" in linha:
                    match = re.search(r"(?:→\s*)?Quantidade:\s*(\d+)", linha)
                    if match:
                        return match.group(1)
        return "1"  # padrão se não encontrar
    #FUNCAO EXTRAIR CODIGO E QUANTIDADE
    def extrair_mapa_codigo_para_quantidade(log_path):
        mapa_codigo_qtd = {}
        with open(log_path, 'r', encoding='latin1') as log:
            for linha in log:
                match_codigo = re.search(r"Codigo_gerado:\s*'([^']+)'", linha)
                match_qtd = re.search(r"Quantidade:\s*(\d+)", linha)
                if match_codigo and match_qtd:
                    codigo = match_codigo.group(1).strip()
                    quantidade = match_qtd.group(1).strip()
                    mapa_codigo_qtd[codigo] = quantidade
        return mapa_codigo_qtd
    #FUNCAO RETORNO AO MENU PRINCIPAL
    def deseja_voltar_ao_menu():
        janela_menu = ctk.CTk()
        janela_menu.title("MAMVIZ")

        # 📐 Centraliza a janela
        largura_janela = 500
        altura_janela = 180
        largura_tela = janela_menu.winfo_screenwidth()
        altura_tela = janela_menu.winfo_screenheight()
        pos_x = int((largura_tela / 2) - (largura_janela / 2))
        pos_y = int((altura_tela / 2) - (altura_janela / 2))
        janela_menu.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

        resposta = ctk.BooleanVar(value=False)

        frame = ctk.CTkFrame(janela_menu)
        frame.pack(expand=True, pady=20)

        ctk.CTkLabel(
            frame,
            text="Deseja voltar ao menu principal?",
            font=("Bahnschrift", 14),
            justify="center"
        ).pack(pady=10)

        def confirmar():
            resposta.set(True)
            janela_menu.quit()
            janela_menu.destroy()

        def cancelar():
            resposta.set(False)
            janela_menu.quit()
            janela_menu.destroy()

        botoes = ctk.CTkFrame(frame)
        botoes.pack(pady=10)

        ctk.CTkButton(botoes, text="✅ Sim", command=confirmar).pack(side="left", padx=10)
        ctk.CTkButton(botoes, text="❌ Não", command=cancelar).pack(side="left", padx=10)

        janela_menu.mainloop()
        return resposta.get()
    # ⏹️ Envolve a execução do menu numa função para reaproveitar
    def executar_fluxo_mamviz():
        
        # while True:
        #     resposta = janela_selecionar_funcao()

        #     if resposta == "Novo":
        #         caminho_planilha = r'C:\Users\jonas.santos\Desktop\teste\GABARITO FICHA TÉCNICA (BIM).xlsx'
        #         incluir_nova_lista(resultado, chrome, caminho_planilha)

        #     elif resposta == "Alterar":
        
        caminho_log = os.path.join(pasta_logs, "engenharia_code.log")
        adicionar_item_lista_material_code_pai(chrome, caminho_log)

            # elif resposta == "Excluir":
            #     log_adicionados_path = r"C:\Users\jonas.santos\Desktop\teste\maternidade\build\MAMVIZ\codigos_adicionados.log"
            #     excluir_itens_lista_materiais(chrome, planilha_original, planilha_atualizada, log_adicionados_path)


            # elif resposta == "Componentes":
            #     chrome.get("https://optionbakery.nomus.com.br/optionbakery/Componente.do?metodo=PesquisarPaginado")

            #     mapeamento_clonagem_path = r'C:\Users\jonas.santos\Desktop\teste\maternidade\build\MAMVIZ\mapeamento_clonagem.log'
            #     escolhas_usuario, mapa_base_para_gerados = detectar_clonagem_multipla_e_selecionar(mapeamento_clonagem_path, codigos_removidos)
            #     for descricao, dados in mapeamento.items():
            #         print(f"\n📌 Descrição Original: {descricao}")
            #         origem_gerado = "Descrição Clonada" if dados.get("descricao_clonada") else "Descrição Original"
            #         print(f"  → Código Gerado(s) [{origem_gerado}]: {','.join(dados['Codigo_gerado'])}")
            #         print(f"  → Código Base(s):   {', '.join(dados['codigo_base'])}")
            #         # Detecta itens clonados mais de uma vez e permite seleção

            #     for codigo_base in dados['codigo_base']:
            #         for codigo_gerado in dados['Codigo_gerado']:

            #             for codigo_removido, escolha in escolhas_usuario.items():
            #                 # ⚠️ Verifica se há múltiplas escolhas para o mesmo código base
            #                 if isinstance(escolha, list) and len(escolha) > 1:
            #                     for item in escolha:
            #                         print(f"🧩 Código removido '{codigo_removido}' foi substituído por '{item}'")
            #                         while True:
            #                             resposta_maquina = pergunta_maquina_por_vinculo(codigo_removido, f"{item} (Qtd: {quantidade})")

            #                             # 🖱️ Substituição no Nomus
            #                             chrome.find_element(By.NAME, "nomeProdutoComponentePesquisa").clear()
            #                             chrome.find_element(By.NAME, "nomeProdutoComponentePesquisa").send_keys(codigo_removido)
            #                             chrome.find_element(By.NAME, "nomeProdutoPesquisa").clear()
            #                             chrome.find_element(By.NAME, "nomeProdutoPesquisa").send_keys(resposta_maquina)
            #                             chrome.find_element(By.NAME, "nomeProdutoPesquisa").send_keys(Keys.RETURN)
            #                             time.sleep(0.5)

            #                             checkboxes = WebDriverWait(chrome, 10).until(
            #                                 EC.presence_of_all_elements_located((By.ID, "marcaredesmarcar"))
            #                             )
            #                             time.sleep(0.5)
            #                             checkboxes[0].click()
            #                             print("☑️ Checkbox marcada!")
            #                             caminho_log = r'C:\Users\jonas.santos\Desktop\teste\maternidade\build\MAMVIZ\engenharia_code.log'
            #                             quantidade = obter_quantidade_por_codigo(caminho_log, item)
            #                             # 🛠️ Ações Nomus
            #                             WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_Acoes"))).click()
            #                             WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_botao.substituir"))).click()
            #                             time.sleep(1)
            #                             WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "nome_produto"))).send_keys(item)
            #                             WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "modificaQtdeComponentes_id"))).click()
            #                             WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "qtdeNecessaria_id"))).send_keys(quantidade)
            #                             WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar"))).click()

            #                             # 🔁 Pergunta se deseja repetir
            #                             deseja_repetir = deseja_repetir_substituicao(codigo_removido, item)
            #                             if deseja_repetir != "Sim":
            #                                 break
                            
            #             quantidade = obter_quantidade_por_descricao_original(planilha_atualizada, descricao)
            #             print(f"{quantidade} qnt encontrada")

            #             # 🔁 Inicializa controle de itens já tratados
            #             codigos_base_ja_tratados = set()

            #             # 🧠 Detecta e processa substituições com múltiplos gerados
            #             for codigo_removido, escolha in escolhas_usuario.items():
            #                 if isinstance(escolha, list):
            #                     for item in escolha:
            #                         executar_substituicao(chrome, codigo_removido, item, quantidade)
            #                     codigos_base_ja_tratados.add(codigo_removido)
            #                 else:
            #                     executar_substituicao(chrome, codigo_removido, escolha, quantidade)
            #                     codigos_base_ja_tratados.add(codigo_removido)

            #             # 🧾 Trecho final — pula só se já foi tratado
            #             for descricao, dados in mapeamento.items():
            #                 quantidade = obter_quantidade_por_descricao_original(planilha_atualizada, descricao)

            #                 for codigo_base, codigo_gerado in zip(dados['codigo_base'], dados['Codigo_gerado']):
            #                     if codigo_base in codigos_base_ja_tratados:
            #                         print(f"⏩ Pulando '{codigo_base}' (já tratado manualmente)")
            #                         continue

            #                     print(f"🔄 Substituindo → Base: {codigo_base} | Gerado: {codigo_gerado} | Qtd: {quantidade}")
            #                     executar_substituicao(chrome, codigo_base, codigo_gerado, quantidade)
            #             todos_gerados = set()
            #             for gerados in mapa_base_para_gerados.values():
            #                 todos_gerados.update(gerados)

            #             gerados_ja_utilizados = set(escolhas_usuario.values())
            #             restantes = todos_gerados - gerados_ja_utilizados

            #             for codigo_restante in restantes:
            #                 resposta = confirmar_inclusao_manual(codigo_restante)
            #                 if resposta == "sim":
            #                     chrome.get("https://optionbakery.nomus.com.br/optionbakery/Produto.do?metodo=Pesquisar")
            #                     # Aqui você pode chamar a pergunta_maquina_por_vinculo() ou abrir outro input manual
            #                     maquina = pergunta_maquina_por_vinculo("Manual", codigo_restante)
            #                     print(f"🔧 Código '{codigo_restante}' será incluído manualmente na máquina '{maquina}'")
            #                     resultado = []
            #                     mapa_qtd_por_codigo = extrair_mapa_codigo_para_quantidade(log_path)
            #                     print(f"🔢 Quantidade usada para '{codigo_restante}': {quantidade}")
            #                     quantidade = mapa_qtd_por_codigo.get(codigo_restante, "1") # fallback defensivo
            #                     pesquisa_code = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.NAME, "nomePesquisa")))
            #                     pesquisa_code.clear()
            #                     pesquisa_code.send_keys(maquina)
            #                     pesquisa_code.send_keys(Keys.RETURN)

            #                     xpath_codigo_pai = f"//span[normalize-space(text())='{maquina}']"
            #                     span_codigo = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_codigo_pai)))
            #                     # Centraliza na tela e clica
            #                     chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", span_codigo)
            #                     span_codigo.click()
            #                     WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "produtoAtivoLiberado_itemSubMenu_acessarListaMateriais"))).click()
            #                     print(f"🔗 Processando: {codigo_restante} → Quantidade: {quantidade}")
            #                     # Clica no botão de estrutura
                        
            #                     botao_estrutura = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "botao_acessaradicionaritemestrutura")))
            #                     chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_estrutura)
            #                     botao_estrutura.click()
            #                     search_produto = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "nome_produto")))
            #                     time.sleep(1)
            #                     search_produto.send_keys(codigo_restante)
            #                     WebDriverWait(chrome, 10).until(EC.invisibility_of_element_located((By.ID, "ui-id-2")))
            #                     WebDriverWait(chrome, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-menu-item-wrapper")))
            #                     suspensao = chrome.find_elements(By.CLASS_NAME, "ui-menu-item-wrapper")
            #                     for item in suspensao:
            #                         texto = item.text.strip()
            #                         if codigo_restante in texto:
            #                             chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
            #                             item.click()
            #                             print(f"🟢 Item clicado na suspensão: '{texto}'")
            #                             break

            #                     campo_qnt_necess = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "qtdeNecessaria_id")))
            #                     campo_qnt_necess.send_keys(quantidade)
            #                     time.sleep(0.7)
            #                     save_item_lista = WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "botao_salvar")))
            #                     chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_item_lista)
            #                     save_item_lista.click()
            #                     pass  # já está implementado no seu script

            # 🔚 Ao final, pergunta se deseja voltar ao menu
            # if not deseja_voltar_ao_menu():
            #     print("👋 Encerrando o MAMVIZ. Até a próxima!")
            #     break


    def atualizar_planilha_original_por_atualizada(caminho_iam):
        nome_base = os.path.splitext(os.path.basename(caminho_iam))[0]
        pasta_montagem = os.path.join(os.path.dirname(caminho_iam), nome_base)

        caminho_atualizada = os.path.join(pasta_montagem, "planilha_atualizada.xlsx")
        caminho_original = os.path.join(pasta_montagem, "planilha_original.xlsx")

        if not os.path.exists(caminho_atualizada):
            print("❌ Planilha atualizada não encontrada:", caminho_atualizada)
            return

        # (restante do código...)

        try:
            # Substitui planilha original pelo conteúdo da atualizada
            shutil.copyfile(caminho_atualizada, caminho_original)
            print("✅ Planilha original foi atualizada com sucesso!")

            # Atualiza o log de caminho original
            caminho_log = os.path.join(pasta_montagem, "caminho_original.txt")
            with open(caminho_log, "w", encoding="utf-8") as log:
                log.write(caminho_original)
            print(f"📝 Caminho atualizado registrado em: {caminho_log}")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar planilha original: {e}")
            logger_erros.error(f"Falha ao atualizar planilha original: → {str(e)}")

    #CHAMA FUNCAO DIFERENÇA
    atualizar_status("Comparando diferenças entre BOMs...", 0.35)
    identificar_diferencas(planilha_original, planilha_atualizada, root)
    lista_removidos = extrair_itens_removidos(planilha_original, planilha_atualizada)

    lista_adicionados = extrair_itens_adicionados(planilha_original, planilha_atualizada)


    # Configura o log detalhado
    caminho_log = os.path.join(pasta_logs, "engenharia_code.log")
    logging.basicConfig(
        filename=caminho_log,
        level=logging.INFO,
        format='[%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


    # 📝 Cria logger separado para códigos removidos
    logger_removidos = logging.getLogger("RemovidosLogger")
    logger_removidos.setLevel(logging.INFO)
    # Define caminho do novo arquivo de log
    arquivo_removidos_log = os.path.join(pasta_logs, "codigos_removidos.log")
    # Formatação das mensagens
    formato_log = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # Handler que escreve no novo arquivo
    file_handler_removidos = logging.FileHandler(arquivo_removidos_log, encoding="utf-8")
    file_handler_removidos.setFormatter(formato_log)
    # Adiciona handler ao logger
    logger_removidos.addHandler(file_handler_removidos)


    # 📝 Cria logger separado para códigos adicionados
    logger_adicionados = logging.getLogger("AdicionadosLogger")
    logger_adicionados.setLevel(logging.INFO)
    arquivo_adicionados_log = os.path.join(pasta_logs, "codigos_adicionados.log")
    formato_log = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler_adicionados = logging.FileHandler(arquivo_adicionados_log, encoding="utf-8")
    handler_adicionados.setFormatter(formato_log)
    logger_adicionados.addHandler(handler_adicionados)

    # 📝 Logger para mapeamento de clonagem
    logger_mapeamento = logging.getLogger("MapeamentoLogger")
    logger_mapeamento.setLevel(logging.INFO)
    arquivo_mapeamento_log = os.path.join(pasta_logs, "mapeamento_clonagem.log")
    formato_mapeamento = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler_mapeamento = logging.FileHandler(arquivo_mapeamento_log, encoding="utf-8")
    handler_mapeamento.setFormatter(formato_mapeamento)
    logger_mapeamento.addHandler(handler_mapeamento)

    # 📝 Logger para mapeamento por similaridade
    logger_parecidos = logging.getLogger("ParecidosLogger")
    logger_parecidos.setLevel(logging.INFO)
    arquivo_parecidos_log = os.path.join(pasta_logs, "mapeamento_parecidos.log")
    formato_parecidos = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler_parecidos = logging.FileHandler(arquivo_parecidos_log, encoding="utf-8")
    handler_parecidos.setFormatter(formato_parecidos)
    logger_parecidos.addHandler(handler_parecidos)

    # 📝 Logger para conversões TAG 09
    logger_tag_09 = logging.getLogger("Tag09Logger")
    logger_tag_09.setLevel(logging.INFO)
    arquivo_tag_09_log = os.path.join(pasta_logs, "tag_09_conversao.log")
    formato_tag_09 = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler_tag_09 = logging.FileHandler(arquivo_tag_09_log, encoding="utf-8")
    handler_tag_09.setFormatter(formato_tag_09)
    logger_tag_09.addHandler(handler_tag_09)

    # 📝 Logger para erros
    logger_erros = logging.getLogger("ErrosLogger")
    logger_erros.setLevel(logging.ERROR)
    # Caminho do log de erros
    arquivo_erros_log = os.path.join(pasta_logs, "erros_mamviz.log")
    # Formatação com data e hora
    formato_erros = logging.Formatter('[%(asctime)s] ERRO: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # Handler dedicado
    handler_erros = logging.FileHandler(arquivo_erros_log, encoding="utf-8")
    handler_erros.setFormatter(formato_erros)
    # Associar ao logger
    logger_erros.addHandler(handler_erros)




    # ABRINDO CHROME
    # Cria as opções para o Chrome
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.popups": 0
    })
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    # Inicializa o Chrome com as opções
    service = Service(ChromeDriverManager().install())
    chrome = webdriver.Chrome(service=service, options=options)
    chrome.maximize_window()  # maximizar a janela do navegador
    chrome.get("https://optionbakery.nomus.com.br/optionbakery")
    time.sleep(1) # aguardar o carregamento da página
    login()


    df_original = pd.read_excel(planilha_original)
    for descricao_nova in lista_adicionados:
        resultado = obter_codigo_do_item_parecido(descricao_nova, df_original)
        print(f"🔍 '{resultado['novo_item']}' → parecido com '{resultado['mais_parecido']}' (score: {resultado['score']}%) → codigo_base: {resultado['codigo']}")
        mensagem_log = f"🔍 '{resultado['novo_item']}' → parecido com '{resultado['mais_parecido']}' (score: {resultado['score']}%) → codigo_base: {resultado['codigo']}"
        logger_parecidos.info(mensagem_log)
        
        
    itens_com_tag_zero_nove = verificar_tags_em_adicionados_zero_nove(lista_adicionados)
    mapa_codigos, _ = mapear_codigos_parecidos(lista_adicionados, df_original)
    # Gera lista simples com os códigos
    codigos_relacionados_para_clonar = [
        mapa_codigos.get(descricao, {}).get("codigo")
        for descricao in lista_adicionados
    ]
    lista_descricoes_com_tag, mapa_clonagem, relacionamento_tag_por_item_base = criando_novo_produto_com_parecidos(
        chrome, lista_removidos, lista_adicionados, df_original, codigos_relacionados_para_clonar
    )

    # Já extraiu lista_descricoes_com_tag e mapa_clonagem
    codigos_encontrados_tag = extrair_codigo_por_descricao_web_tag(lista_adicionados, lista_descricoes_com_tag)
    codigos_encontrados_normal = extrair_codigo_por_descricao_web_normal(planilha_atualizada, lista_adicionados)
    codigos_encontrados_completos = codigos_encontrados_normal + codigos_encontrados_tag

    codigos_encontrados_normal = extrair_codigo_por_descricao_web_normal(planilha_atualizada, lista_adicionados)
    #Fazendo mapeamento de descrições, para localizar a descrição antes de ser alterada, e usar a descrição original pra pegar a quantidade de cada item tag
    for original, versões_clonadas in mapa_clonagem.items():
        quantidade = obter_quantidade_por_descricao_original(planilha_atualizada, original)

        print(f"\n🔗 Original: '{original}' → Quantidade: {quantidade}")
        for clonada in versões_clonadas:
            print(f"   → Clonada como: '{clonada}'")
    registrar_resultados_finais(
        planilha_path= planilha_atualizada,
        lista_descricoes_clonadas=lista_descricoes_com_tag,
        codigos_encontrados=codigos_encontrados_tag,
        mapa_clonagem=mapa_clonagem,
        relacionamento_tag_por_item_base=relacionamento_tag_por_item_base
    )


    log_path = os.path.join(pasta_logs, "engenharia_code.log")
    resultado= extrair_codigos_e_quantidades_do_log(log_path) 
    codigos_removidos = extrair_codigos_removidos(planilha_original, planilha_atualizada)

    caminho_conversao = os.path.join(pasta_logs, "tag_09_conversao.log")

    mapeamento = extrair_mapeamento_por_descricao(log_path, lista_adicionados, mapa_clonagem, debug=False)


    for descricao, dados in mapeamento.items():
        print(f"\n📌 Descrição Original: {descricao}")
        
        origem_gerado = "Descrição Clonada" if dados.get("descricao_clonada") else "Descrição Original"
        print(f"  → Código Gerado(s) [{origem_gerado}]: {', '.join(dados['Codigo_gerado'])}")
        print(f"  → Código Base(s):   {', '.join(dados['codigo_base'])}")


    for descricao, dados in mapeamento.items():
        for codigo_base, codigo_gerado in zip(dados['codigo_base'], dados['Codigo_gerado']):
            logger_mapeamento.info(f"→ Codigo Base: {codigo_base} → Codigo Gerado: {codigo_gerado}")
        
                
    # 🧭 Iniciar o programa principal do MAMVIZ
    executar_fluxo_mamviz()
        


    atualizar_somente_descricoes(planilha_atualizada, lista_adicionados, lista_descricoes_com_tag, relacionamento_tag_por_item_base)
    log_path = os.path.join(pasta_logs, "engenharia_code.log")
    atualizar_codigos_via_log(planilha_atualizada, log_path)
    atualizar_planilha_original_por_atualizada(caminho_iam)


    nome_arquivo = os.path.basename(caminho_iam)
    atualizar_status("Enviando mensagem...", 0.95)
    # Mensagem que você quer enviar
    message = f"*MAMVIZ:*\n✅ Olá! {nome_arquivo} foi finalizado com sucesso."
    # Montar URL de requisição
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={message}&apikey={api_key}"
    # Enviar mensagem
    response = requests.get(url)
    # Mostrar resultado
    print(response.status_code)
    print(response.text)
    atualizar_status("Processo finalizado!", 1.0)
    #ANTES DE TRANSFORMA EM EXE, TROQUE O TRECHO ABAIXO:
    if confirmar_salvamento_outra_maquina():
        os.system(f'python "{sys.argv[0]}"')
        sys.exit()
        
        
    # #PARA:

    # if confirmar_salvamento_outra_maquina(): 
    #     subprocess.Popen([sys.executable])
    #     sys.exit()



    # #PARA PRODUTO NORMAL:
    # Solicitar finalidade

# Cria a janela
criar_janela_progresso()

# Agende a execução do fluxo na thread principal
janela_principal.after(100, fluxo)

# Mantém a interface viva
janela_principal.mainloop()

