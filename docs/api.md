 # Documentación de la API

 ## Descripción General

 La API de BubbleGrade está desarrollada con FastAPI y ofrece:
 - Endpoints REST para gestionar escaneos de formularios de burbujas.
 - Comunicación en tiempo real mediante WebSocket para seguimiento de progreso.
 - Exportación de resultados en formato Excel.

 ## URL Base

 ```
 http://localhost:8080/api/v1
 ```

 ## Autenticación

 - En desarrollo: no requiere autenticación.
 - En producción: implementar JWT u OAuth2.

 ## Endpoints Principales

 1. **Subir Escaneo**
    - **POST** `/api/v1/scans`
    - Solicitud: `multipart/form-data` con campo `file` (imagen JPG/PNG).
    - Respuesta:
      ```json
      { "id": "uuid-escaneo", "filename": "archivo.jpg", "status": "QUEUED" }
      ```

 2. **Listar Escaneos**
    - **GET** `/api/v1/scans?limit=&offset=&status=`
    - Consulta paginada y filtrada por estado.
    - Respuesta:
      ```json
      {
        "scans": [ /* array de objetos ProcessedScan */ ],
        "total": 123,
        "offset": 0,
        "limit": 20
      }
      ```

 3. **Detalles de Escaneo**
    - **GET** `/api/v1/scans/{scan_id}`
    - Parámetro: `scan_id` (UUID).
    - Respuesta: objeto `ProcessedScan` con regiones, resultados OMR/OCR y metadatos.

 4. **Actualizar Escaneo**
    - **PATCH** `/api/v1/scans/{scan_id}`
    - Cuerpo JSON con correcciones manuales:
      ```json
      { "nombre": { "value": "Nuevo Nombre" }, "curp": { "value": "CURP123..." } }
      ```
    - Respuesta: `ProcessedScan` actualizado.

 5. **Exportar Resultados**
    - **GET** `/api/v1/exports/{scan_id}?format=xlsx|csv|pdf`
    - Descarga de archivo con resultados.

 6. **Health Check**
    - **GET** `/health`
    - Respuesta:
      ```json
      { "status": "healthy" }
      ```

 ## Comunicación WebSocket

 - **URL**: `ws://localhost:8080/ws`
 - **Tipos de Mensajes**:
   1. **scan_progress**: `{ "type": "scan_progress", "scan_id": "uuid", "stage": "preprocessing" }`
   2. **scan_progress** (graded): `{ "type": "scan_progress", "scan_id": "uuid", "stage": "graded", "score": 85 }`
   3. **scan_progress** (completed): `{ "type": "scan_progress", "scan_id": "uuid", "status": "COMPLETED", "score": 85 }`
   4. **scan_progress** (error): `{ "type": "scan_progress", "scan_id": "uuid", "status": "ERROR", "error": "mensaje" }`