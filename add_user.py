"""
Roda via terminal para adicionar usuários:
  python add_user.py

Ou direto com argumentos:
  python add_user.py --login joao --nome "João Silva" --email joao@ailapartners.com.br --senha MinhaSenh@123
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from auth import load_users, save_users, hash_senha, enviar_email


def add_user(login, nome, email, senha, enviar=True):
    usuarios = load_users()
    login = login.strip().lower()

    if login in usuarios:
        print(f"Usuário '{login}' já existe.")
        return False

    usuarios[login] = {
        "nome": nome,
        "email": email,
        "senha_hash": hash_senha(senha),
        "ativo": True,
    }
    save_users(usuarios)
    print(f"✅ Usuário '{login}' criado com sucesso.")

    if enviar:
        corpo = f"""
        <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
            <h2 style="color:#185FA5;">FIDC Dashboard</h2>
            <p>Olá, <b>{nome}</b>!</p>
            <p>Seu acesso ao FIDC Dashboard foi criado.</p>
            <p><b>Usuário:</b> {login}</p>
            <p><b>Senha inicial:</b> <code style="font-size:18px;">{senha}</code></p>
            <p>Recomendamos que você troque sua senha no primeiro acesso.</p>
        </div>
        """
        ok = enviar_email(email, "FIDC Dashboard — Bem-vindo!", corpo)
        if ok:
            print(f"📧 Email de boas-vindas enviado para {email}.")
        else:
            print(f"⚠️  Não foi possível enviar o email para {email}.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adicionar usuário ao FIDC Dashboard")
    parser.add_argument("--login",  required=False)
    parser.add_argument("--nome",   required=False)
    parser.add_argument("--email",  required=False)
    parser.add_argument("--senha",  required=False)
    parser.add_argument("--no-email", action="store_true")
    args = parser.parse_args()

    if args.login and args.nome and args.email and args.senha:
        add_user(args.login, args.nome, args.email, args.senha, enviar=not args.no_email)
    else:
        print("=== Adicionar novo usuário ===")
        login = input("Login (ex: joao): ").strip()
        nome  = input("Nome completo: ").strip()
        email = input("Email: ").strip()
        senha = input("Senha inicial: ").strip()
        add_user(login, nome, email, senha)