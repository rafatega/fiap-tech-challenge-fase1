# FIAP Tech Challenge - Fase 1

API desenvolvida para realizar scraping de livros do site [Books to Scrape](https://books.toscrape.com) e disponibilizar os dados através de uma API RESTful com autenticação via JWT.

---

## Índice

- [FIAP Tech Challenge - Fase 1](#fiap-tech-challenge---fase-1)
  - [Índice](#índice)
  - [Tecnologias Utilizadas](#tecnologias-utilizadas)
  - [Estrutura do Projeto](#estrutura-do-projeto)
  - [Como Executar](#como-executar)
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
    - [GET /api/v1/books](#get-apiv1books)
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
    - [GET /api/v1/categories](#get-apiv1categories)
      - [Resposta](#resposta-8)
    - [GET /api/v1/stats/overview](#get-apiv1statsoverview)
      - [Resposta](#resposta-9)
    - [GET /api/v1/stats/categories](#get-apiv1statscategories)
      - [Resposta](#resposta-10)
    - [POST /api/v1/scraping/trigger](#post-apiv1scrapingtrigger)
      - [Auth](#auth)
      - [Params](#params)
      - [Resposta](#resposta-11)

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
.
├── api/
│   ├── main.py              # Entrypoint da API FastAPI
│   ├── models.py            # Schemas Pydantic (dados, respostas)
│   ├── auth.py              # Lógica de autenticação e tokens
├── scripts/
│   └── scraper.py           # Web scraper do site de livros
├── utils/
│   └── logger.py            # Logger global configurado com Loguru
├── data/
│   └── books.csv            # Base de dados em CSV (scraping)
│   └── auth.db              # Banco de usuários (SQLite)
├── logs/
│   └── app.log              # Arquivo de log (rotativo)
├── requirements.txt         # Dependências do projeto
└── README.md                # Documentação principal

---

## Como Executar

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
| `GET`  | `/api/v1/books`             | Retorna todos os livros                |
| `GET`  | `/api/v1/books/search`      | Busca por título ou categoria          |
| `GET`  | `/api/v1/books/{id}`        | Consulta livro por ID                  |
| `GET`  | `/api/v1/books/top-rated`   | Lista livros com melhor rating         |
| `GET`  | `/api/v1/books/price-range` | Filtra livros por preço                |
| `GET`  | `/api/v1/categories`        | Lista categorias disponíveis           |
| `GET`  | `/api/v1/stats/overview`    | Estatísticas gerais dos livros         |
| `GET`  | `/api/v1/stats/categories`  | Estatísticas por categoria             |
| `POST` | `/api/v1/scraping/trigger`  | (admin) Dispara scraping em background |

### Run results
Todas APIs foram testadas utilizando o Postman. Abaixo estão os resultados da execução dos testes, retornando status code 200 para todas as requisições:
```json
{
	"id": "39f76c63-0ab3-4f20-8d23-4baf8d469dec",
	"name": "Tech Challenge Fase 1",
	"timestamp": "2026-01-18T15:16:50.784Z",
	"collection_id": "45464934-fd1ead76-9d28-405b-95a7-e368f69ffe6a",
	"folder_id": 0,
	"environment_id": "0",
	"totalPass": 0,
	"delay": 0,
	"persist": true,
	"status": "finished",
	"startedAt": "2026-01-18T15:16:49.160Z",
	"totalFail": 0,
	"results": [
		{
			"id": "9bf068f2-49a2-4c60-85a4-364cc6c04467",
			"name": "/api/v1/auth/login",
			"url": "http://127.0.0.1:8000/api/v1/auth/login",
			"time": 13,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				13
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "b43f263d-69eb-433f-aa6b-fc016cd25167",
			"name": "/api/v1/auth/refresh",
			"url": "http://127.0.0.1:8000/api/v1/auth/refresh",
			"time": 4,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				4
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "60efc129-e0b8-4e6d-a564-ce9a3c8ad93e",
			"name": "/api/v1/health",
			"url": "http://127.0.0.1:8000/api/v1/health",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "c2688b65-bbf3-43f4-915a-f0523b6b1c8b",
			"name": "/api/v1/books",
			"url": "http://127.0.0.1:8000/api/v1/books",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "ec44a693-2533-409f-a45b-0d8c083b91b5",
			"name": "/api/v1/books/search",
			"url": "http://127.0.0.1:8000/api/v1/books/search\n?title=&category=",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "d0bb8156-13e2-43e7-ad1e-c159a368837e",
			"name": "/api/v1/books/{id}",
			"url": "http://127.0.0.1:8000/api/v1/books/10\n",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "5017ee22-bc8e-4d6f-add8-7d882e21fe55",
			"name": "/api/v1/books/top-rated",
			"url": "http://127.0.0.1:8000/api/v1/books/top-rated",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "68653e2b-fba4-454b-86b7-0b73996c5888",
			"name": "/api/v1/books/price-range",
			"url": "http://127.0.0.1:8000/api/v1/books/price-range",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "5e8160e2-028d-4d87-aa59-bd1a0f6f3347",
			"name": "/api/v1/categories",
			"url": "http://127.0.0.1:8000/api/v1/categories\n",
			"time": 2,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				2
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "ebe1d5b8-5d46-4d43-8b81-9eb3790d9018",
			"name": "/api/v1/stats/overview",
			"url": "http://127.0.0.1:8000/api/v1/stats/overview\n",
			"time": 2,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				2
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "89d07bf4-31e8-4bf0-8cf7-4575ab31aa2a",
			"name": "/api/v1/stats/categories",
			"url": "http://127.0.0.1:8000/api/v1/stats/categories\n",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		},
		{
			"id": "cb6df7da-df40-4814-b87b-1b4e870bf547",
			"name": "/api/v1/scraping/trigger",
			"url": "http://127.0.0.1:8000/api/v1/scraping/trigger?max_pages=50",
			"time": 3,
			"responseCode": {
				"code": 200,
				"name": "OK"
			},
			"tests": {},
			"testPassFailCounts": {},
			"times": [
				3
			],
			"allTests": [
				{}
			]
		}
	],
	"count": 1,
	"totalTime": 45,
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
				"id": "cb6df7da-df40-4814-b87b-1b4e870bf547",
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

### GET /api/v1/categories
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