from fastapi import FastAPI, Depends, HTTPException, Body, status, Query
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import bcrypt
import io
import random
import string
from typing import Any, Dict, Optional
import smtplib
import requests, re
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from email.message import EmailMessage
from datetime import datetime, timedelta
import jwt
from db import SessionLocal
from models import Cliente, PecasClientes, Usuarios, Permissoes
import xml.etree.ElementTree as ET
templates = Jinja2Templates(directory="templates")
# -------------------- CONFIG --------------------
app = FastAPI(title="API de Clientes", version="3.5")

SECRET_KEY = os.environ.get("SECRET_KEY", "SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 150

bearer_scheme = HTTPBearer()
tokens_temp = {}  # {documento_numeros: {"token": str, "expira": datetime}}

# -------------------- BANCO --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- UTILITÁRIOS --------------------
def somente_numeros(valor: str) -> str:
    return ''.join(filter(str.isdigit, valor or ""))

def gerar_token(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def enviar_email(destinatario: str, assunto: str, corpo: str) -> bool:
    SMTP_HOST = "smtps.uhserver.com"
    SMTP_PORT = 465
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASS = os.environ.get("SMTP_PASS")

    if not SMTP_USER or not SMTP_PASS:
        raise HTTPException(status_code=500, detail="SMTP_USER ou SMTP_PASS não configurados")

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content(corpo, charset="utf-8")

    try:
        # Conexão segura via SSL
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar email: {e}")


# -------------------- AUTENTICAÇÃO JWT --------------------
def criar_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def autenticar_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    return verificar_token(token)

# -------------------- ROTAS --------------------
@app.post("/login")
def login_api(documento: str = Body(...), senha: str = Body(...), db: Session = Depends(get_db)):
    documento_numeros = somente_numeros(documento)
    usuario = db.query(Usuarios).filter(
        func.regexp_replace(Usuarios.documento, r'\D', '', 'g') == documento_numeros
    ).first()
    
    # Verifica se usuário existe e senha confere
    if not usuario or not bcrypt.checkpw(senha.encode("utf-8"), usuario.senha.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Documento ou senha incorretos")

    # 🔥 Verifica se o status é ativo
    if usuario.status != "ativo":
        raise HTTPException(status_code=403, detail="Usuário não está ativo")

    # Gera token normalmente
    token = criar_token(usuario.documento)
    return {
        "access_token": token,
        "token_type": "bearer",
        "nome": usuario.nome,
        "grupo": usuario.grupo,
        "status": usuario.status
    }
@app.get("/")
def home(user: str = Depends(autenticar_token)):
    return {"status": "API está funcionando!", "usuario": user}

# -------- CLIENTES --------
@app.get("/clientes")
def listar_clientes(db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    return db.query(Cliente).all()

@app.get("/clientes/{cliente_id}/pecas")
def listar_pecas_cliente(cliente_id: int, db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente.pecas

@app.post("/clientes/{cliente_id}/pecas")
def atualizar_pecas_cliente(cliente_id: int, pecas: list[dict] = Body(...), db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    for p in pecas:
        peca_existente = db.query(PecasClientes).filter(
            PecasClientes.id == p.get("id"),
            PecasClientes.cliente_id == cliente_id
        ).first()
        
        if peca_existente:
            peca_existente.ultima_compra = (
                datetime.fromisoformat(p["ultima_compra"]).date() if p.get("ultima_compra") else None
            )
        else:
            nova_peca = PecasClientes(
                peca=p.get("peca", "Sem nome"),
                cliente_id=cliente_id,
                ultima_compra=(datetime.fromisoformat(p["ultima_compra"]).date() if p.get("ultima_compra") else None)
            )
            db.add(nova_peca)
    
    db.commit()
    return {"success": True, "message": "Peças atualizadas ou criadas com sucesso"}

@app.get("/meu-cliente/{documento}")
def buscar_cliente_por_documento(documento: str, db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    documento_numeros = somente_numeros(documento)
    cliente = db.query(Cliente).filter(
        func.regexp_replace(Cliente.cnpj, r'\D', '', 'g') == documento_numeros
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@app.put("/clientes/{cliente_id}")
def atualizar_cliente(cliente_id: int, dados: dict = Body(...), db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    for campo, valor in dados.items():
        if hasattr(cliente, campo):
            setattr(cliente, campo, valor)

    db.commit()
    db.refresh(cliente)
    return cliente

# -------- USUÁRIOS / PERMISSÕES --------
@app.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    return db.query(Usuarios).all()

@app.get("/permissoes/{grupo}")
def listar_permissoes(grupo: str, db: Session = Depends(get_db), user: str = Depends(autenticar_token)):
    permissoes = db.query(Permissoes).filter(Permissoes.grupo == grupo).all()
    if not permissoes:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    return permissoes

# -------- SENHA --------
@app.post("/esqueceu-senha")
def solicitar_redefinicao(documento: str = Body(...), db: Session = Depends(get_db)):
    documento_numeros = somente_numeros(documento)
    usuario = db.query(Usuarios).filter(
        func.regexp_replace(Usuarios.documento, r'\D', '', 'g') == documento_numeros
    ).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não cadastrado")

    token = gerar_token()
    tokens_temp[documento_numeros] = {"token": token, "expira": datetime.utcnow() + timedelta(minutes=15)}

    if usuario.email:
        enviar_email(usuario.email, "Redefinição de senha", f"Seu código de verificação é: {token[-6:]}")

    return {"success": True, "message": "Token enviado"}

@app.post("/validar-token")
def validar_token(documento: str = Body(...), token: str = Body(...)):
    documento_numeros = somente_numeros(documento)
    registro = tokens_temp.get(documento_numeros)

    if not registro:
        raise HTTPException(status_code=400, detail="Token não encontrado ou expirado")

    if registro["expira"] < datetime.utcnow():
        del tokens_temp[documento_numeros]
        raise HTTPException(status_code=400, detail="Token expirado")

    if token != registro["token"][-6:]:
        raise HTTPException(status_code=400, detail="Token inválido")

    return {"success": True, "message": "Token válido"}

@app.post("/resetar-senha")
def resetar_senha(documento: str = Body(...), token: str = Body(...), nova_senha: str = Body(...), db: Session = Depends(get_db)):
    documento_numeros = somente_numeros(documento)
    registro = tokens_temp.get(documento_numeros)

    if not registro or registro["expira"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    if token != registro["token"][-6:]:
        raise HTTPException(status_code=400, detail="Token inválido")

    usuario = db.query(Usuarios).filter(
        func.regexp_replace(Usuarios.documento, r'\D', '', 'g') == documento_numeros
    ).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.senha = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.commit()
    del tokens_temp[documento_numeros]

    return {"success": True, "message": "Senha atualizada"}

# -------- ORÇAMENTO --------
@app.post("/solicitar-orcamento")
def solicitar_orcamento(dados: dict = Body(...), user: str = Depends(autenticar_token)):
    corpo = f"Orçamento solicitado por {dados.get('cliente', 'Sem nome')}\n"
    corpo += f"Documento: {dados.get('documento', 'Não informado')}\n\n"
    corpo += "Peças:\n"
    for p in dados.get("pecas", []):
        corpo += f"- {p.get('peca')} (código: {p.get('codigo')})\n"

    enviar_email("comercial@optionbakery.com", "Solicitação de Orçamento", corpo)
    return {"success": True, "message": "Orçamento enviado"}

# -------- NOMUS --------
def formatar_cnpj(cnpj: str) -> str:
    """Formata um CNPJ numérico para o padrão 00.000.000/0000-00"""
    cnpj = re.sub(r"\D", "", cnpj)  # garante que só números fiquem
    if len(cnpj) != 14:
        raise ValueError("CNPJ inválido")
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


@app.get("/nomus/notas-fiscais/saida")
def listar_notas_fiscais_saida(pagina: int = 1, user: dict = Depends(autenticar_token)):
    NOMUS_API_URL = os.environ.get("NOMUS_API_URL")
    NOMUS_API_AUTH = os.environ.get("NOMUS_API_AUTH")

    if not NOMUS_API_URL or not NOMUS_API_AUTH:
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API Nomus não configuradas")

    headers = {
        "Authorization": f"Basic {NOMUS_API_AUTH}",
        "Accept": "application/json"
    }

    url = f"{NOMUS_API_URL}/documentosEstoque?query=tipoDocumentoEstoque==DocumentoSaida&pagina={pagina}"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()




@app.get("/nomus/notas-fiscais/cliente")
def listar_notas_fiscais_cliente(
    pagina: int = 1,
    cnpj_cpf: Optional[str] = Query(None, description="CNPJ/CPF do cliente"),
    user: dict = Depends(autenticar_token)
):
    """
    Lista notas fiscais do Nomus de um cliente específico.
    Se cnpj_cpf for fornecido, usa ele; caso contrário, usa o sub do token.
    """
    NOMUS_API_URL = os.environ.get("NOMUS_API_URL")
    NOMUS_API_AUTH = os.environ.get("NOMUS_API_AUTH")

    if not NOMUS_API_URL or not NOMUS_API_AUTH:
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API Nomus não configuradas")
    
    # Usar cnpj_cpf passado via query ou sub do token
    cnpj_raw = cnpj_cpf if cnpj_cpf else user.get("sub")
    
    try:
        cnpj_formatado = formatar_cnpj(cnpj_raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="CNPJ/CPF inválido")

    headers = {
        "Authorization": f"Basic {NOMUS_API_AUTH}",
        "Accept": "application/json"
    }

    url = f"{NOMUS_API_URL}/documentosEstoque?query=pessoaCNPJ==\"{cnpj_formatado}\"&pagina={pagina}"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"HTTP error: {response.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro de conexão: {str(e)}"
        )


@app.get("/nomus/nf/{idNFE}")
def buscar_nf_nomus(idNFE: int, user: str = Depends(autenticar_token)):
    NOMUS_API_URL = os.environ.get("NOMUS_API_URL")
    NOMUS_API_AUTH = os.environ.get("NOMUS_API_AUTH")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {NOMUS_API_AUTH}"
    }

    response = requests.get(f"{NOMUS_API_URL}/nfes/{idNFE}", headers=headers, timeout=30)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Erro ao consultar Nomus")

    data = response.json()
    numero = data.get("numero")
    xml_str = data.get("xml")

    if not xml_str:
        raise HTTPException(status_code=404, detail="XML da NF-e não encontrado")

    try:
        root = ET.fromstring(xml_str)
        vnf_elem = root.find(".//{http://www.portalfiscal.inf.br/nfe}vNF")
        vnf = vnf_elem.text if vnf_elem is not None else None
    except ET.ParseError:
        raise HTTPException(status_code=500, detail="Erro ao interpretar o XML")

    return {"numero": numero, "vNF": vnf}

@app.get("/notas-fiscais/danfe/{id}")
def baixar_danfe(id: int, user: str = Depends(autenticar_token)):
    NOMUS_API_URL = os.environ.get("NOMUS_API_URL")
    NOMUS_API_AUTH = os.environ.get("NOMUS_API_AUTH")

    url = f"{NOMUS_API_URL}/nfes/danfe/{id}"
    headers = {"Authorization": f"Basic {NOMUS_API_AUTH}", "Accept": "application/json"}

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "arquivo" not in data:
        raise HTTPException(status_code=404, detail="PDF do DANFE não encontrado")
    return JSONResponse(content={"arquivo": data["arquivo"]})


# -------- OMIE --------
@app.get("/omie/nf/saida", response_model=Dict[str, Any])
def listar_notas_saida(
    pagina: int = 1,
    registros: int = 50,
    cnpj_cpf: Optional[str] = Query(None, description="Filtrar apenas NF do CNPJ/CPF do cliente"),
    user: str = Depends(autenticar_token)  # Dependência do token
):
    """
    Lista NFs de saída do Omie. Opcionalmente filtra por CNPJ/CPF do cliente.
    """
    OMIE_URL = "https://app.omie.com.br/api/v1/produtos/nfconsultar/"
    APP_KEY = os.getenv("OMIE_API_APP_KEY", "OMIE_API_APP_KEY")
    APP_SECRET = os.getenv("OMIE_API_SECRET_KEY", "OMIE_API_SECRET_KEY")

    payload = {
        "call": "ListarNF",
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "param": [{
            "pagina": pagina,
            "registros_por_pagina": registros,
            "apenas_importado_api": "N",
            "ordenar_por": "DATA_EMISSAO",
            "ordem_decrescente": "S",
            "tpNF": "1"  # Apenas notas de saída
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(OMIE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # 🔎 Filtrar pelo CNPJ/CPF se fornecido
        if cnpj_cpf and "nfCadastro" in data:
            doc_limpo = re.sub(r'\D', '', cnpj_cpf)
            data["nfCadastro"] = [
                nf for nf in data["nfCadastro"]
                if re.sub(r'\D', '', nf.get("nfDestInt", {}).get("cnpj_cpf", "")) == doc_limpo
            ]

        return data

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"HTTP error: {response.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro de conexão: {str(e)}"
        )

@app.get("/omie/nf/danfe/{nCodNF}")
def baixar_pdf_omie(nCodNF: int, user: str = Depends(autenticar_token)):
    import requests, os

    OMIE_URL = "https://app.omie.com.br/api/v1/produtos/notafiscalutil/"
    APP_KEY = os.getenv("OMIE_API_APP_KEY", "OMIE_API_APP_KEY")
    APP_SECRET = os.getenv("OMIE_API_SECRET_KEY", "OMIE_API_SECRET_KEY")

    payload = {
        "call": "GetUrlDanfe",
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "param": [{"nCodNF": nCodNF, "cCodNFInt": ""}]
    }

    response = requests.post(OMIE_URL, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and "cUrlDanfe" in data:
        pdf_url = data["cUrlDanfe"]
    elif isinstance(data, list) and len(data) > 0 and "cUrlDanfe" in data[0]:
        pdf_url = data[0]["cUrlDanfe"]
    else:
        raise HTTPException(status_code=404, detail="PDF do DANFE não encontrado")

    pdf_response = requests.get(pdf_url)
    pdf_response.raise_for_status()

    return StreamingResponse(io.BytesIO(pdf_response.content), media_type="application/pdf")


def criar_usuario(nome: str, documento: str, senha: str, email: str = None, db: Session = None):
    """Função utilitária para criar usuário com grupo 'cliente'"""
    if db is None:
        db = SessionLocal()

    # Verifica se já existe usuário com o mesmo documento
    existente = db.query(Usuarios).filter(Usuarios.documento == documento).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Usuário com documento {documento} já existe.")

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    usuario = Usuarios(
        nome=nome,
        documento=documento,
        senha=senha_hash,
        grupo="cliente",  # <- grupo fixo
        email=email
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario

# ---------------- ENDPOINT ----------------
@app.post("/usuarios/cliente")
def criar_usuario_cliente_endpoint(
    nome: str = Body(...),
    documento: str = Body(...),
    senha: str = Body(...),
    email: str | None = Body(None),
    db: Session = Depends(SessionLocal)
):
    """
    Cria um usuário com grupo 'cliente'.
    """
    usuario = criar_usuario(nome, documento, senha, email, db)
    return {"success": True, "usuario": {"id": usuario.id, "nome": usuario.nome, "documento": usuario.documento, "email": usuario.email, "grupo": usuario.grupo}}


def autenticar_api_key(key: str = Query(..., description="Chave de API")):
    if key != os.environ.get("API_KEY_SUPER_SECRET"):
        raise HTTPException(status_code=401, detail="API Key inválida")
    return True


@app.get("/usuarios/{documento}")
def buscar_usuario(documento: str, db: Session = Depends(get_db), auth: bool = Depends(autenticar_api_key)):
    documento_numeros = somente_numeros(documento)
    usuario = db.query(Usuarios).filter(
        func.regexp_replace(Usuarios.documento, r'\D', '', 'g') == documento_numeros
    ).first()
    if not usuario:
        return {"existe": False}
    return {"existe": True, "status": usuario.status}


@app.post("/usuarios/convite")
def convidar_usuario(
    nome: str = Body(...),
    documento: str = Body(...),
    email: str = Body(...),
    db: Session = Depends(get_db)
):
    existente = db.query(Usuarios).filter(Usuarios.documento == documento).first()
    if existente:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    usuario = Usuarios(
        nome=nome,
        documento=documento,
        senha=None,
        grupo="cliente",
        email=email,
        status="pendente"
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # gera token temporário
    token = gerar_token(32)
    tokens_temp[documento] = {"token": token, "expira": datetime.utcnow() + timedelta(hours=1)}

    # envia link por e-mail
    link = f"https://api.optionbakerysystems.com/definir-senha?token={token}$&key=7X9L2Q0M8R5Z1Y4H6C3D8N0K5W2T9V1"
    print(f"Link para definir senha (enviar por email): {link}")
    enviar_email(email, "Defina sua senha", f"Olá {nome},\n\nClique no link para definir sua senha:\n{link}\n\nEsse link expira em 1 hora.")

    return {"success": True, "message": "Convite enviado", "link": link}



def validar_senha(senha: str):
    # Pelo menos 8 caracteres
    if len(senha) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 8 caracteres")

    # Pelo menos uma letra maiúscula
    if not re.search(r"[A-Z]", senha):
        raise HTTPException(status_code=400, detail="A senha deve conter pelo menos uma letra maiúscula")

    # Pelo menos uma letra minúscula
    if not re.search(r"[a-z]", senha):
        raise HTTPException(status_code=400, detail="A senha deve conter pelo menos uma letra minúscula")

    # Pelo menos um número
    if not re.search(r"[0-9]", senha):
        raise HTTPException(status_code=400, detail="A senha deve conter pelo menos um número")

    return True

@app.put("/usuarios/{documento}/status")
def atualizar_status_usuario(
    documento: str,
    novo_status: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    auth: bool = Depends(autenticar_api_key)
):
    if novo_status not in ["ativo", "inativo"]:
        raise HTTPException(status_code=400, detail="Status inválido. Use 'ativo' ou 'inativo'.")
    
    documento_numeros = somente_numeros(documento)
    usuario = db.query(Usuarios).filter(
        func.regexp_replace(Usuarios.documento, r'\D', '', 'g') == documento_numeros
    ).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    usuario.status = novo_status
    db.commit()
    db.refresh(usuario)
    
    return {"success": True, "documento": usuario.documento, "status": usuario.status}


@app.post("/usuarios/definir-senha")
def definir_senha(
    token: str = Body(...),
    nova_senha: str = Body(...),
    confirmar_senha: str = Body(...),
    db: Session = Depends(get_db)
):
    # 1. Verifica se as senhas coincidem
    if nova_senha != confirmar_senha:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")

    # 2. Valida a força da senha
    validar_senha(nova_senha)

    # 3. Procura o token
    documento = None
    for doc, registro in tokens_temp.items():
        if registro["token"] == token:
            documento = doc
            if registro["expira"] < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Token expirado")
            break

    if not documento:
        raise HTTPException(status_code=400, detail="Token inválido")

    usuario = db.query(Usuarios).filter(Usuarios.documento == documento).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # 4. Grava senha
    usuario.senha = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    usuario.status = "ativo"   # 👈 atualiza status
    db.commit()

    # 5. Invalida token
    del tokens_temp[documento]

    return {"success": True, "message": "Senha definida com sucesso"}


@app.post("/usuarios/convite_interno")
def convidar_usuario_interno(
    nome: str = Body(...),
    documento: str = Body(...),
    email: str = Body(...),
    db: Session = Depends(get_db)
):
    """
    Cria um usuário interno (grupo 'usuario') e envia link para definir senha.
    """
    existente = db.query(Usuarios).filter(Usuarios.documento == documento).first()
    if existente:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    usuario = Usuarios(
        nome=nome,
        documento=documento,
        senha=None,
        grupo="usuario",  # 👈 diferente do convite de cliente
        email=email,
        status="pendente"
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # Gera token temporário
    token = gerar_token(32)
    tokens_temp[documento] = {
        "token": token,
        "expira": datetime.utcnow() + timedelta(hours=1)
    }

    # Envia link por e-mail
    link = f"https://api.optionbakerysystems.com/definir-senha?token={token}&key=7X9L2Q0M8R5Z1Y4H6C3D8N0K5W2T9V1"
    print(f"Link para definir senha (enviar por email): {link}")
    enviar_email(
        email,
        "Defina sua senha (Acesso Interno)",
        f"Olá {nome},\n\nVocê foi convidado para acessar o sistema Option Bakery Systems.\n"
        f"Clique no link abaixo para definir sua senha:\n\n{link}\n\n"
        f"Esse link expira em 1 hora.\n\nAtenciosamente,\nEquipe Option"
    )

    return {
        "success": True,
        "message": "Convite de acesso interno enviado com sucesso",
        "link": link
    }


@app.get("/definir-senha", response_class=HTMLResponse)
def form_definir_senha(


    request: Request,
    token: str = Query(...),
    key: str = Query("7X9L2Q0M8R5Z1Y4H6C3D8N0K5W2T9V1")
):
    api_key_env = os.getenv("API_KEY_SUPER_SECRET", "7X9L2Q0M8R5Z1Y4H6C3D8N0K5W2T9V1")

    if key != api_key_env:
        raise HTTPException(status_code=401, detail="API Key inválida")

    context = {"request": request, "token": token, "key": key}
    return templates.TemplateResponse("definir_senha.html", context)