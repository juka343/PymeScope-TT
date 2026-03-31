## Backend

El backend de PymeScope-TT representa la capa de lógica y control del sistema.  
Su función principal es procesar, validar y analizar la información financiera que recibe del frontend, exponiendo dicha lógica a través de una API.


### Tecnología utilizada

- Lenguaje: Python
- Framework: FastAPI
- Servidor: Uvicorn

FastAPI permite:
- Desarrollo rápido de APIs
- Validación automática de datos
- Documentación interactiva automática
- Separación clara de responsabilidades

---
Credenciales → core/config.py

Conexiones → clients/

Lógica → services/

Endpoints → api/

---

### Descripción de carpetas


- **main.py**  
  Inicializa la aplicación FastAPI y registra los endpoints.

- **api/**  
  Contiene los endpoints de la API. Se encarga de recibir solicitudes y devolver respuestas, sin lógica compleja.

  La carpeta api/routes contiene la definición de los endpoints del backend.
  Aquí se especifica qué rutas expone la API, qué tipo de petición reciben (GET, POST, etc.) y qué información regresan.

- **clients/** 
  Aquí va el código que se conecta a servicios externos.

- **services/**  
  Contiene la lógica del negocio, algoritmos financieros y reglas del sistema.
  También aquí USAMOS los clientes de servicios externos (lógica).

- **models/**  
  Define las estructuras de datos para validar entradas y salidas.

- **core/**  
  Contiene configuración global y manejo de variables de entorno. Aqui va TODO lo sensible.

- **__init__.py**

  __init__.py convierte carpetas en paquetes

    - Permite imports limpios y seguros

    - Por eso está en todas las carpetas del backend

    - Puede estar vacío y aún así cumplir su función

---

### Entorno virtual

El backend utiliza un entorno virtual (`venv`) para aislar dependencias y asegurar que todos los desarrolladores trabajen con las mismas versiones de librerías.

Las dependencias del proyecto se documentan en el archivo `requirements.txt`.

---

### Endpoint base

El backend incluye un endpoint de verificación: GET /health
 
Este endpoint permite comprobar que la API está activa y funcionando correctamente. Es útil para pruebas, diagnóstico e integración.

---

### Documentación automática

FastAPI genera documentación automática accesible en: http://127.0.0.1:8000/docs


Esta documentación muestra:
- Endpoints disponibles
- Esquemas de datos
- Pruebas interactivas

---


### Estado actual

- Backend inicializado y funcional
- Estructura base creada
- API operativa con FastAPI
- Preparado para agregar modelos financieros y endpoints reales

