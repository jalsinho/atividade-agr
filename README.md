# Mural de Achados & Perdidos

Aplicacao web em Flask com SQLite para publicar itens perdidos ou encontrados, consultar o mural e acompanhar a devolucao.

## Executar

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Acesse http://127.0.0.1:5000. O banco SQLite e criado automaticamente em `instance/mural.sqlite3`.

## Fluxo dos itens

- Item perdido: Aberto -> Encontrado -> Devolvido.
- Item encontrado: Encontrado -> Devolvido.

Para uso fora de desenvolvimento local, defina uma `SECRET_KEY` segura e execute com um servidor WSGI de producao.