from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tkinter as tk
from tkinter import simpledialog
import pandas as pd
from tkinter import messagebox
modalidade_escolhida = None
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service



# LENDO O ARQUIVO MERCÚRIO
mercurio = 'mercurio.xlsx'
df = pd.read_excel(mercurio, usecols=[0,1,2])
df.dropna(how='all', inplace=True)  # Remove linhas onde todas as colunas são NaN

# MENSAGEM DE CONFIRMAÇÃO DE LEITURA DO MERCÚRIO
root = tk.Tk()
root.withdraw()  # Oculta a janela principal
messagebox.showinfo("Ultron", "Dados da humaninade... digo, do orçamento foram analisados. Pressione OK para continuar.", parent=root)
print(df)
qmercurio = len(df)
print(qmercurio)




# ABRINDO CHROME
# Cria as opções para o Chrome
options = Options()
options.add_argument("--incognito")  # ativa o modo anônimo
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
service = Service(ChromeDriverManager().install())
chrome = webdriver.Chrome(service=service, options=options)


chrome.maximize_window()  # maximizar a janela do navegador
chrome.get("https://optionbakery.nomus.com.br/optionbakery")
time.sleep(1) # aguardar o carregamento da página
wait1 = WebDriverWait(chrome, 120)

# Criar janela e solicitar o usuário
root = tk.Tk()
root.withdraw()  # Oculta a janela principal
wait = WebDriverWait(chrome, 5)
while True:
    usuario = simpledialog.askstring("Login", "Digite seu usuário:")
    senha = simpledialog.askstring("Senha", "Digite sua senha, ninguém saberá hahahaha:", show="*")
    print(f"Ultron: Tentando autenticar {usuario}...")

    campo_login = wait.until(EC.presence_of_element_located((By.ID, "campologin")))
    campo_login.clear()
    campo_login.send_keys(usuario)
    chrome.find_element(By.NAME, "senha").clear()
    chrome.find_element(By.NAME, "senha").send_keys(senha)
    chrome.find_element(By.NAME, "metodo").click()
    time.sleep(2)

    # Verifica se há mensagem de erro
    try:
        erro_login = chrome.find_element(By.CLASS_NAME, "mensagem-erro-login")
        print("Ultron: Erro detectado na autenticação. Tentando novamente...")
    except:
        print("Ultron: Identificação válida. Avançando no protocolo.")
        break



#ACESSANDO PEDIDOS DE COTAÇÃO
chrome.get("https://optionbakery.nomus.com.br/optionbakery/CotacaoCompra.do?metodo=pesquisarPaginado")
af_str = simpledialog.askstring("Pesquisar Pedido de Cotação (PC)", "Digite o número do PC:")
PC = int(af_str)
print(PC)
chrome.find_element(By.NAME, "nomePesquisa").send_keys(PC)  # inserir o número do PC
chrome.find_element(By.ID, "botao_pesquisarpaginado").click()
time.sleep(2)  # aguardar o carregamento dos resultados da pesquisa




#ABRINDO O PEDIDO DE COTAÇÃO


resposta = messagebox.askyesno("Ultron", "Humano, o pedido está liberado?")
IDPC = "3_" + str(PC - 78)   # calcular o ID do PC
print(IDPC)
clicarPC = chrome.find_element(By.ID, IDPC) # encontrando o pedido de cotação
libera = chrome.find_element(By.ID, "submenuCotacao_itemSubMenu_liberarColetaPrecosCotacaoCompra")  # Encontrando liberar coleta de preço
clicarPC.click()  # clicar no PC desejado
time.sleep(1)

if resposta:
    print("Ultron: Veja que houve uma alteração...")
    try: 

        clicarPC.click()
        registro = chrome.find_element(By.ID, "submenuCotacaoColetaPrecos_itemSubMenu_registrarColetaPrecosCotacaoCompraCadastro") # Encontrando registrar preços
        time.sleep(1)
        registro.click() #clicando registrar preços

    except Exception as e:
        print("Ultron: Não encontrei o botão de registro. Tentando alternativa...")
        clicarPC.click()
        registro = chrome.find_element(By.ID, "submenuCotacaoColetaPrecosComColeta_itemSubMenu_registrarColetaPrecosCotacaoCompraCadastro") # Encontrando registrar preços
        time.sleep(1)
        registro.click() #clicando registrar preços


