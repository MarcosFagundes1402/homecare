# 1. Objetivo - Fornecer todos os serviços necessários para o sistema de gerenciamento de cuidadores de idosos, permitindo que administradores, cuidadores e familiares acessem e manipulem informações de forma segura.

# 2. URL base - localhost/API/V1

# 3. Endpoints -
    AUTENTIÇAO
        POST   / login
        POST   / logout
        POST   / resfresh-token

    USUARIOS
        GET    / users
        GET    / users/{id}
        POST   / users
        PUT    / users/{id}
        DELETE / users/{id}

    EMPRESAS 
        GET     / empresas
        GET     / empresas/{id}
        POST    / empresas
        PUT     / empresas/{id}
        DELETE  / empresas/{id}

    POCIENTES
        GET     / pacientes
        GET     / pacientes/{id}
        POST    / pacientes
        PUT     / pacientes/{id}
        DELETE  / pacientes/{id}

    CUIDADORES
        GET     / cuidadores
        GET     / cuidadores/{id}
        POST    / cuidadores
        PUT     / cuidadores/{id}
        DELETE  / cuidadores/{id}

    FAMILIARES
        GET     / familiares
        GET     / familiares/{id}
        POST    / familiares
        PUT     / familiares/{id}
        DELETE  / familiares/{id}

    RELATORIOS
        GET     / relatorios
        POST    / relatorios
        GET     / relatorios/{id}
        PUT     / relatorios/{id}
        DELETE  / relatorios/{id}

    PONTOS
        POST    / pontos
        PUT     / pontos/{id}/saida
        GET     / pontos
        GET     / pontos/{id}