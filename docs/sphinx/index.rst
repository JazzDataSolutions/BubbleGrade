🫧 Documentación de BubbleGrade
==============================

Bienvenido a BubbleGrade, un sistema avanzado de **Reconocimiento Óptico de Marcas (OMR)** diseñado para la calificación automatizada de formularios de opción múltiple.

.. image:: _static/bubblegrade-banner.png
   :alt: BubbleGrade Banner
   :align: center

**BubbleGrade** combines modern microservices architecture with the power of OpenCV computer vision, real-time WebSocket communication, and beautiful React interfaces to provide a production-ready solution for educational institutions.

Features
--------

🎯 **Capacidades Principales**
   - Real-time bubble detection using OpenCV and Hough Circle Transform
   - Drag-and-drop file upload with instant processing feedback
   - Live progress updates via WebSocket connections
   - Professional Excel export with detailed results and formatting
   - PostgreSQL database for persistent scan history
   - RESTful API with comprehensive endpoints

🏗️ **Arquitectura**
   - **Clean Architecture** with SOLID principles implementation
   - **Microservices design** with independent, scalable services
   - **Container-first** approach with Docker Compose orchestration
   - **Health checks** and service dependency management
   - **Production-ready** with proper logging, error handling, and monitoring
   - **Domain-driven design** with clear separation of concerns

🎨 **Experiencia de Usuario**
   - Modern React interface with TypeScript and Vite
   - Responsive design that works on desktop and mobile
   - Real-time status updates during scan processing
   - Beautiful gradient UI with smooth animations

Quick Start
-----------

.. code-block:: bash

   # Clonar el repositorio
   git clone <url-del-repositorio>
   cd BubbleGrade

   # Iniciar todos los servicios
   docker compose -f compose.micro.yml up --build

   # Abrir la aplicación
   open http://localhost:5173

System Architecture
------------------

.. mermaid::

   graph TB
       subgraph "Client Layer"
           Browser[Web Browser]
       end
       
       subgraph "Docker Network: bubblegrade"
           Frontend[React Frontend<br/>:5173]
           API[FastAPI Backend<br/>:8080]
           OMR[Go OMR Service<br/>:8090]
           DB[(PostgreSQL<br/>:5432)]
       end
       
       Browser --> Frontend
       Frontend --> API
       API --> OMR
       API --> DB
       OMR --> API
       
       Frontend -.->|WebSocket| API

Service Details
--------------

+-------------+---------------------------+------+------------------+----------------------------------------+
| Servicio    | Tecnología                | Puerto | Propósito        | Características Clave                  |
+=============+===========================+======+==================+========================================+
| Frontend    | React 18 + Vite + TS     | 5173 | User Interface  | Drag-drop, real-time updates, responsive |
+-------------+---------------------------+------+------------------+----------------------------------------+
| API         | FastAPI + SQLAlchemy     | 8080 | Backend Logic   | REST endpoints, WebSocket, database ORM |
+-------------+---------------------------+------+------------------+----------------------------------------+
| OMR         | Go + OpenCV (gocv)       | 8090 | Image Processing| Circle detection, bubble analysis, scoring |
+-------------+---------------------------+------+------------------+----------------------------------------+
| Database    | PostgreSQL 16            | 5432 | Data Persistence| Scan results, user data, audit logs    |
+-------------+---------------------------+------+------------------+----------------------------------------+

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Guía del Usuario

   getting-started
   user-interface
   uploading-scans
   viewing-results
   exporting-data

.. toctree::
   :maxdepth: 2
   :caption: Referencia de la API

   api/overview
   api/endpoints
   api/websockets
   api/models
   api/errors

.. toctree::
   :maxdepth: 2
   :caption: Guía del Desarrollador

   development/setup
   development/frontend
   development/backend
   development/omr-service
   development/database
   development/testing

.. toctree::
   :maxdepth: 2
   :caption: Despliegue

   deployment/docker
   deployment/kubernetes
   deployment/cloud
   deployment/monitoring
   deployment/security

.. toctree::
   :maxdepth: 2
   :caption: Arquitectura

   architecture/overview
   architecture/clean-architecture
   architecture/microservices
   architecture/data-flow
   architecture/scaling
   architecture/performance

.. toctree::
   :maxdepth: 2
   :caption: Technical Reference

   technical/image-processing
   technical/bubble-detection
   technical/database-schema
   technical/configuration
   technical/troubleshooting

.. toctree::
   :maxdepth: 1
   :caption: Recursos Adicionales

   roadmap
   changelog
   contributing
   license
   support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`