else:
    print("Ultron: Finalmente um retorno desse reles fornecedor!")
    
    libera = chrome.find_element(By.ID, "submenuCotacao_itemSubMenu_liberarColetaPrecosCotacaoCompra")  # Encontrando liberar coleta de preço
    libera.click() #Clicando liberar coleta de preço
    time.sleep(2)
    clicarPC = WebDriverWait(chrome, 10).until( EC.element_to_be_clickable((By.ID, IDPC)))
    chrome.execute_script("arguments[0].scrollIntoView();", clicarPC)
    clicarPC.click()
    registro = chrome.find_element(By.ID, "submenuCotacaoColetaPrecos_itemSubMenu_registrarColetaPrecosCotacaoCompraCadastro") # Encontrando registrar preços
    time.sleep(0.5)
    registro.click() #clicando registrar preços




#ESCOLHENDO FORNECEDOR
forne = simpledialog.askfloat("Ultron", "Confirme se o fornecedor é o primeiro, segundo, etc... Digite somente o número:") # Perguntando ao comprador qual fornecedor
idfornecedor = "ui-id-" + str(int(forne + 1)) #definindo id do fornecedor
time.sleep(1)
fornecedor = chrome.find_element(By.ID, idfornecedor) # encontrando fornecedor definido
fornecedor.click() #Clicando no fornecedor


check = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'atendeAosItens')]")
visiveis = [el for el in check if el.is_displayed() and el.is_enabled()]

quantidade_checkboxes = len(visiveis)
qmercurio = len(df)  # Quantidade de linhas da planilha Mercúrio

print(f"Ultron: {quantidade_checkboxes} checkbox(es) visível(is) encontradas.")
time.sleep(1)
print(f"Ultron: {qmercurio} item(ns) identificado(s) no arquivo Mercúrio.")



if quantidade_checkboxes == qmercurio:
    print("Ultron: Quantidade compatível. Preparando marcação estratégica...")
    for el in visiveis:
        if not el.is_selected():
            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(el))
            el.click()
            #valor = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'valoresUnitariosProdutos')]")
            #alorvisiv = [el for el in valor if el.is_displayed() and el.is_enabled()]
            #print(f"Ultron: {len(valorvisiv)} campo(s) de valor visível(is) detectado(s).")

            print(f"→ Checkbox marcada: {el.get_attribute('id')}")
else:
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    messagebox.showinfo("Ultron", "Humano, a quantidade de itens presentes nesse pedido é diferente da quantidade de itens no orçamento. " \
    "Verifique se faltou algum item a ser cotado, ou se esqueceu de excluir um item do pedido. Estou abortando a missão para evitar um caos maior.", parent=root)
    exit()




campos_valor = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'valoresUnitariosProdutos')]")
valorvisiv = [el for el in campos_valor if el.is_displayed() and el.is_enabled()]


for campo, linha in zip(valorvisiv, df.itertuples(index=False)):
    valor = linha[2]  # Pega o terceiro valor da planilha (coluna de preço)

    try:
        chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
        WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(campo))
        campo.clear()
        # Converte o valor para string e separa a parte decimal
        valor_str = str(valor).replace(",", ".")  # Garante ponto como separador decimal
        partes = valor_str.split(".")

        if len(partes) == 2:
            casas_decimais = len(partes[1])
        else:
            casas_decimais = 0

        # Define o número de casas com base na lógica inversa que você quer
        if casas_decimais == 3:
            casas = 6
        elif casas_decimais == 5:
            casas = 6
        elif casas_decimais == 5:
            casas = 6
        else:
            casas = 6  # padrão
        campo.send_keys(f"{valor:.{casas}f}")


        print(f"Ultron: Campo {campo.get_attribute('id')} preenchido com R${valor}")
    except Exception as e:
        print(f"Ultron: Falha ao preencher campo {campo.get_attribute('id')}. Erro: {e}")




prazop = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'prazoEntregaPadrao')]") #localizando campos prazo padrão
prazopadrao = [el for el in prazop if el.is_displayed() and el.is_enabled()] #filtrando 
prazo = int(simpledialog.askfloat("Ultron", "Qual o prazo?"))  #definindo prazo
prazopadrao[0].clear() #limpando campo
prazopadrao[0].send_keys(prazo) #digitando o prazo
locatualizarprazo = chrome.find_elements(By.CSS_SELECTOR, ".fa.fa-refresh.iconeAzul[aria-hidden='true']") #localizando atualizar prazo
clicaveis = [el for el in locatualizarprazo if el.is_displayed() and el.is_enabled()] #Filtrando somente o atualizar prazo presente na pagina
chrome.execute_script("arguments[0].click();", clicaveis[0])
time.sleep(1)





# INCLUINDO O TIPO DE FRETE

