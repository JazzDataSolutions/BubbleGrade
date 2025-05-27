Clean Architecture Implementation
================================

BubbleGrade implements **Clean Architecture** principles with **SOLID** design patterns to ensure maintainability, testability, and scalability.

Architecture Overview
--------------------

The system follows a layered architecture with clear separation of concerns:

.. code-block:: text

    ┌─────────────────────────────────────────────────────────┐
    │                  Presentation Layer                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
    │  │   Routers   │  │   Schemas   │  │Dependencies │     │
    │  └─────────────┘  └─────────────┘  └─────────────┘     │
    └─────────────────────────────────────────────────────────┘
                               │
    ┌─────────────────────────────────────────────────────────┐
    │                  Application Layer                      │
    │  ┌─────────────────────────────────────────────────────┐ │
    │  │              Use Cases                              │ │
    │  └─────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘
                               │
    ┌─────────────────────────────────────────────────────────┐
    │                   Domain Layer                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
    │  │  Entities   │  │Repositories │  │  Services   │     │
    │  └─────────────┘  └─────────────┘  └─────────────┘     │
    └─────────────────────────────────────────────────────────┘
                               │
    ┌─────────────────────────────────────────────────────────┐
    │                Infrastructure Layer                     │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
    │  │  Database   │  │External APIs│  │File Storage │     │
    │  └─────────────┘  └─────────────┘  └─────────────┘     │
    └─────────────────────────────────────────────────────────┘

Layer Responsibilities
---------------------

Domain Layer
~~~~~~~~~~~~

**Location**: ``services/api/app/domain/``

Contains the core business logic and rules:

- **Entities** (``entities.py``): Core business objects like ``Scan``, ``OMRResult``
- **Repository Interfaces** (``repositories.py``): Abstract data access contracts
- **Service Interfaces** (``services.py``): External service contracts

.. code-block:: python

    # Domain Entity Example
    @dataclass
    class Scan:
        id: UUID
        filename: str
        status: ScanStatus
        upload_time: datetime
        
        def mark_as_completed(self, score: int, answers: List[str]) -> None:
            self.status = ScanStatus.COMPLETED
            self.score = score
            self.answers = answers

Application Layer
~~~~~~~~~~~~~~~~

**Location**: ``services/api/app/application/``

Orchestrates business workflows:

- **Use Cases** (``use_cases.py``): Business logic orchestration
- Coordinates between domain and infrastructure layers
- Implements application-specific business rules

.. code-block:: python

    class ScanUseCases:
        def __init__(self, scan_repository: ScanRepository, 
                     omr_service: OMRService):
            self.scan_repository = scan_repository
            self.omr_service = omr_service
        
        async def create_scan(self, filename: str, content: bytes) -> Scan:
            # Business logic orchestration
            scan = Scan(...)
            await self.scan_repository.create(scan)
            # Process asynchronously
            return scan

Infrastructure Layer
~~~~~~~~~~~~~~~~~~~

**Location**: ``services/api/app/infrastructure/``

Implements external concerns:

- **Database** (``database.py``): SQLAlchemy models and configuration
- **Repositories** (``repositories.py``): Concrete repository implementations
- **External Services** (``external_services.py``): HTTP clients, file storage
- **Mappers** (``mappers.py``): Domain ↔ Persistence model conversion

Presentation Layer
~~~~~~~~~~~~~~~~~

**Location**: ``services/api/app/presentation/``

Handles HTTP concerns:

- **Routers** (``routers.py``): FastAPI route definitions
- **Schemas** (``schemas.py``): Pydantic request/response models
- **Dependencies** (``dependencies.py``): Dependency injection setup

SOLID Principles Implementation
------------------------------

Single Responsibility Principle (SRP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each class has one reason to change:

- ``ScanRepository``: Only handles scan data persistence
- ``OMRService``: Only handles image processing
- ``WebSocketService``: Only handles real-time communication

Open/Closed Principle (OCP)
~~~~~~~~~~~~~~~~~~~~~~~~~~

System is open for extension, closed for modification:

.. code-block:: python

    # Add new OMR service without changing existing code
    class EnhancedOMRService(OMRService):
        async def process_image(self, file_path: str) -> OMRResult:
            # Enhanced implementation with ML models
            pass

Liskov Substitution Principle (LSP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Derived classes are substitutable for base classes:

.. code-block:: python

    # Any OMRService implementation can be used
    def process_scan(omr_service: OMRService):
        # Works with HttpOMRService, MockOMRService, MLOMRService
        return omr_service.process_image(path)

Interface Segregation Principle (ISP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients depend only on interfaces they use:

- ``ScanRepository``: Only scan-related methods
- ``WebSocketService``: Only WebSocket methods
- ``ExcelExportService``: Only export methods

Dependency Inversion Principle (DIP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

High-level modules depend on abstractions:

.. code-block:: python

    # Use cases depend on interfaces, not concrete implementations
    class ScanUseCases:
        def __init__(self, 
                     scan_repository: ScanRepository,  # Interface
                     omr_service: OMRService):         # Interface
            # Implementation injected at runtime

Dependency Injection
-------------------

FastAPI's dependency injection system manages object creation:

.. code-block:: python

    # dependencies.py
    def get_scan_use_cases(
        scan_repository: ScanRepository = Depends(get_scan_repository),
        omr_service: OMRService = Depends(get_omr_service)
    ) -> ScanUseCases:
        return ScanUseCases(scan_repository, omr_service)

Benefits of This Architecture
----------------------------

1. **Testability**: Easy to mock dependencies for unit testing
2. **Maintainability**: Changes isolated to specific layers
3. **Scalability**: Can swap implementations without affecting business logic
4. **Flexibility**: New features added without modifying existing code
5. **Separation of Concerns**: Each layer has clear responsibilities

Testing Strategy
---------------

The clean architecture enables comprehensive testing:

.. code-block:: python

    # Unit test example
    async def test_create_scan():
        # Arrange
        mock_repo = Mock(spec=ScanRepository)
        mock_omr = Mock(spec=OMRService)
        use_cases = ScanUseCases(mock_repo, mock_omr)
        
        # Act
        result = await use_cases.create_scan("test.jpg", b"content")
        
        # Assert
        mock_repo.create.assert_called_once()

Migration Path
-------------

To migrate from the old monolithic structure:

1. **Phase 1**: Extract domain entities and interfaces
2. **Phase 2**: Implement repository pattern
3. **Phase 3**: Create use cases layer
4. **Phase 4**: Set up dependency injection
5. **Phase 5**: Replace old endpoints with new routers

This gradual approach ensures system stability during the transition.