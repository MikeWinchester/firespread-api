# 🔥 FireSpread Simulator Backend

Backend API para simulación de propagación de incendios forestales utilizando el modelo de Rothermel.

## 🏗️ Características Principales

- **Modelo de Rothermel**: Implementación completa del modelo físico de propagación de incendios
- **API REST**: Endpoints completos para gestión de simulaciones y escenarios
- **WebSocket en Tiempo Real**: Updates en vivo del estado de las simulaciones
- **Múltiples Tipos de Vegetación**: Bosque, pastizal, matorral, agrícola, urbano
- **Factores Ambientales**: Viento, humedad, pendiente del terreno

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.11+
- pip
- Docker (opcional)

### Instalación Local

```bash
# Clonar el repositorio
git clone <repository-url>
cd firespread-backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python run.py
```

### Usando Docker

```bash
# Construir y ejecutar con Docker Compose
docker-compose up --build

# O solo ejecutar si ya está construido
docker-compose up
```

### Usando Docker directamente

```bash
# Construir la imagen
docker build -t firespread-backend .

# Ejecutar el contenedor
docker run -p 8000:8000 firespread-backend
```

## 📖 Documentación de la API

Una vez que el servidor esté ejecutándose, la documentación interactiva estará disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principales

#### Salud del Sistema
- `GET /api/health` - Estado del sistema
- `GET /api/health/detailed` - Estado detallado con estadísticas

#### Simulaciones
- `POST /api/simulations` - Crear nueva simulación
- `POST /api/simulations/{id}/start` - Iniciar simulación
- `POST /api/simulations/{id}/pause` - Pausar simulación
- `POST /api/simulations/{id}/stop` - Detener simulación
- `GET /api/simulations/{id}` - Obtener estado de simulación
- `GET /api/simulations` - Listar todas las simulaciones
- `DELETE /api/simulations/{id}` - Eliminar simulación

#### Escenarios
- `GET /api/scenarios` - Listar escenarios
- `POST /api/scenarios` - Crear escenario
- `GET /api/scenarios/{id}` - Obtener escenario
- `PUT /api/scenarios/{id}` - Actualizar escenario
- `DELETE /api/scenarios/{id}` - Eliminar escenario

#### WebSocket
- `WS /ws/simulations/{id}` - Updates en tiempo real de simulación

## 🔧 Configuración

### Variables de Entorno

```bash
# Configuración del servidor
ENVIRONMENT=development|production|testing
DEBUG=true|false
HOST=0.0.0.0
PORT=8000

# Configuración de simulación
MAX_SIMULATIONS=100
MAX_CONCURRENT_SIMULATIONS=10
MAX_SIMULATION_TIME=600
SIMULATION_STEP_INTERVAL=1.0
GRID_RESOLUTION=0.01

# Configuración de logging
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
LOG_FORMAT=json|text

# WebSocket
WEBSOCKET_HEARTBEAT_INTERVAL=30
```

### Archivo .env

Crea un archivo `.env` en la raíz del proyecto:

```env
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
MAX_SIMULATIONS=50
MAX_CONCURRENT_SIMULATIONS=5
```

## 🧪 Ejemplo de Uso

### Crear una Simulación

```bash
curl -X POST "http://localhost:8000/api/simulations" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "vegetationType": "forest",
      "windSpeed": 15.5,
      "windDirection": 270,
      "humidity": 45,
      "slope": 10
    },
    "ignitionPoints": [
      {
        "id": "ignition_001",
        "lat": -34.6037,
        "lng": -58.3816,
        "timestamp": 1640995200
      }
    ]
  }'
```

### Iniciar la Simulación

```bash
curl -X POST "http://localhost:8000/api/simulations/{simulation_id}/start"
```

