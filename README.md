# FIAP Tech Challenge - Fase 1

API desenvolvida para realizar scraping de livros do site [Books to Scrape](https://books.toscrape.com) e disponibilizar os dados através de uma API RESTful com autenticação via JWT.

---

## Índice

- [FIAP Tech Challenge - Fase 1](#fiap-tech-challenge---fase-1)
	- [Índice](#índice)
	- [Tecnologias Utilizadas](#tecnologias-utilizadas)
	- [Estrutura do Projeto](#estrutura-do-projeto)
	- [Arquitetura da Aplicação](#arquitetura-da-aplicação)
	- [Como Executar](#como-executar)
		- [Em produção](#em-produção)
			- [API](#api)
			- [Dashboard](#dashboard)
		- [Localmente](#localmente)
			- [API](#api-1)
			- [Dashboard](#dashboard-1)
	- [Autenticação e Acesso](#autenticação-e-acesso)
		- [Requisição de login para o usuário `admin`](#requisição-de-login-para-o-usuário-admin)
		- [Requisição de login para o usuário `user`](#requisição-de-login-para-o-usuário-user)
		- [Resposta esperada](#resposta-esperada)
		- [Como usar o token](#como-usar-o-token)
		- [Renovar token](#renovar-token)
	- [Endpoints da API](#endpoints-da-api)
		- [Run results](#run-results)
		- [POST /api/v1/auth/login](#post-apiv1authlogin)
			- [Body](#body)
			- [Resposta](#resposta)
		- [POST /api/v1/auth/refresh](#post-apiv1authrefresh)
			- [Body](#body-1)
			- [Resposta](#resposta-1)
		- [GET /api/v1/health](#get-apiv1health)
			- [Resposta](#resposta-2)
		- [GET /api/v1/health/performance](#get-apiv1healthperformance)
			- [Resposta](#resposta-3)
		- [GET /api/v1/books/search](#get-apiv1bookssearch)
			- [Parâmetros de exemplo](#parâmetros-de-exemplo)
			- [Resposta](#resposta-4)
		- [GET /api/v1/books/{id}](#get-apiv1booksid)
			- [Parâmetros de exemplo](#parâmetros-de-exemplo-1)
			- [Resposta](#resposta-5)
		- [GET /api/v1/books/top-rated](#get-apiv1bookstop-rated)
			- [Resposta](#resposta-6)
		- [/api/v1/books/price-range](#apiv1booksprice-range)
			- [Parâmetros de exemplo](#parâmetros-de-exemplo-2)
			- [Resposta](#resposta-7)
		- [GET /api/v1/books/categories](#get-apiv1bookscategories)
			- [Resposta](#resposta-8)
		- [GET /api/v1/stats/overview](#get-apiv1statsoverview)
			- [Resposta](#resposta-9)
		- [GET /api/v1/stats/categories](#get-apiv1statscategories)
			- [Resposta](#resposta-10)
		- [POST /api/v1/scraping/trigger](#post-apiv1scrapingtrigger)
			- [Auth](#auth)
			- [Params](#params)
			- [Resposta](#resposta-11)
		- [GET /api/v1/ml/features](#get-apiv1mlfeatures)
			- [Resposta](#resposta-12)
		- [GET /api/v1/ml/training-data](#get-apiv1mltraining-data)
			- [Resposta](#resposta-13)
		- [POST /api/v1/ml/predictions](#post-apiv1mlpredictions)
			- [Body](#body-2)
			- [Resposta](#resposta-14)
	- [Scraping](#scraping)
	- [Estatísticas](#estatísticas)
	- [Scripts e Utilitários](#scripts-e-utilitários)
	- [Logs](#logs)
	- [Dashboard de Insights](#dashboard-de-insights)

---

## Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Pandas](https://pandas.pydata.org/)
- [JWT](https://jwt.io/)
- [SQLite (via SQLAlchemy)](https://www.sqlite.org/index.html)
- [Loguru](https://github.com/Delgan/loguru)

---

##  Estrutura do Projeto
```plaintext
.
├── api/
│   ├── auth.py              # Lógica de autenticação, tokens e endpoints
│   ├── books.py			 # Endpoints relacionados a livros
│   ├── main.py              # Entrypoint da API FastAPI e roteadores
│   ├── metrics.py           # Endpoints de estatísticas (health e performance) e lógica
│   ├── ml.py 			     # Endpoints relacionados a Machine Learning e lógica
│   ├── models.py            # Schemas Pydantic (dados, respostas)
│   ├── scraping.py		     # Endpoints de scraping e lógica
│   ├── state.py			 # Estado global da aplicação (DB de livros em memória)
│   ├── stats.py			 # Lógica de estatísticas dos livros e endpoints
├── dashboard/
│   ├── app.py               # Aplicação Dash para visualização dos dados usando streamlit
├── data/
│   └── books.csv            # Base de dados em CSV (scraping)
│   └── auth.db              # Banco de usuários (SQLite)
├── doc/
│   ├── imagens.png		     # Imagens usadas na documentação README
├── logs/
│   └── app.log              # Arquivo de log (local)
├── scripts/
│   └── scraper.py           # Script Web scraper do site de livros
├── utils/
│   └── logger.py            # Logger global configurado com Loguru
├── README.md                # Documentação principal
└── requirements.txt         # Dependências do projeto
```
---

## Arquitetura da Aplicação

```mermaid
graph TB
    subgraph INGESTAO ["INGESTÃO DE DADOS"]
        WEB["books.toscrape.com<br/>Fonte Externa"]
        SCRAPER["scripts/scraper.py<br/>Web Scraper"]
        COLETA["requests + BeautifulSoup<br/>Coleta HTML"]
    end

    subgraph PROCESSAMENTO ["PROCESSAMENTO"]
        PARSE["Parse HTML<br/>parse_book()"]
        TRANSFORM["Transformação<br/>Rating, Preço, Disponibilidade"]
        ENRICH["Enriquecimento<br/>Adiciona ID, Categoria"]
    end

    subgraph ARMAZENAMENTO ["ARMAZENAMENTO"]
        CSV["data/books.csv<br/>Persistência"]
        STATE["In-Memory DB<br/>state.py"]
    end

    subgraph API ["FASTAPI - CAMADA DE SERVIÇO"]
        MAIN["main.py<br/>Inicialização"]
        
        subgraph AUTENTICACAO ["Segurança"]
            AUTH["auth.py<br/>JWT + Login"]
        end
        
        subgraph ENDPOINTS_PUBLICOS ["Endpoints Públicos"]
            BOOKS["books.py<br/>GET /books"]
            STATS["stats.py<br/>GET /stats"]
            ML["ml.py<br/>GET /features"]
        end
        
        subgraph ENDPOINTS_ADMIN ["Endpoints Admin"]
            METRICS["metrics.py<br/>POST /health/performance"]
            SCRAPING["scraping.py<br/>POST /scraping/trigger"]
        end
        
        VALIDACAO["✅ Pydantic Models<br/>Validação + Serialização"]
    end

    subgraph CONSUMO ["CONSUMO"]
        CLIENTE_HTTP["Cliente HTTP<br/>curl, Postman, etc"]
        DASHBOARD["Dashboard Streamlit<br/>Visualizações"]
        USER["Usuário Final"]
    end

    %% INGESTÃO
    SCRAPER -->|Dispara em background| COLETA
    COLETA -->|GET Request| WEB
    WEB -->|HTML Response| PARSE

    %% PROCESSAMENTO
    PARSE -->|Extrai dados brutos| TRANSFORM
    TRANSFORM -->|Normaliza campos| ENRICH

    %% ARMAZENAMENTO
    ENRICH -->|Salva DataFrame| CSV
    CSV -->|Carrega no startup| MAIN
    MAIN -->|Popula memória| STATE

    %% API - Fluxo Admin (Scraping)
    CLIENTE_HTTP -->|POST /scraping/trigger<br/>ADMIN| SCRAPING
    SCRAPING -->|Dispara| SCRAPER
    SCRAPER -->|Atualiza| CSV
    CSV -->|Reload| STATE

    %% API - Autenticação
    CLIENTE_HTTP -->|POST /auth/login| AUTH
    AUTH -->|JWT Token| CLIENTE_HTTP

    %% API - Endpoints Públicos
    CLIENTE_HTTP -->|GET /books| BOOKS
    CLIENTE_HTTP -->|GET /stats| STATS
    CLIENTE_HTTP -->|GET /ml/features| ML
    
    BOOKS -->|Lê dados| STATE
    STATS -->|Agrega dados| STATE
    ML -->|Formata features| STATE

    %% API - Validação
    BOOKS -->|Valida| VALIDACAO
    STATS -->|Valida| VALIDACAO
    ML -->|Valida| VALIDACAO
    VALIDACAO -->|Response JSON| CLIENTE_HTTP

    %% API - Admin Metrics
    CLIENTE_HTTP -->|POST /health/performance<br/>ADMIN| METRICS

    %% Dashboard
    DASHBOARD -->|GET /stats| STATS
    DASHBOARD -->|GET /health| METRICS
    DASHBOARD -->|Render gráficos| DASHBOARD
    USER -->|Acessa| DASHBOARD
    DASHBOARD -->|Visualiza| USER

    style INGESTAO fill:#FF6B6B,stroke:#C92A2A,color:#fff,stroke-width:2px
    style PROCESSAMENTO fill:#FFA94D,stroke:#F76707,color:#fff,stroke-width:2px
    style ARMAZENAMENTO fill:#2196F3,stroke:#1565C0,color:#fff,stroke-width:2px
    style API fill:#4CAF50,stroke:#2E7D32,color:#fff,stroke-width:3px
    style CONSUMO fill:#9C27B0,stroke:#6A1B9A,color:#fff,stroke-width:2px
    style AUTENTICACAO fill:#FF9800,stroke:#E65100,color:#fff
    style ENDPOINTS_ADMIN fill:#FF5722,stroke:#BF360C,color:#fff
```

---

## Como Executar

### Em produção
A API foi disponibilizada via [Render](https://render.com/) e pode ser acessada no link abaixo:
Observação: A aplicação é hospedada em um plano gratuito, portanto pode haver um tempo de "wake up" quando acessada após um período de 15 minutos de inatividade.

#### API

`https://fiap-tech-challenge-fase1-18ng.onrender.com/docs`


#### Dashboard

`https://fiap-tech-challenge-fase1-1.onrender.com/`


### Localmente

#### API
```bash
# 1. Clone o repositório
git clone https://github.com/rafatega/fiap-tech-challenge-fase1.git

# 2. Crie o ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
.\venv\Scripts\activate (no Windows)
source venv/bin/activate (no Linux/Mac)

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Inicie a API
uvicorn api.main:app --reload

# 6. Acesse a documentação interativa da API no navegador
http://localhost:8000/docs
```

#### Dashboard
```bash
streamlit run dashboard/app.py
```

---

## Autenticação e Acesso
A API utiliza autenticação baseada em JWT (JSON Web Tokens).
Existem dois usuários padrão criados automaticamente no banco:

* admin / `admin123`

* user / `user123`

Você pode usar o endpoint de login para obter um access token e um refresh token:
```bash
POST /api/v1/auth/login
```

### Requisição de login para o usuário `admin`
```json
{
  "username": "admin",
  "password": "admin123"
}
```

### Requisição de login para o usuário `user`
```json
{
  "username": "user",
  "password": "user123"
}
```

### Resposta esperada
```json
{
  "token_type": "bearer",
  "access_token": "<token_de_acesso>",
  "refresh_token": "<token_de_refresh>",
  "expires_in": 3600
}
```

### Como usar o token
Em qualquer endpoint protegido (`/api/v1/scraping/trigger`), adicione o token de acesso no header:
```bash
Authorization: Bearer <access_token>
```
![authTokenConfig](./doc/authTokenConfig.png)

### Renovar token
Para obter um novo par de tokens usando o refresh_token, utilize:
```bash
POST /api/v1/auth/refresh
```
Exemplo de requisição:
```json
{
  "refresh_token": "<token_de_refresh>"
}
```
![refreshTokenConfig](./doc/authRefreshToken.png)

---

## Endpoints da API
| Método | Rota                        | Descrição                              |
| ------ | --------------------------- | -------------------------------------- |
| `POST` | `/api/v1/auth/login`        | Login e obtenção de tokens             |
| `POST` | `/api/v1/auth/refresh`      | Gera novos tokens via refresh          |
| `GET`  | `/api/v1/health`            | Verifica status da API                 |
| `GET`  | `/api/v1/health/performance`| (admin) Verifica desempenho da API     |
| `GET`  | `/api/v1/books`             | Retorna todos os livros                |
| `GET`  | `/api/v1/books/search`      | Busca por título ou categoria          |
| `GET`  | `/api/v1/books/{id}`        | Consulta livro por ID                  |
| `GET`  | `/api/v1/books/top-rated`   | Lista livros com melhor rating         |
| `GET`  | `/api/v1/books/price-range` | Filtra livros por preço                |
| `GET`  | `/api/v1/books/categories`  | Lista categorias disponíveis           |
| `GET`  | `/api/v1/stats/overview`    | Estatísticas gerais dos livros         |
| `GET`  | `/api/v1/stats/categories`  | Estatísticas por categoria             |
| `POST` | `/api/v1/scraping/trigger`  | (admin) Dispara scraping em background |
| `GET`  | `/api/v1/ml/features`       | Retorna as features (X)                |
| `GET`  | `/api/v1/ml/training-data`  | Retorna os dados de treinamento (X e y)|
| `POST` | `/api/v1/ml/predictions`    | Recebe predições e registra em memória |

### Run results
Todas APIs foram testadas utilizando o Postman. Abaixo estão os resultados da execução dos testes, retornando status code 200 para todas as requisições:
```json
{
	"id": "690bbe73-cec0-483e-9a83-31e857624baf",
	"name": "Tech Challenge Fase 1",
	"timestamp": "2026-01-20T00:25:02.272Z",
	"collection_id": "45464934-fd1ead76-9d28-405b-95a7-e368f69ffe6a",
	"folder_id": 0,
	"environment_id": "0",
	"totalPass": 0,
	"delay": 0,
	"persist": true,
	"status": "finished",
	"startedAt": "2026-01-20T00:24:59.188Z",
	"totalFail": 0,
	"results": [
		{
			"id": "9bf068f2-49a2-4c60-85a4-364cc6c04467",
			"name": "/api/v1/auth/login",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/auth/login",
			"time": 173,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				173
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "b43f263d-69eb-433f-aa6b-fc016cd25167",
			"name": "/api/v1/auth/refresh",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/auth/refresh",
			"time": 150,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				150
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "60efc129-e0b8-4e6d-a564-ce9a3c8ad93e",
			"name": "/api/v1/health",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/health",
			"time": 152,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				152
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "c2688b65-bbf3-43f4-915a-f0523b6b1c8b",
			"name": "/api/v1/books",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/books",
			"time": 204,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				204
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "ec44a693-2533-409f-a45b-0d8c083b91b5",
			"name": "/api/v1/books/search",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/books/search\n?title=&category=",
			"time": 437,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				437
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "d0bb8156-13e2-43e7-ad1e-c159a368837e",
			"name": "/api/v1/books/{id}",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/books/100\n",
			"time": 149,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				149
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "5017ee22-bc8e-4d6f-add8-7d882e21fe55",
			"name": "/api/v1/books/top-rated",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/books/top-rated",
			"time": 150,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				150
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "68653e2b-fba4-454b-86b7-0b73996c5888",
			"name": "/api/v1/books/price-range",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/books/price-range?min=20&max=27",
			"time": 147,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				147
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "5e8160e2-028d-4d87-aa59-bd1a0f6f3347",
			"name": "/api/v1//books/categories",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/books/categories\n",
			"time": 147,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				147
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "ebe1d5b8-5d46-4d43-8b81-9eb3790d9018",
			"name": "/api/v1/stats/overview",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/stats/overview\n",
			"time": 143,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				143
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "89d07bf4-31e8-4bf0-8cf7-4575ab31aa2a",
			"name": "/api/v1/stats/categories",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/stats/categories\n",
			"time": 145,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				145
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "a6a316de-2d04-4e1c-8677-68bcc24770ec",
			"name": "/api/v1/ml/features",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/ml/features\n",
			"time": 157,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				157
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "073698a5-5f33-4a78-a475-f84fda2762f9",
			"name": "/api/v1/ml/training-data",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/ml/training-data\n",
			"time": 156,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				156
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "f1e102ee-22a0-442e-80a4-edf62440f480",
			"name": "/api/v1/ml/predictions",
			"url": "https://fiap-tech-challenge-fase1-18ng.onrender.com/api/v1/ml/predictions\n",
			"time": 141,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				141
			],
			"allTests": [
				{}
			]
		}
	],
	"count": 1,
	"totalTime": 2451,
	"collection": {
		"requests": [
			{
				"id": "9bf068f2-49a2-4c60-85a4-364cc6c04467",
				"method": "POST"
			},
			{
				"id": "b43f263d-69eb-433f-aa6b-fc016cd25167",
				"method": "POST"
			},
			{
				"id": "60efc129-e0b8-4e6d-a564-ce9a3c8ad93e",
				"method": "GET"
			},
			{
				"id": "c2688b65-bbf3-43f4-915a-f0523b6b1c8b",
				"method": "GET"
			},
			{
				"id": "ec44a693-2533-409f-a45b-0d8c083b91b5",
				"method": "GET"
			},
			{
				"id": "d0bb8156-13e2-43e7-ad1e-c159a368837e",
				"method": "GET"
			},
			{
				"id": "5017ee22-bc8e-4d6f-add8-7d882e21fe55",
				"method": "GET"
			},
			{
				"id": "68653e2b-fba4-454b-86b7-0b73996c5888",
				"method": "GET"
			},
			{
				"id": "5e8160e2-028d-4d87-aa59-bd1a0f6f3347",
				"method": "GET"
			},
			{
				"id": "ebe1d5b8-5d46-4d43-8b81-9eb3790d9018",
				"method": "GET"
			},
			{
				"id": "89d07bf4-31e8-4bf0-8cf7-4575ab31aa2a",
				"method": "GET"
			},
			{
				"id": "a6a316de-2d04-4e1c-8677-68bcc24770ec",
				"method": "GET"
			},
			{
				"id": "073698a5-5f33-4a78-a475-f84fda2762f9",
				"method": "GET"
			},
			{
				"id": "f1e102ee-22a0-442e-80a4-edf62440f480",
				"method": "POST"
			}
		]
	}
}
```

### POST /api/v1/auth/login
Endpoint para autenticação de usuários e obtenção de tokens JWT.
#### Body
Admin:
```json
{
  "username": "admin123",
  "password": "admin123"
}
```
User:
```json
{
  "username": "user123",
  "password": "user123"
}
```
#### Resposta
```json
{
  "token_type": "bearer",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc2ODc1MDQ5MH0.lNkipr0kVVIoH020U8JbawaZWRkHaBlOU4TNi4_1Vb2",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE3NjkzNTE2OTB9.RPQW8s6j8mjeLPaS0Se1u8dn4oOwe5TYlDmvKBQAtiU",
  "expires_in": 3600
}
```

### POST /api/v1/auth/refresh
Endpoint para renovação de tokens JWT usando o refresh token.

#### Body
Para ser válido o refresh token deve ser o mesmo recebido no login:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE3NjkzNTE2OTB9.RPQW8s6j8mjeLPaS0Se1u8dn4oOwe5TYlDmvKBQAtiU"
}
```
#### Resposta
Você receberá um novo par de tokens:
```json
{
    "token_type": "bearer",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc2ODc1MDYxOX0._n3wqHylwbRvhZbdukxmBxlCOTVNGkoN6WPvEc6if80",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjE3NjkzNTE4MTl9.VZYnCl3rvO_UJ9axpVkkCYS7IqKgoeOWUGYSXnNr6Rc",
    "expires_in": 3600
}
```

### GET /api/v1/health
Endpoint para verificação do status da API. 
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
Retorna o status da API e a quantidade de livros carregados:
```json
{
    "status": "ok",
    "books_loaded": 1000
}
```

### GET /api/v1/health/performance
Endpoint para verificação do desempenho da API.
- Precisa de autenticação como usuário `admin`.
- Não precisa de parâmetros.
#### Resposta
```json
{
    "uptime_seconds": 734,
    "in_flight": 0,
    "total_requests": 52,
    "by_status": {
        "2xx": 47,
        "3xx": 3,
        "4xx": 2
    },
    "top_routes": [
        {
            "route": "/api/v1/stats/overview",
            "count": 5
        },
        {
            "route": "/api/v1/stats/categories",
            "count": 5
        },
        {...},
		{...}
    ],
    "latency_overall": {
        "count": 52,
        "avg_ms": 12.89,
        "p50_ms": 3.08,
        "p95_ms": 15.44,
        "p99_ms": 16.72,
        "min_ms": 0.32,
        "max_ms": 434.11
    },
    "latency_by_route": {
        "/api/v1/stats/overview": {
            "count": 5,
            "avg_ms": 1.69,
            "p50_ms": 1.57,
            "p95_ms": 2.29,
            "p99_ms": 2.29,
            "min_ms": 1.4,
            "max_ms": 2.29
        },
        "/api/v1/stats/categories": {
            "count": 5,
            "avg_ms": 3.65,
            "p50_ms": 3.55,
            "p95_ms": 4.78,
            "p99_ms": 4.78,
            "min_ms": 2.75,
            "max_ms": 4.78
        },
		{...},
		{...}
	}
}
```	

### GET /api/v1/books
Endpoint para obter a lista completa de livros disponíveis na base de dados.
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
```json
[
    {
        "id": 1,
        "titulo": "A Light in the Attic",
        "preco": 51.77,
        "rating": 3,
        "disponibilidade": "In stock",
        "categoria": "Poetry",
        "imagem": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
        "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    },
    {
        "id": 2,
        "titulo": "Tipping the Velvet",
        "preco": 53.74,
        "rating": 1,
        "disponibilidade": "In stock",
        "categoria": "Historical Fiction",
        "imagem": "https://books.toscrape.com/media/cache/26/0c/260c6ae16bce31c8f8c95daddd9f4a1c.jpg",
        "url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
    },
    {...},
    {...}...
]
```

### GET /api/v1/books/search
Endpoint para buscar livros por título ou categoria.
- Não precisa de autenticação é um endpoint público.
- Parâmetros de consulta (query parameters):
  - `title` (opcional): termo para busca no título do livro.
  - `category` (opcional): nome da categoria para filtrar os livros.

#### Parâmetros de exemplo
```bash
Sem parâmetros, filtra todos os livros: `http://127.0.0.1:8000/api/v1/books/search?title=&category=`
Filtro apenas por título: `http://127.0.0.1:8000/api/v1/books/search?title=A Light&category=`
Filtro apenas por categoria: `http://127.0.0.1:8000/api/v1/books/search?title=&category=Travel`
Filtro por título e categoria: `http://127.0.0.1:8000/api/v1/books/search?title=A Light&category=Poetry`
```
![Parâmetros de exemplo](doc/booksSearchParams.png)

#### Resposta
`http://127.0.0.1:8000/api/v1/books/search?title=A Light&category=`
```json
{
    "total": 1,
    "items": [
        {
            "id": 1,
            "titulo": "A Light in the Attic",
            "preco": 51.77,
            "rating": 3,
            "disponibilidade": "In stock",
            "categoria": "Poetry",
            "imagem": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
            "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        }
    ]
}
```

### GET /api/v1/books/{id}
Endpoint para obter detalhes de um livro específico pelo seu ID.
- Não precisa de autenticação é um endpoint público.
- Parâmetros de caminho (path parameters):
  - `id`: ID do livro a ser consultado.

#### Parâmetros de exemplo
```bash
Buscar o ID 100: http://127.0.0.1:8000/api/v1/books/10
```

#### Resposta
```json
{
    "id": 100,
    "titulo": "In the Country We Love: My Family Divided",
    "preco": 22.0,
    "rating": 4,
    "disponibilidade": "In stock",
    "categoria": "Nonfiction",
    "imagem": "https://books.toscrape.com/media/cache/fe/ea/feeafd2ad7b3077f8e74cbb1da9e3c7d.jpg",
    "url": "https://books.toscrape.com/catalogue/in-the-country-we-love-my-family-divided_901/index.html"
}
```

### GET /api/v1/books/top-rated
Endpoint para obter os livros com melhor avaliação (rating, que no caso é *5*).
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.

#### Resposta
```json
[
    {
        "id": 5,
        "titulo": "Sapiens: A Brief History of Humankind",
        "preco": 54.23,
        "rating": 5,
        "disponibilidade": "In stock",
        "categoria": "History",
        "imagem": "https://books.toscrape.com/media/cache/be/a5/bea5697f2534a2f86a3ef27b5a8c12a6.jpg",
        "url": "https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html"
    },
    {
        "id": 13,
        "titulo": "Set Me Free",
        "preco": 17.46,
        "rating": 5,
        "disponibilidade": "In stock",
        "categoria": "Young Adult",
        "imagem": "https://books.toscrape.com/media/cache/5b/88/5b88c52633f53cacf162c15f4f823153.jpg",
        "url": "https://books.toscrape.com/catalogue/set-me-free_988/index.html"
    },
    {...},
    {...}...
]
```

### /api/v1/books/price-range
Endpoint para filtrar livros por faixa de preço.
- Não precisa de autenticação é um endpoint público.
- Parâmetros de consulta (query parameters):
  - `min_price` (obrigatório): preço mínimo.
  - `max_price` (obrigatório): preço máximo.
#### Parâmetros de exemplo
```bash
Filtrando por preço entre 20 e 27: `http://127.0.0.1:8000/api/v1/books/price-range?min=20&max=27`
```

#### Resposta
```json
[
    {
        "id": 6,
        "titulo": "The Requiem Red",
        "preco": 22.65,
        "rating": 1,
        "disponibilidade": "In stock",
        "categoria": "Young Adult",
        "imagem": "https://books.toscrape.com/media/cache/68/33/68339b4c9bc034267e1da611ab3b34f8.jpg",
        "url": "https://books.toscrape.com/catalogue/the-requiem-red_995/index.html"
    },
    {
        "id": 9,
        "titulo": "The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics",
        "preco": 22.6,
        "rating": 4,
        "disponibilidade": "In stock",
        "categoria": "Default",
        "imagem": "https://books.toscrape.com/media/cache/66/88/66883b91f6804b2323c8369331cb7dd1.jpg",
        "url": "https://books.toscrape.com/catalogue/the-boys-in-the-boat-nine-americans-and-their-epic-quest-for-gold-at-the-1936-berlin-olympics_992/index.html"
    },
    {...},
    {...}...
] 
```

### GET /api/v1/books/categories
Endpoint para obter a lista de categorias disponíveis na base de dados.
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
```bash
[
    "Academic",
    "Add a comment",
    "Adult Fiction",
    "Art",
    "Autobiography",
    "Biography",
    "Business",
    "Childrens",
    "Christian",
    "Christian Fiction",
    "Classics",
    "Contemporary",
    "Crime",
    "Cultural",
    "Default",
    "Erotica",
    "Fantasy",
    "Fiction",
    "Food and Drink",
    "Health",
    "Historical",
    "Historical Fiction",
    "History",
    "Horror",
    "Humor",
    "Music",
    "Mystery",
    "New Adult",
    "Nonfiction",
    "Novels",
    "Paranormal",
    "Parenting",
    "Philosophy",
    "Poetry",
    "Politics",
    "Psychology",
    "Religion",
    "Romance",
    "Science",
    "Science Fiction",
    "Self Help",
    "Sequential Art",
    "Short Stories",
    "Spirituality",
    "Sports and Games",
    "Suspense",
    "Thriller",
    "Travel",
    "Unknown",
    "Womens Fiction",
    "Young Adult"
]
```

### GET /api/v1/stats/overview
Endpoint para obter estatísticas gerais sobre os livros.
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
```json
{
    "total_livros": 1000,
    "preco_medio": 35.07,
    "distribuicao_ratings": {
        "3": 203,
        "1": 226,
        "4": 179,
        "5": 196,
        "2": 196
    }
}
```

### GET /api/v1/stats/categories
Endpoint para obter estatísticas por categoria.
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
```bash
{
    "Poetry": {
        "count": 19,
        "min_price": 14.19,
        "max_price": 57.31,
        "avg_price": 35.97,
        "total_price": 683.51
    },
    "Historical Fiction": {
        "count": 26,
        "min_price": 16.62,
        "max_price": 55.55,
        "avg_price": 33.64,
        "total_price": 874.75
    },
    "Fiction": {
        "count": 65,
        "min_price": 10.6,
        "max_price": 59.98,
        "avg_price": 36.07,
        "total_price": 2344.33
    },
    {...},
    {...}...
}
```

### POST /api/v1/scraping/trigger
Endpoint para disparar o processo de scraping em background.
- Requer autenticação (somente usuário `admin`).
- Parâmetro de máximo de páginas a serem raspadas (opcional):
  - `max_pages`: número máximo de páginas a serem raspadas (padrão: `None`, raspagem completa).
#### Auth
Adicione o token de acesso no header:
```bash
Auth Type: Bearer Token
Token: <access_token>
```
![authTokenConfig](./doc/booksScrapingAuth.png)
#### Params
- Exemplo de requisição com parâmetro `max_pages` definido como `5`:
`http://127.0.0.1:8000/api/v1/scraping/trigger?max_pages=5`

![paramsConfig](./doc/booksScrapingParams.png)

```bash
`Key`: max_pages
`Value`: 5
```

#### Resposta

```json
{
    "status": "accepted",
    "message": "Scraping disparado em background"
}
```

### GET /api/v1/ml/features
Endpoint para obter as features utilizadas no modelo de machine learning.
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
```json
[
    {
        "id": 1,
        "categoria": "Poetry",
        "in_stock": 1,
        "rating": 3
    },
    {
        "id": 2,
        "categoria": "Historical Fiction",
        "in_stock": 1,
        "rating": 1
    },
	{...},
	{...}...
]
```

### GET /api/v1/ml/training-data
Endpoint para obter os dados de treinamento (features X e target y) para o modelo de machine
- Não precisa de autenticação é um endpoint público.
- Não precisa de parâmetros.
#### Resposta
```json
{
	"X": [
		{
			"categoria": "Poetry",
			"in_stock": 1,
			"rating": 3
		},
		{
			"categoria": "Historical Fiction",
			"in_stock": 1,
			"rating": 1
		},
		{...},
		{...}...
	],
	"y": [
		51.77,
		53.74,
		{...},
		{...}...
	]
}
```
### POST /api/v1/ml/predictions
Endpoint para receber predições de preços e registrá-las em memória.
- Não precisa de autenticação é um endpoint público.
- Body: lista de features para predição.
#### Body
```json
[
	{
  		"book_id": 10,
  		"price_prediction": 42.9,
  		"model_name": "baseline-v1"
	}
]
```
#### Resposta
```json
{
    "status": "ok",
    "saved": {
        "book_id": 10,
        "price_prediction": 42.9,
        "model_name": "baseline-v1"
    }
}
```

## Scraping
* O scraper é implementado em `scripts/scraper.py`.
* Ele coleta os dados do site e salva em `data/books.csv`.
* Pode ser executado de duas formas:
  * Manualmente: `python -m scripts.scraper`
  * Via API: POST `/api/v1/scraping/trigger` (admin)

## Estatísticas
* A API oferece endpoints para estatísticas:
  * /stats/overview: total de livros, preço médio, distribuição de ratings
    * GET `/api/v1/stats/overview`: estatísticas gerais.
  * /stats/categories: estatísticas por categoria
    * GET `/api/v1/stats/categories`: estatísticas detalhadas por categoria.

## Scripts e Utilitários
* Logger: todos os logs estão centralizados no utils/logger.py
  * Configuração de log rotativo com Loguru.
* CSV de livros: salvo em data/books.csv
* Banco de usuários: SQLite em data/auth.db

## Logs
Modelo de logs implementado com Loguru em `utils/logger.py`.
* Logs são salvos em `logs/app.log` quando executado localmente.
* Logs são enviados para stdout quando implantado em Render.com, podendo ser visualizados no painel de controle da Render.
* Todos os endpoints registram logs de requisições, respostas e erros.
![Exemplo de logs](./doc/logExemple.png)

## Dashboard de Insights
* Implementado com Streamlit em `dashboard/insights_dashboard.py`.
* Executar com: `streamlit run dashboard/insights_dashboard.py`