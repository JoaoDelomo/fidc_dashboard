import json
import os
import bcrypt
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

USERS_PATH = os.path.join(os.path.dirname(__file__), "users.json")
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")


def load_users() -> dict:
    if not os.path.exists(USERS_PATH):
        return {}
    with open(USERS_PATH, encoding="utf-8") as f:
        return json.load(f).get("usuarios", {})


def save_users(usuarios: dict):
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump({"usuarios": usuarios}, f, ensure_ascii=False, indent=2)


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), hash_salvo.encode())
    except:
        return False


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def autenticar(login: str, senha: str) -> dict | None:
    usuarios = load_users()
    login = login.strip().lower()
    if login not in usuarios:
        return None
    u = usuarios[login]
    if not u.get("ativo", True):
        return None
    if verificar_senha(senha, u["senha_hash"]):
        return u
    return None


def gerar_senha_temp(tamanho: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(tamanho))


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = destinatario
        msg.attach(MIMEText(corpo_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False


def resetar_senha(email: str) -> bool:
    usuarios = load_users()
    usuario_key = None
    for key, u in usuarios.items():
        if u["email"].lower() == email.strip().lower():
            usuario_key = key
            break

    if not usuario_key:
        return False

    nova_senha = gerar_senha_temp()
    usuarios[usuario_key]["senha_hash"] = hash_senha(nova_senha)
    save_users(usuarios)

    corpo = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
        <h2 style="color:#185FA5;">FIDC Dashboard</h2>
        <p>Olá, <b>{usuarios[usuario_key]['nome']}</b>!</p>
        <p>Recebemos uma solicitação de redefinição de senha para sua conta.</p>
        <p>Sua nova senha temporária é:</p>
        <div style="background:#f8f9fa;border-radius:8px;padding:16px;text-align:center;
                    font-size:24px;font-weight:bold;letter-spacing:4px;color:#212529;
                    margin:16px 0;">
            {nova_senha}
        </div>
        <p>Acesse o sistema e troque sua senha assim que possível.</p>
        <hr style="border-color:#dee2e6;">
        <p style="font-size:12px;color:#6c757d;">
            Se você não solicitou a redefinição, ignore este email.
        </p>
    </div>
    """
    return enviar_email(usuarios[usuario_key]["email"], "FIDC Dashboard — Nova senha temporária", corpo)


def alterar_senha(login: str, senha_atual: str, nova_senha: str) -> bool:
    usuarios = load_users()
    login = login.strip().lower()
    if login not in usuarios:
        return False
    if not verificar_senha(senha_atual, usuarios[login]["senha_hash"]):
        return False
    usuarios[login]["senha_hash"] = hash_senha(nova_senha)
    save_users(usuarios)
    return True