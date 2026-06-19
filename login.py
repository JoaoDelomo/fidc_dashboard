import streamlit as st
from auth import autenticar, resetar_senha


def tela_login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "modo_login" not in st.session_state:
        st.session_state.modo_login = "login"

    if st.session_state.autenticado:
        return True

    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        st.markdown("""
        <div style='text-align:center;padding:40px 0 20px;'>
            <h1 style='font-size:28px;color:#185FA5;margin-bottom:4px;'>📊 FIDC Dashboard</h1>
            <p style='color:#6c757d;font-size:14px;'>Larca Aurora</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.modo_login == "login":
            with st.form("form_login"):
                login  = st.text_input("Usuário ou email", placeholder="helena ou helena@...")
                senha  = st.text_input("Senha", type="password", placeholder="••••••••")
                entrar = st.form_submit_button("Entrar", use_container_width=True)

            if entrar:
                if not login or not senha:
                    st.error("Preencha usuário e senha.")
                else:
                    usuario = autenticar(login, senha)
                    if usuario:
                        st.session_state.autenticado = True
                        st.session_state.usuario = {**usuario, "login": login.strip().lower()}
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Esqueci minha senha", use_container_width=True):
                st.session_state.modo_login = "reset"
                st.rerun()

        elif st.session_state.modo_login == "reset":
            st.markdown("### Redefinir senha")
            st.caption("Informe o email cadastrado e enviaremos uma senha temporária.")

            with st.form("form_reset"):
                email  = st.text_input("Email", placeholder="seu@email.com")
                enviar = st.form_submit_button("Enviar nova senha", use_container_width=True)

            if enviar:
                if not email:
                    st.error("Informe seu email.")
                else:
                    with st.spinner("Enviando..."):
                        ok = resetar_senha(email)
                    if ok:
                        st.success("Email enviado! Verifique sua caixa de entrada.")
                    else:
                        st.error("Email não encontrado na base de usuários.")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Voltar ao login", use_container_width=True):
                st.session_state.modo_login = "login"
                st.rerun()

    return False