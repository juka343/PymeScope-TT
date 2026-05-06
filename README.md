# PymeScope-TT

## Flujo de trabajo para colaboradores

Este proyecto está dividido en **frontend (Vue 3)** , **backend (Python + FastAPI)** y **Firebase** (Firestore + Storage + Functions).  
Durante el desarrollo, **ambos se ejecutan de forma simultánea**, cada uno en su propio servidor local.

---

## Requisitos previos
- git --version
- node -v
- npm -v
- python3 --version
Si algo no existe, se instala antes de seguir.

## Versiones requeridas

- Python 3.13.x
- pip 25.0.1 (viene ya con python)
- Node 24.x (LTS)
- npm 11.6.2

## Rama de trabajo
El desarrollo se realiza sobre la rama develop o ramas derivadas de ella.

git checkout develop
git pull origin develop

Para comenzar una nueva tarea:

git checkout -b nombre-de-la-tarea

## Frontend
- cd frontend
- npm install
- npm run dev
El frontend se ejecuta en: http://localhost:5173

### Variables de entorno (frontend)
Crear `frontend/.env` (no se sube) con:

```
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_API_BASE_URL=
```

## Backend (FastAPI)
- Abrir una nueva terminal
- cd backend
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- cp .env.example .env **(Este archivo NO SE SUBE AL REPOSITORIO)**
  
**Editar el archivo .env y colocar las credenciales necesarias (Azure, Firebase, etc.).**

-Correr el backend: uvicorn app.main:app --reload

Crear `.env` en la raiz del repo con:

## Instalación SDK Azure para python

pip install azure-ai-formrecognizer azure-core python-dotenv

```
FIREBASE_CREDENTIALS_PATH=
FIREBASE_STORAGE_BUCKET=
AZURE_DOC_INTEL_ENDPOINT=
AZURE_DOC_INTEL_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=
```

Correr el backend: uvicorn app.main:app --reload

El backend se ejecuta en: http://localhost:8000/docs

**Ambos deben estar activos para trabajar con el sistema completo.**

## Credenciales
- Cada colaborador debe tener su **service account JSON** fuera del repo.
- No subir llaves ni `.env` al repositorio.

## Flujo de trabajo recomendado

- Cambiar a develop
- Crear una rama nueva para la tarea
- Correr frontend y backend
- Realizar cambios
- Hacer commit con mensajes claros
- Subir la rama al repositorio
- Crear Pull Request hacia develop




