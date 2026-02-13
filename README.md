<div align="center">

# Fastuator

[![CI](https://github.com/fastuator/fastuator/actions/workflows/test.yml/badge.svg)](https://github.com/fastuator/fastuator/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[![Fastuator](https://img.shields.io/pypi/v/fastuator?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/fastuator/)
<!--[![Downloads](https://img.shields.io/pypi/dm/fastuator?style=for-the-badge)](https://pypistats.org/packages/fastuator)-->
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?style=for-the-badge)](https://github.com/fastuator/fastuator)

</div>

<div align="center">
  <img src="https://img.shields.io/github/stars/fastuator/fastuator?style=social" alt="GitHub stars">
  <br><br>
  
  **Production-ready monitoring toolkit for FastAPI applications.**  
  Kubernetes probes, Prometheus metrics, and health checks in **one line**.
  
</div>

## ✨ Features

- 🏥 **Health Checks**: Aggregated health status with customizable checks
- 🔍 **K8s Probes**: Built-in liveness and readiness endpoints
- 📊 **Prometheus Metrics**: Auto-instrumented HTTP metrics
- ℹ️ **System Info**: Build version and platform details
- 🎯 **Zero Config**: Works out of the box with sensible defaults
- ⚡ **100% Test Coverage**: Battle-tested and production-ready

## 📦 Installation

```bash
pip install fastuator
```

## 🚀 Quick Start

```python
from fastapi import FastAPI
from fastuator import Fastuator

app = FastAPI()
Fastuator(app)  # That's it!
```

**Available Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /fastuator/health` | Aggregated health status with optional details |
| `GET /fastuator/liveness` | Kubernetes liveness probe (critical checks only) |
| `GET /fastuator/readiness` | Kubernetes readiness probe (all dependencies) |
| `GET /fastuator/metrics` | Prometheus-compatible metrics |
| `GET /fastuator/info` | Application and system information |


## 📖 Usage

### Basic Setup

```python
from fastapi import FastAPI
from fastuator import Fastuator

app = FastAPI()

# Use default configuration
Fastuator(app)

# Custom prefix
Fastuator(app, prefix="/monitoring")
```

### Custom Health Checks

```python
from fastuator import Fastuator

app = FastAPI()

# Define custom health checks
async def database_health():
    try:
        # Check database connection
        await db.execute("SELECT 1")
        return {"status": "UP", "database": "connected"}
    except Exception as e:
        return {"status": "DOWN", "database": str(e)}

async def redis_health():
    try:
        await redis.ping()
        return {"status": "UP", "redis": "connected"}
    except Exception:
        return {"status": "DOWN", "redis": "unreachable"}

# Register custom checks
Fastuator(
    app,
    health_checks=[database_health, redis_health],
    readiness_checks=[database_health, redis_health],
    liveness_checks=[],  # No external dependencies for liveness
)
```

### Health Check Response

**Without details:**
```bash
curl http://localhost:8000/fastuator/health
```
```json
{"status": "UP"}
```

**With details:**
```bash
curl http://localhost:8000/fastuator/health?show_details=true
```
```json
{
  "status": "UP",
  "components": {
    "check_0": {
      "status": "UP",
      "cpu_percent": 45.2
    },
    "check_1": {
      "status": "UP",
      "memory_percent": 62.1,
      "memory_available_mb": 4096
    }
  }
}
```

## ☸️ Kubernetes Integration

### Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /fastuator/liveness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /fastuator/readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📊 Prometheus Metrics

Fastuator automatically collects the following metrics:

- `http_requests_total`: Total HTTP requests (counter)
- `http_request_duration_seconds`: Request duration histogram
- `app_health_status`: Health status gauge (1=UP, 0=DOWN)

**Scrape configuration:**
```yaml
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/fastuator/metrics'
```

## ⚙️ Configuration

```python
Fastuator(
    app,
    prefix="/fastuator",              # URL prefix for all endpoints
    health_checks=[...],               # List of health check functions
    liveness_checks=[...],             # Checks for liveness probe
    readiness_checks=[...],            # Checks for readiness probe
    enable_metrics=True,               # Enable Prometheus metrics
)
```

## 🧪 Built-in Health Checks

Fastuator includes these health checks by default:

- **CPU Usage**: Reports DOWN if CPU > 90%
- **Memory Usage**: Reports DOWN if memory > 90%
- **Disk Usage**: Reports DOWN if disk > 90%

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest --cov=fastuator`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Inspired by [Spring Boot Actuator](https://docs.spring.io/spring-boot/docs/current/reference/html/actuator.html).

## 📚 Related Projects

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for Python
- [Prometheus](https://prometheus.io/) - Monitoring and alerting toolkit
- [Kubernetes](https://kubernetes.io/) - Container orchestration platform

<div align="center">
  
**⭐ Loved this library? Star us to support!**
  
[![Star History Chart](https://api.star-history.com/svg?repos=fastuator/fastuator)](https://star-history.com/#fastuator/fastuator&Date)

</div>
