import streamlit as st
import pandas as pd
import hashlib
import os
import datetime
from PIL import Image
from streamlit_qrcode_scanner import qrcode_scanner  

# Cores do projeto
COR_PRIMARIA = "#f44336"   # vermelho
COR_SECUNDARIA = "#1565c0" # azul escuro
COR_TEXTO = "#004d40"      # verde escuro
COR_FUNDO = "#f1f8e9"      # verde claro

# Logo
logo_path = "03.webp"  # Use o nome real do seu arquivo
CAMINHO_ARQUIVO_ALUNOS = "alunos.csv"
CAMINHO_ARQUIVO_LOG = "log_creditos.csv"

def carregar_usuarios():
    try:
        return pd.read_csv("usuarios.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["usuario", "senha_hash"])

def verificar_login(usuario, senha, usuarios_df):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    usuario_linha = usuarios_df[usuarios_df['usuario'] == usuario]
    if not usuario_linha.empty:
        return usuario_linha.iloc[0]['senha_hash'] == senha_hash
    return False

def carregar_dados_alunos():
    if os.path.exists(CAMINHO_ARQUIVO_ALUNOS):
        return pd.read_csv(CAMINHO_ARQUIVO_ALUNOS)
    else:
        return pd.DataFrame(columns=[
            "id_qrcode", "nome", "idade", "turma", "escola", 
            "saldo", "data_cadastro", "ultima_movimentacao"
        ])

def salvar_dados_alunos(df):
    df.to_csv(CAMINHO_ARQUIVO_ALUNOS, index=False)


def tela_cadastro_aluno():
    st.subheader("📋 Cadastro de Aluno com QR Code")

    modo_qr = st.radio("Como deseja fornecer o QR Code do aluno?", ["📷 Escanear com a câmera", "⌨️ Digitar manualmente"])

    if modo_qr == "📷 Escanear com a câmera":
        id_qrcode = qrcode_scanner(key="leitor_qr")
        if id_qrcode:
            st.success(f"✅ QR Code lido com sucesso: `{id_qrcode}`")
    else:
        id_qrcode = st.text_input("ID do QR Code (digite ou cole)", max_chars=50)

    with st.form("form_cadastro_aluno"):
        nome = st.text_input("Nome completo do aluno")
        idade = st.number_input("Idade", min_value=5, max_value=25, step=1)
        turma = st.text_input("Turma (ex: 6º A, 7º B)")
        escola = st.session_state.get("usuario", "")  # assume que o nome da escola é o login
        pontos_iniciais = st.number_input("Saldo inicial (pontos)", min_value=0.0, step=0.5)

        submitted = st.form_submit_button("Salvar Cadastro")

        if submitted:
            if not id_qrcode:
                st.warning("⚠️ Você precisa escanear ou digitar um QR Code válido.")
                st.stop()

            df_alunos = carregar_dados_alunos()
            id_qrcode = id_qrcode.strip().lower()
            df_alunos["id_qrcode"] = df_alunos["id_qrcode"].astype(str).str.strip().str.lower()

            if id_qrcode in df_alunos["id_qrcode"].values:
                st.error("❌ Esse QR Code já está cadastrado.")
                st.stop()

            data_atual = datetime.datetime.now().strftime("%d/%m/%Y")

            novo_aluno = pd.DataFrame([{
                "id_qrcode": id_qrcode,
                "nome": nome.strip(),
                "idade": idade,
                "turma": turma.strip(),
                "escola": escola,
                "saldo": pontos_iniciais,
                "data_cadastro": data_atual,
                "ultima_movimentacao": data_atual
            }])

            df_alunos = pd.concat([df_alunos, novo_aluno], ignore_index=True)
            salvar_dados_alunos(df_alunos)

            st.success(f"✅ Aluno(a) {nome} cadastrado(a) com sucesso!")

def carregar_log_creditos():
    if os.path.exists(CAMINHO_ARQUIVO_LOG):
        return pd.read_csv(CAMINHO_ARQUIVO_LOG)
    else:
        return pd.DataFrame(columns=[
            "data_hora", "id_qrcode", "nome", "escola", "operacao", "valor", "realizado_por"
        ])

def salvar_log_creditos(df):
    df.to_csv(CAMINHO_ARQUIVO_LOG, index=False)

def registrar_log(id_qrcode, nome, escola, operacao, valor, realizado_por):
    df_log = carregar_log_creditos()
    novo_log = pd.DataFrame([{
        "data_hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "id_qrcode": id_qrcode,
        "nome": nome,
        "escola": escola,
        "operacao": operacao,
        "valor": valor,
        "realizado_por": realizado_por
    }])
    df_log = pd.concat([df_log, novo_log], ignore_index=True)
    salvar_log_creditos(df_log)


def tela_creditos(tipo_operacao):
    titulo = "➕ Adicionar Créditos" if tipo_operacao == "adicao" else "➖ Remover Créditos"
    st.subheader(titulo)

    modo = st.radio("Modo de identificação do aluno:", ["📷 Escanear QR Code", "⌨️ Digitar Manualmente"])

    id_qrcode = None
    if modo == "📷 Escanear QR Code":
        id_qrcode = qrcode_scanner(key="scanner_credito")
        if id_qrcode:
            st.success(f"✅ QR Code lido com sucesso: `{id_qrcode}`")
        else:
            st.info("Aguardando leitura do QR Code...")
    else:
        id_qrcode = st.text_input("ID do QR Code (digite ou cole)", max_chars=50)

    valor = st.number_input("Valor em pontos", min_value=0.0, step=0.5)
    confirmar = st.button(titulo)

    if confirmar:
        if not id_qrcode:
            st.warning("⚠️ Nenhum QR Code fornecido.")
            st.stop()

        df_alunos = carregar_dados_alunos()
        id_qrcode = id_qrcode.strip().lower()
        df_alunos["id_qrcode"] = df_alunos["id_qrcode"].astype(str).str.strip().str.lower()

        escola_usuario = st.session_state.get("usuario", "").strip().lower()
        df_alunos["escola"] = df_alunos["escola"].astype(str).str.strip().str.lower()
        aluno = df_alunos[(df_alunos["id_qrcode"] == id_qrcode) & (df_alunos["escola"] == escola_usuario)]

        if aluno.empty:
            st.error("❌ Aluno não encontrado.")
            return

        idx = aluno.index[0]

        if tipo_operacao == "remocao" and df_alunos.at[idx, "saldo"] < valor:
            st.warning("⚠️ Saldo insuficiente.")
            return

        operacao = "Adição" if tipo_operacao == "adicao" else "Remoção"
        df_alunos.at[idx, "saldo"] += valor if tipo_operacao == "adicao" else -valor
        df_alunos.at[idx, "ultima_movimentacao"] = datetime.datetime.now().strftime("%d/%m/%Y")
        salvar_dados_alunos(df_alunos)

        registrar_log(
            id_qrcode=id_qrcode,
            nome=df_alunos.at[idx, "nome"],
            escola=df_alunos.at[idx, "escola"],
            operacao=operacao,
            valor=valor,
            realizado_por=st.session_state.get("usuario", "Desconhecido")
        )

        st.success(f"{operacao} de {valor} ponto(s) realizada com sucesso para {df_alunos.at[idx, 'nome']}.")


def tela_visualizar_saldo():
    st.subheader("📦 Consultar Saldo do Aluno")
    
    modo = st.radio("Modo de identificação do aluno:", ["📷 Escanear QR Code", "⌨️ Digitar Manualmente"])
    
    id_qrcode = None
    if modo == "📷 Escanear QR Code":
        id_qrcode = qrcode_scanner(key="scanner_saldo")
        if id_qrcode:
            st.success(f"✅ QR Code lido com sucesso: `{id_qrcode}`")
        else:
            st.info("Aguardando leitura do QR Code...")
    else:
        id_qrcode = st.text_input("ID do QR Code (digite ou cole)", max_chars=50)

    if st.button("Consultar Saldo"):
        if not id_qrcode:
            st.warning("⚠️ Nenhum QR Code fornecido.")
            st.stop()

        df_alunos = carregar_dados_alunos()
        id_qrcode = id_qrcode.strip().lower()
        df_alunos["id_qrcode"] = df_alunos["id_qrcode"].astype(str).str.strip().str.lower()

        escola_usuario = st.session_state.get("usuario", "").strip().lower()
        df_alunos["escola"] = df_alunos["escola"].astype(str).str.strip().str.lower()

        aluno = df_alunos[(df_alunos["id_qrcode"] == id_qrcode) & (df_alunos["escola"] == escola_usuario)]

        if aluno.empty:
            st.error("❌ Aluno não encontrado ou não pertence à sua escola.")
            return

        aluno_info = aluno.iloc[0]
        st.success("✅ Aluno encontrado:")
        st.markdown(f"""
        - **Nome:** {aluno_info['nome']}
        - **Idade:** {aluno_info['idade']} anos  
        - **Turma:** {aluno_info['turma']}  
        - **Saldo Atual:** `{aluno_info['saldo']} ponto(s)`
        - **Última movimentação:** {aluno_info['ultima_movimentacao']}
        - **Data de cadastro:** {aluno_info['data_cadastro']}
        """)

def tela_consultar_por_nome():
    st.subheader("🔎 Consultar Aluno por Nome")

    nome_busca = st.text_input("Digite o nome (ou parte do nome) do aluno")

    if nome_busca:
        df_alunos = carregar_dados_alunos()
        escola_usuario = st.session_state.get("usuario", "").strip().lower()
        df_alunos["escola"] = df_alunos["escola"].astype(str).str.strip().str.lower()

        resultados = df_alunos[
            (df_alunos["escola"] == escola_usuario) &
            (df_alunos["nome"].str.lower().str.contains(nome_busca.strip().lower()))
        ]

        if resultados.empty:
            st.warning("❌ Nenhum aluno encontrado com esse nome.")
        else:
            st.success(f"✅ {len(resultados)} aluno(s) encontrado(s):")
            for idx, row in resultados.iterrows():
                st.markdown(f"""
                ---
                - **Nome:** {row['nome']}
                - **Idade:** {row['idade']} anos
                - **Turma:** {row['turma']}
                - **Saldo Atual:** `{row['saldo']} ponto(s)`
                - **ID QR Code:** `{row['id_qrcode']}`
                - **Última movimentação:** {row['ultima_movimentacao']}
                - **Data de cadastro:** {row['data_cadastro']}
                """)

# --- Layout ---
def tela_login():
    st.set_page_config(page_title="Tampinha Mágica", page_icon="🧙‍♂️", layout="centered")

    st.markdown(
        f"""
        <div style='text-align:center'>
            <img src='data:image/png;base64,{get_image_base64(logo_path)}'
                 style='max-width: 280px; width: 100%; height: auto; image-rendering: auto;' />
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("### 🔐 Login")
    usuarios = carregar_usuarios()
    email = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
      if verificar_login(email, senha, usuarios):
          st.session_state["logado"] = True
          st.session_state["usuario"] = email
          st.rerun()
      else:
          st.error("Usuário ou senha inválidos.")

# --- Painel pós-login ---
def tela_painel():
    st.set_page_config(page_title="Tampinha Mágica", page_icon="🧙‍♂️", layout="wide")
    # Aplica o fundo branco no menu
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                background-color: white;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.image(logo_path, use_container_width=True)
    #st.sidebar.markdown(f"<h2 style='color:{COR_PRIMARIA};'>Tampinha Mágica</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    st.sidebar.success(f"Usuário: {st.session_state['usuario']}")
    
    menu = st.sidebar.radio("📚 Menu Principal", [
        "📋 Cadastro de Aluno",
        "➕ Adicionar Créditos",
        "➖ Remover Créditos",
        "📦 Visualizar Saldo",
        "🔎 Consultar por Nome",
        "🚪 Sair"
    ])

    st.markdown(f"<h2 style='color:{COR_TEXTO};'>🧙‍♂️ {menu}</h2>", unsafe_allow_html=True)

    if menu == "📋 Cadastro de Aluno":
        tela_cadastro_aluno()
    elif menu == "➕ Adicionar Créditos":
        tela_creditos("adicao")
    elif menu == "➖ Remover Créditos":
        tela_creditos("remocao")
    elif menu == "📦 Visualizar Saldo":
        tela_visualizar_saldo()
    elif menu == "🔎 Consultar por Nome":
        tela_consultar_por_nome()
    elif menu == "🚪 Sair":
        st.session_state["logado"] = False
        st.session_state["usuario"] = ""
        st.rerun()


# --- Utilitário para mostrar imagem como base64 ---
import base64
def get_image_base64(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

# --- Controle de sessão ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario"] = ""

if not st.session_state["logado"]:
    tela_login()
else:
    tela_painel()
