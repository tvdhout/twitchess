# Twitchess backend

### The backend consists of:
1. The website & API
2. A postgres database
3. Nginx webserver

The backend is containerized with docker-compose, 
check out the services in the [docker-compose.yml](docker-compose.yml) file.

The website and API are a python Flask application, served with uWSGI and Nginx.