janela_modalidade = tk.Tk()
janela_modalidade.title("Ultron")
largura, altura = 400, 150
x = (janela_modalidade.winfo_screenwidth() // 2) - (largura // 2)
y = (janela_modalidade.winfo_screenheight() // 2) - (altura // 2)
janela_modalidade.geometry(f"{largura}x{altura}+{x}+{y}")

def set_modalidade(modalidade):
    global modalidade_escolhida
    modalidade_escolhida = modalidade
    print(f"Ultron: Modalidade escolhida → {modalidade}")
    janela_modalidade.quit()
    janela_modalidade.destroy()

tk.Label(janela_modalidade, text="Qual modalidade do frete?").pack(pady=10)
tk.Button(janela_modalidade, text="FOB", command=lambda: set_modalidade("FOB")).pack(fill='x')
tk.Button(janela_modalidade, text="CIF", command=lambda: set_modalidade("CIF")).pack(fill='x')
tk.Button(janela_modalidade, text="Incluir valor de frete.", command=lambda: set_modalidade("Incluir valor de frete.")).pack(fill='x')
janela_modalidade.mainloop()
locmodali = chrome.find_elements(By.XPATH, "//*[starts-with(@name, 'modalidadesTransporte')]")
filmodali = [el for el in locmodali if el.is_displayed() and el.is_enabled()]
fil = len(filmodali)
if filmodali:
    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", filmodali[0])
    time.sleep(0.5)

    if modalidade_escolhida == "FOB":
        filmodali[0].send_keys("1")
        print("Ultron: Modalidade FOB selecionada.")
    elif modalidade_escolhida == "CIF":
        filmodali[0].send_keys("0")
        print("Ultron: Modalidade CIF selecionada.")
    elif modalidade_escolhida == "Incluir valor de frete.":
        locvalfrete = chrome.find_elements(By.XPATH, "//*[starts-with(@name, 'valoresTotalFrete')]")
        filvalfrete = [el for el in locvalfrete if el.is_displayed()]
        quesvalorfrete = simpledialog.askstring("Ultron", "Qual o valor do frete?")
        filvalfrete[0].send_keys(quesvalorfrete)
else:
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    messagebox.showinfo("Ultron", "Humano, não identifiquei uma modalidade escolhida. Estou abortando a missão para evitar um caos maior.", parent=root)
    exit()



#RODAPÉ PEDIDO COTAÇÃO

botaovaltot = chrome.find_elements(By.XPATH, "//*[@title='Valores totais']")
filbotaovaltot = [el for el in botaovaltot if el.is_displayed() and el.is_enabled()]

if filbotaovaltot:
    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", filbotaovaltot[0])
    filbotaovaltot[0].click()

# Localiza botão "Calcular valores totais"
locbtcalcvt = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'botao_calcular_valores_totais_')]")
botaocalcvt = [el for el in locbtcalcvt if el.is_displayed() and el.is_enabled()]

if botaocalcvt:
    WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(botaocalcvt[0]))
    botaocalcvt[0].click()

# Localiza aba "Condições de pagamento"
btcpagamento = chrome.find_elements(By.XPATH, "//*[@title='Condições de pagamento']")
filbtcpagamento = [el for el in btcpagamento if el.is_displayed() and el.is_enabled()]

if filbtcpagamento:
    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", filbtcpagamento[0])
    filbtcpagamento[0].click()


