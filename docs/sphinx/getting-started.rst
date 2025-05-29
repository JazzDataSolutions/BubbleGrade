Primeros Pasos
==============

Esta guía te ayudará a poner en marcha BubbleGrade rápidamente para desarrollo o producción.

Prerequisites
-------------

Before you begin, ensure you have the following installed:

**Software Requerido**

- **Docker Desktop** 4.0+ con Docker Compose
- Al menos **4GB de RAM** disponibles para los contenedores
- **Puertos 5173, 8080, 8090, 5432** libres

**Optional for Development**

- **Node.js** 18+ y npm (para desarrollo frontend)
- **Python** 3.11+ (para desarrollo del API)
- **Go** 1.22+ (para desarrollo del servicio OMR)

Installation
------------

Método 1: Docker Compose (Recomendado)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the fastest way to get BubbleGrade running:

.. code-block:: bash

   # Clonar el repositorio
   git clone <url-del-repositorio>
   cd BubbleGrade

   # Iniciar todos los servicios
   docker compose -f compose.micro.yml up --build

   # Access the application
   open http://localhost:5173

Método 2: Servicios Individuales
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For development purposes, you may want to run services individually:

**Iniciar la Base de Datos**

.. code-block:: bash

   docker run --name bubblegrade-db \
     -e POSTGRES_USER=omr \
     -e POSTGRES_PASSWORD=omr \
     -e POSTGRES_DB=omr \
     -p 5432:5432 \
     -d postgres:16-alpine

**Start OMR Service**

.. code-block:: bash

   cd services/omr
   docker build -t bubblegrade-omr .
   docker run -p 8090:8090 bubblegrade-omr

**Start API Service**

.. code-block:: bash

   cd services/api
   docker build -t bubblegrade-api .
   docker run -p 8080:8080 \
     -e DATABASE_URL=postgresql+asyncpg://omr:omr@host.docker.internal/omr \
     -e OMR_URL=http://host.docker.internal:8090/grade \
     bubblegrade-api

**Start Frontend**

.. code-block:: bash

   cd services/frontend
   docker build -t bubblegrade-frontend .
   docker run -p 5173:80 bubblegrade-frontend

Verification
------------

Una vez que todos los servicios estén activos, verifica la instalación:

**Verificar estado de los servicios**

.. code-block:: bash

  # Verificación de salud del API
  curl http://localhost:8080/health

  # Verificación de salud del servicio OMR
  curl http://localhost:8090/health

Expected responses:

.. code-block:: json

   # API Response
   {
     "status": "healthy",
     "service": "api",
     "database": "connected"
   }

   # OMR Response
   {
     "status": "healthy",
     "service": "omr"
   }

**Access the Web Interface**

1. Open your browser to http://localhost:5173
2. You should see the BubbleGrade interface with a drag-and-drop zone
3. The interface should display "Drop your bubble sheets here"

**Check Docker Services**

.. code-block:: bash

   # List running containers
   docker compose -f compose.micro.yml ps

You should see all four services running:

.. code-block:: text

   NAME                     COMMAND                  SERVICE    STATUS
   bubblegrade-frontend-1   "/docker-entrypoint.…"   frontend   Up
   bubblegrade-api-1        "uvicorn app.main:ap…"   api        Up
   bubblegrade-omr-1        "./omr"                  omr        Up
   bubblegrade-db-1         "docker-entrypoint.s…"   db         Up

First Test
----------

Let's perform a quick test to ensure everything is working:

**Prepare Test Data**

If you don't have a bubble sheet image, you can create a simple test image or download one from the internet. The system accepts JPG and PNG formats.

**Upload and Process**

1. **Navigate to the Interface**
   
   Open http://localhost:5173 in your browser

2. **Upload a File**
   
   - Drag and drop an image file onto the drop zone, or
   - Click "Choose Files" to select a file

3. **Monitor Processing**
   
   - Watch the real-time status updates
   - The status should change from "QUEUED" → "PROCESSING" → "COMPLETED"

4. **View Results**
   
   - Once complete, you'll see the score and detected answers
   - Click "Export Excel" to download detailed results

**Expected Behavior**

- File upload should be immediate
- Processing typically takes 5-15 seconds depending on image size
- WebSocket updates should show real-time progress
- Excel export should download a formatted spreadsheet

Troubleshooting
---------------

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Services Won't Start**

.. code-block:: bash

   # Check port conflicts
   lsof -i :5173 -i :8080 -i :8090 -i :5432

   # Stop conflicting services
   docker compose -f compose.micro.yml down

   # Restart with fresh containers
   docker compose -f compose.micro.yml up --build --force-recreate

**Database Connection Issues**

.. code-block:: bash

   # Check database is running
   docker compose -f compose.micro.yml logs db

   # Test database connection
   docker compose -f compose.micro.yml exec db psql -U omr -d omr -c "SELECT 1;"

**API Not Responding**

.. code-block:: bash

   # Check API logs
   docker compose -f compose.micro.yml logs api

   # Verify API container is healthy
   docker compose -f compose.micro.yml exec api curl localhost:8080/health

**OMR Service Issues**

.. code-block:: bash

   # Check OMR service logs
   docker compose -f compose.micro.yml logs omr

   # Test OMR service directly
   curl -X POST http://localhost:8090/grade \
     -F "file=@test-image.jpg"

**Frontend Loading Issues**

.. code-block:: bash

   # Check frontend logs
   docker compose -f compose.micro.yml logs frontend

   # Verify nginx configuration
   docker compose -f compose.micro.yml exec frontend nginx -t

Memory and Performance Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Insufficient Memory**

If you encounter out-of-memory errors:

.. code-block:: bash

   # Check Docker memory allocation
   docker system df
   docker system prune

   # Increase Docker memory limit in Docker Desktop settings
   # Recommended: 4GB minimum, 8GB preferred

**Slow Processing**

For better performance:

.. code-block:: bash

   # Reduce image size before upload
   # Ensure sufficient CPU cores allocated to Docker
   # Consider scaling OMR service for high load:
   docker compose -f compose.micro.yml up -d --scale omr=3

Getting Help
-----------

If you encounter issues not covered here:

1. **Check the Logs**
   
   .. code-block:: bash
   
      # View all service logs
      docker compose -f compose.micro.yml logs

2. **Review Documentation**
   
   - :doc:`development/setup` - Detailed development setup
   - :doc:`deployment/docker` - Advanced Docker configuration
   - :doc:`technical/troubleshooting` - Comprehensive troubleshooting

3. **Community Support**
   
   - GitHub Issues: Report bugs and request features
   - GitHub Discussions: Community Q&A
   - Documentation: Complete technical reference

Next Steps
----------

Now that BubbleGrade is running:

- :doc:`user-interface` - Learn about the web interface
- :doc:`uploading-scans` - Detailed upload and processing guide
- :doc:`api/overview` - Explore the API capabilities
- :doc:`development/setup` - Set up development environment