### Conectar WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/simulations/{simulation_id}');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Simulation update:', data);
    // Actualizar UI con datos de la simulación
};
```

## 🔬 Modelo de Rothermel

El backend implementa el modelo de Rothermel para calcular la velocidad de propagación del fuego basado en:

### Ecuación Principal

```
R = (I_R × ξ × φ_w × φ_s) / (ρ_b × ε × Q_ig)
```

Donde:
- **R**: Velocidad de propagación (m/min)
- **I_R**: Intensidad de reacción (kW/m²)
- **ξ**: Factor de flujo propagante
- **φ_w**: Factor de influencia del viento
- **φ_s**: Factor de influencia de la pendiente
- **ρ_b**: Densidad de la carga de combustible (kg/m³)
- **ε**: Fracción del combustible disponible
- **Q_ig**: Energía requerida para la ignición (kJ/kg)

### Factores Considerados

1. **Propiedades del Combustible**: Tipo de vegetación, carga de combustible, humedad
2. **Condiciones Meteorológicas**: Velocidad y dirección del viento, humedad relativa
3. **Topografía**: Pendiente del terreno
4. **Estado del Fuego**: Intensidad, temperatura, tiempo de quema

## 📊 Tipos de Vegetación

| Tipo | Descripción | Características |
|------|-------------|-----------------|
| `forest` | Bosque | Alta carga combustible, retiene humedad |
| `grassland` | Pastizal | Combustible fino, se seca rápidamente |
| `shrubland` | Matorral | Carga media, combustión moderada |
| `agricultural` | Agrícola | Baja carga, residuos de cultivos |
| `urban` | Urbano | Combustible limitado, materiales mixtos |

## 🏗️ Arquitectura

```
firespread-backend/
├── app/
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración
│   ├── models/              # Modelos Pydantic
│   │   ├── simulation.py    # Modelos de simulación
│   │   └── scenario.py      # Modelos de escenarios
│   ├── core/                # Lógica de negocio
│   │   ├── rothermel.py     # Modelo de Rothermel
│   │   ├── simulation_engine.py  # Motor de simulación
│   │   └── simulation_manager.py # Gestor de simulaciones
│   ├── api/                 # Endpoints API
│   │   ├── routes/
│   │   │   ├── health.py    # Salud del sistema
│   │   │   ├── simulations.py # Simulaciones
│   │   │   ├── scenarios.py  # Escenarios
│   │   │   └── websockets.py # WebSockets
│   │   └── deps.py          # Dependencias
│   └── utils/
│       └── logging.py       # Configuración de logs
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Imagen Docker
├── docker-compose.yml      # Orquestación Docker
└── run.py                  # Punto de entrada
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/

# Tests específicos
pytest tests/test_rothermel.py
pytest tests/test_simulation.py
pytest tests/test_api.py
```

## 📈 Monitoreo y Logs

El sistema incluye logging detallado y métricas de rendimiento:

- **Logs de Simulación**: Progreso y estadísticas
- **Logs de WebSocket**: Conexiones y mensajes
- **Logs de Performance**: Tiempos de ejecución y recursos
- **Health Checks**: Estado del sistema

## 🔒 Seguridad

- **CORS**: Configurado para dominios específicos
- **Validación**: Validación estricta de inputs con Pydantic
- **Límites de Recursos**: Límites en número de simulaciones y recursos
- **Error Handling**: Manejo robusto de errores sin exposición de información sensible

## 🚀 Despliegue en Producción

### Usando Docker

```bash
# Producción con Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Variables de Entorno para Producción

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_HOSTS=["https://your-frontend-domain.com"]
MAX_SIMULATIONS=200
MAX_CONCURRENT_SIMULATIONS=20
```

### Consideraciones de Escalabilidad

- **Múltiples Instancias**: Usar un load balancer para múltiples instancias
- **Base de Datos**: Agregar PostgreSQL para persistencia
- **Cache**: Usar Redis para cache y sesiones
- **Monitoring**: Integrar con Prometheus/Grafana

## 🤝 Contribución

1. Fork el repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar bugs o solicitar features, por favor crear un issue en el repositorio.

## 📚 Referencias

- [Rothermel, R.C. 1972. A mathematical model for predicting fire spread](https://www.fs.fed.us/rm/pubs_int/int_rp115.pdf)
- [Anderson, H.E. 1982. Aids to determining fuel models for estimating fire behavior](https://www.fs.fed.us/rm/pubs_int/int_gtr122.pdf)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)