#condição pagamento pix
time.sleep(2)
loccondpg = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'idsCondicaoPagamento')]")  
filcondpg = [el for el in loccondpg if el.is_displayed() and el.is_enabled()]
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", filcondpg[0])
filcondpg[0].send_keys("pi")
#forma pagamento pix
locformpg = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'idsFormaPagamento')]") 
filfomrpg = [el for el in locformpg if el.is_displayed() and el.is_enabled()]
filfomrpg[0].send_keys("pi")
#prazo da parcela
locgerpar = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'regrasGerarParcelas')]")  
filgerpar = [el for el in locgerpar if el.is_displayed() and el.is_enabled()]
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", filgerpar[0])
filgerpar[0].clear()
filgerpar[0].send_keys("1")
#gerando parcela
locbtgerpar = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'botao_gerarParcelas_')]")  
filbtgerpar = [el for el in locbtgerpar if el.is_displayed() and el.is_enabled()]
filbtgerpar[0].click()
time.sleep(1)
#forma pagamento na parcela
WebDriverWait(chrome, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[starts-with(@id, 'id_idsFormasPagamentoParcelas_')]")))
locpformpg = chrome.find_elements(By.XPATH, "//*[starts-with(@id, 'id_idsFormasPagamentoParcelas_')]")
filpformpg = [el for el in locpformpg if el.is_displayed() and el.is_enabled()]
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", filpformpg[0])
filpformpg[0].send_keys("pi")


#SALVANDO PEDIDO COTAÇÃO
btsavepc = chrome.find_element(By.ID, "botao_salvar")  
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", btsavepc)
btsavepc.click()


#LIBERANDO PARA DECISÃO DE COMPRA
IDPC = "3_" + str(PC - 78)
WebDriverWait(chrome, 20).until(EC.visibility_of_element_located((By.ID, IDPC)))
clicarPC = chrome.find_element(By.ID, IDPC)
clicarPC.click()
WebDriverWait(chrome, 20).until(EC.visibility_of_element_located((By.ID, "submenuCotacaoColetaPrecosComColeta_itemSubMenu_liberarDecisaoCompraCotacaoCompra")))
btlibera = chrome.find_element(By.ID, "submenuCotacaoColetaPrecosComColeta_itemSubMenu_liberarDecisaoCompraCotacaoCompra")
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", btlibera)
btlibera.click()

#TOMANDO DECISÃO DE COMPRA
IDPC = "3_" + str(PC - 78)
WebDriverWait(chrome, 20).until(EC.visibility_of_element_located((By.ID, IDPC)))
clicarPC = chrome.find_element(By.ID, IDPC)
clicarPC.click()
WebDriverWait(chrome, 10).until(EC.visibility_of_element_located((By.ID, "submenuCotacaoDecisaoCompra_itemSubMenu_tomarDecisaoCompraCadastro")))
bttomada = chrome.find_element(By.ID, "submenuCotacaoDecisaoCompra_itemSubMenu_tomarDecisaoCompraCadastro")
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", bttomada)
bttomada.click()


#SALVANDO DECISÃO DE COMPRA
WebDriverWait(chrome, 10).until(EC.visibility_of_element_located((By.ID, "botao_gerarpedido")))
savedecisao = chrome.find_element(By.ID, "botao_gerarpedido")
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", savedecisao)
savedecisao.click()

#CONFIRMANDO O NÚMERO DA AF
chrome.get("https://optionbakery.nomus.com.br/optionbakery/PedidoCompra.do?metodo=pesquisar") 
af_str = simpledialog.askstring("Ultron", "Confirme o número da AF para não haver erro:")
AF = int(af_str)
chrome.find_element("name", "nomePesquisa").send_keys(AF)  # inserir o número da AF
chrome.find_element("id", "botao_pesquisar").click()
time.sleep(2)  # aguardar o carregamento dos resultados da pesquisa
ID = "3_" + str(AF - 69)   # calcular o ID da AF
chrome.find_element("id", ID).click()  # clicar na AF desejada
time.sleep(0.5)
chrome.find_element("id", "pedidoCompra_itemSubMenu_editarPedidoCompra").click()  # clicar editar AF

#EDITANDO CABEÇALHO AF
tipopedido = chrome.find_element(By.ID, "idTipoPedidoCompra")
tipopedido.send_keys("p")
setorentrada = chrome.find_element(By.ID, "id_idSetorEntrada")
setorentrada.send_keys("a")
condpagamento =  chrome.find_element(By.NAME, "condicaoPagamento")
condpagamento.clear()
filobs = chrome.find_element(By.NAME, "observacaoPedido")
via = simpledialog.askstring("Ultron", "Orçamento foi feito através de que? Email ou Whatsapp?")
pagamento = simpledialog.askstring("Ultron", "Digite a chave pix ou forma de pagamento:")
aplicacao = simpledialog.askstring("Ultron", "Digite a aplicação:")
filobs.send_keys(f"Orçamento via {via}", Keys.ENTER, f"{pagamento}", Keys.ENTER, Keys.ENTER, f"{aplicacao}")


#JARVIS

jarvis = messagebox.askyesno("Ultron", "Jarvis agora é meu servo. Deseja executá-lo?")

if jarvis:
    codes = ["Aguardando liberação", "Liberado", "Atendido parcialmente", "Atendido com corte"]
    codes_set = set(codes)
    xpath = " | ".join([f"//span[normalize-space(text())='{code}']" for code in codes_set])
    spans = chrome.find_elements(By.XPATH, xpath)
    aliquota = simpledialog.askstring("Ultron", "Defina a alíquota de TODOS os itens:")

    falhas = []

    for index in range(len(spans)):
        try:
            # Recarrega os elementos atualizados

            xpath = " | ".join([f"//span[normalize-space(text())='{code}']" for code in codes_set])
            spans = chrome.find_elements(By.XPATH, xpath)
            item = spans[index]


            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(item)).click()

            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "pedidoCompraCriarEditar_itemSubMenu_selecionarItemPedidoCompra"))).click()

            # Acessa aba de tributos
            WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "ui-id-9")))
            tributos = chrome.find_element(By.ID, "ui-id-9")
            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", tributos)
            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(tributos)).click()

            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "id_idSituacaoTributariaIPI"))).send_keys("49")
            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "id_idFormulaTributacaoIPI"))).send_keys("ipi")
            WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "id_aliquotaIPI"))).send_keys(aliquota)
            saveitem = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "botao_salvaritempedido")))
            chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", saveitem)
            saveitem.click()
            
            

        except Exception as e:
            print(f"❌ Erro no item {index + 1}: {e}")
            falhas.append(index)

    # Reprocessamento de falhas
    tentativas = 1
    max_tentativas = 3

    while falhas and tentativas <= max_tentativas:
        print(f"🔁 Tentativa {tentativas}: Reprocessando {len(falhas)} item(ns) com falha...")
        novas_falhas = []

        for index in falhas:
            try:
                xpath = " | ".join([f"//span[normalize-space(text())='{code}']" for code in codes_set])
                spans = chrome.find_elements(By.XPATH, xpath)

                if index >= len(spans):
                    print(f"⚠️ Item {index + 1} não encontrado na nova lista. Pulando...")
                    continue

                item = spans[index]
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(item)).click()

                WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "pedidoCompraCriarEditar_itemSubMenu_selecionarItemPedidoCompra"))).click()

                # Acessa aba de tributos
                WebDriverWait(chrome, 10).until(EC.presence_of_element_located((By.ID, "ui-id-9")))
                tributos = chrome.find_element(By.ID, "ui-id-9")
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", tributos)
                WebDriverWait(chrome, 10).until(EC.element_to_be_clickable(tributos)).click()

                WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "id_idSituacaoTributariaIPI"))).send_keys("49")
                WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "id_idFormulaTributacaoIPI"))).send_keys("ipi")
                WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "id_aliquotaIPI"))).send_keys(aliquota)
                saveitem = WebDriverWait(chrome, 10).until(EC.element_to_be_clickable((By.ID, "botao_salvaritempedido")))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", saveitem)
                saveitem.click()


                print(f"✔ Item {index + 1} salvo com sucesso na tentativa {tentativas}.")

            except Exception as e:
                print(f"⚠️ Tentativa {tentativas} falhou no item {index + 1}: {e}")
                novas_falhas.append(index)

        falhas = novas_falhas
        tentativas += 1

    if falhas:
        print(f"❌ Após {max_tentativas} tentativas, os seguintes itens ainda falharam: {falhas}")
    else:
        print("✅ Todos os itens foram processados com sucesso.")

    vtotais = chrome.find_element(By.ID, "ui-id-12")  # localizar o elemento de valores totais
    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", vtotais)  # rolar para o elemento
    vtotais.click()  # clicar em valores totais
    cvtotal = wait1.until(EC.element_to_be_clickable((By.ID, "botao_calcular_valores_totais")))  # localizar o botão calcular valores totais
    cvtotal.click()  # clicar no botão calcular valores totais


    #CARREGANDO CONDIÇÕES DE PAGAMENTO
    cpagamento = chrome.find_element(By.ID, "ui-id-15") # localizar o elemento de condições de pagamento
    chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", cpagamento) #rolar para o elemento
    cpagamento.click()  # clicar em condições de pagamento
    campo_parcela = chrome.find_element(By.ID, "id_regraGerarParcelas")
    campo_parcela.clear()
    campo_parcela.send_keys("1")
    gerarp = chrome.find_element(By.ID, "botao_gerar_parcelas") #encontar o botão de gerar parcelas
    gerarp.click()  # clicar no botão de gerar parcelas
    time.sleep(1)
    pag = chrome.find_element(By.ID, "id_idsFormasPagamentoParcelas_0")
    pag.send_keys("pi")
    print("Jarvis foi executado.")

else: 
    print("Ultron: Jarvis não será executado. Pulando para o salvamento da AF.")




saveaf = chrome.find_element(By.ID, "botao_salvar") # localizar o botão de salvar AF
chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", saveaf) # rolar para o botão de salvar AF
time.sleep(0.5)
saveaf.click()  # clicar no botão de salvar AF










time.sleep(30)
