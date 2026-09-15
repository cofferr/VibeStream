VibeStream - Plataforma de Streaming Musical
📖 Descripción

VibeStream es una plataforma moderna de streaming musical que permite a los usuarios descubrir, reproducir y gestionar música. Los artistas pueden subir su música y gestionar su contenido a través de un panel especializado.
🚀 Características Principales
Para Usuarios

    🔊 Reproducción de música en alta calidad

    🔍 Búsqueda avanzada de canciones, álbumes y artistas

    📚 Biblioteca personal con playlists

    👤 Perfiles de usuario personalizables

    📱 Interfaz responsive y moderna

Para Artistas

    🎤 Panel de artista para gestión de contenido

    📤 Subida de canciones y álbumes

    📊 Estadísticas de reproducción

    🎨 Personalización de perfil de artista

🛠️ Tecnologías Utilizadas
Backend

    Go (Gin) - Servicios de autenticación y streaming

    Python (FastAPI) - Microservicios de contenido

    PostgreSQL - Base de datos principal

    RabbitMQ - Message broker para comunicación entre servicios

    JWT - Autenticación y autorización

Frontend

    React con Vite

    Tailwind CSS - Estilos

    Framer Motion - Animaciones

    React Hook Form - Formularios

📋 Prerrequisitos

    Docker y Docker Compose

    Git

    4GB de RAM mínimo

    2GB de espacio libre en disco

🐳 Instalación con Docker
1. Clonar el repositorio
bash

git clone <url-del-repositorio>
cd streaming-backend

2. Configurar variables de entorno
bash

# Copiar el archivo de ejemplo
cp .env.example .env

# Editar las variables según tu entorno
nano .env

3. Levantar los servicios
bash

# Levantar todos los servicios
docker-compose build
docker-compose up 

# O levantar servicios específicos
docker-compose up -d auth-service streaming-service front_music_stm

4. Verificar que los servicios estén corriendo
bash

docker ps

Deberías ver los siguientes servicios:

    auth-service (puerto 8080)

    streaming-service (puerto 8001)

    content-service (puerto 8002)

    artist-service (puerto 8003)

    playlist-service (puerto 8004)

    history-service (puerto 8005)

    search-service (puerto 8006)

    subscription-service (puerto 8007)

    front_music_stm (puerto 5173)

    rabbitmq (puerto 15672)

5. Acceder a la aplicación

    Frontend: http://localhost:5173

    RabbitMQ Management: http://localhost:15672 (usuario: guest, contraseña: guest)

🎯 Guía de Uso
Primeros Pasos

    Registro de Usuario

        Ve a http://localhost:5173

        Haz clic en "Sign Up"

        Completa el formulario con:

            Username

            Email

            Fecha de nacimiento

            Contraseña

        Marca "Soy artista" si quieres acceso al panel de artista

    Inicio de Sesión

        Usa tu email y contraseña

        Serás redirigido automáticamente según tu rol

Para Usuarios Regulares
Navegación Principal

    Inicio: Descubre música recomendada

    Buscar: Encuentra música por nombre, artista o álbum

    Biblioteca: Tus playlists y música guardada

    Playlists: Gestiona tus listas de reproducción

Reproducción de Música

    Haz clic en cualquier canción para reproducirla

    Usa los controles del reproductor en la parte inferior

    Controla el volumen y progreso de la canción

    Salta a la siguiente/anterior canción

Gestión de Playlists

    Ve a "Playlists" en el menú lateral

    Crea una nueva playlist con el botón "+"

    Agrega canciones desde la biblioteca o resultados de búsqueda

Para Artistas
Acceso al Panel de Artista (activalo desde tu perfil)

    Inicia sesión con una cuenta de artista

    Ve a "Mi estudio" en el menú lateral

    Gestiona tu contenido desde el panel

Gestión de Álbumes

    Crea álbumes desde la sección "Mis Álbumes"

    Agrega canciones existentes o sube nuevas

🔧 Comandos Útiles
Docker
bash

# Ver estado de los contenedores
docker ps

# Ver logs de un servicio específico
docker-compose logs -f auth-service

# Reiniciar un servicio
docker-compose restart streaming-service

# Reconstruir y levantar
docker-compose up -d --build

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

Desarrollo
bash

# Acceder a un contenedor
docker exec -it streaming-service sh

# Ver logs en tiempo real
docker-compose logs -f

# Ver uso de recursos
docker stats

🗂️ Estructura del Proyecto
text
```bash
streaming-backend/
├── auth-service/          # Autenticación y usuarios (Go)
├── streaming-service/     # Streaming de audio (Go)
├── content-service/       # Gestión de contenido (Python)
├── artist-service/        # Panel de artista (Python)
├── playlist-service/      # Playlists (Python)
├── history-service/       # Historial de reproducción (Go)
├── search-service/        # Búsqueda (Python)
├── subscription-service/  # Suscripciones (Python)
├── frontend/              # Aplicación React
├── docker-compose.yml     # Orquestación de contenedores
└── .env                   # Variables de entorno
```
