# backend/models/__init__.py

# Este arquivo pode ficar vazio ou ser usado para facilitar importações.
# Por enquanto, vamos deixá-lo simples. 
# Quando tivermos os modelos, nós os importaremos aqui 
# para que o Flask-Migrate os encontre.

# Futuramente, adicionaremos linhas como:
# from .users import User, Role
# from .companies import Company
# ...etc.

print("Carregando pacote de modelos (models)...")

# Para que o Flask-Migrate funcione, ele precisa saber 
# quais modelos existem. Vamos importar o db aqui 
# e os modelos abaixo dele assim que os criarmos.

# Importa a instância 'db' que será criada em 'app.py'
# Usamos uma tentativa de importação para evitar erros se app.py
# ainda não estiver totalmente carregado.
try:
    from app import db
except ImportError:
    # Isso pode acontecer em alguns cenários de inicialização,
    # mas os modelos reais lidarão com a importação correta.
    pass