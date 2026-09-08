# Microservice

A simple REST API microservice.

## Setup

```bash
pip install -r requirements.txt
python service/main.py
```

## API Endpoints

- GET /health - Health check
- GET /api/users - List users
- POST /api/users - Create user
- GET /api/users/:id - Get user by ID

## Configuration

Edit `config/settings.py` to configure the service.
