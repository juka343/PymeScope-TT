# PymeScope-TT

## Flujo de trabajo para colaboradores

Este proyecto está dividido en **frontend (Vue 3)** , **backend (Python + FastAPI)** y **Firebase** (pendiente).  
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

## Backend (FastAPI)
- Abrir una nueva terminal
- cd backend
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- cp .env.example .env **(Este archivo NO SE SUBE AL REPOSITORIO)**
  
**Editar el archivo .env y colocar las credenciales necesarias (Azure, Firebase, etc.).**

-Correr el backend: uvicorn app.main:app --reload

El backend se ejecuta en: http://localhost:8000/docs

**Ambos deben estar activos para trabajar con el sistema completo.**

## Flujo de trabajo recomendado

- Cambiar a develop
- Crear una rama nueva para la tarea
- Correr frontend y backend
- Realizar cambios
- Hacer commit con mensajes claros
- Subir la rama al repositorio
- Crear Pull Request hacia develop




