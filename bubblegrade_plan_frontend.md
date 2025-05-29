Eres un experto en UI/UX, diseño de interacción y sistemas de diseño. Diseña la interfaz/frontend de BubbleGrade cubriendo todos los requisitos funcionales.

1️⃣  Principios de diseño  
   - Enumera 4-5 principios clave (claridad, feedback inmediato, accesibilidad WCAG 2.1 AA, etc.).

2️⃣  Mapa de navegación  
   - Lista las secciones y subrutas (ej. "/", "/scans/{id}", "/reports", "/settings").

3️⃣  Lista de pantallas  
   Para cada pantalla entrega:
     • Nombre y URL  
     • Objetivo principal y KPIs de éxito  
     • Wireframe en texto ASCII o Mermaid (máx 80 caracteres de ancho)  
     • Componentes UI clave (botones, tablas, formularios)  
     • Estados (loading, vacío, error)  
     • Consideraciones de accesibilidad y responsive (desktop + mobile)  

   Pantallas mínimas:
     - Inicio / Upload
     - Progreso en tiempo real
     - Tabla de resultados con edición inline (nombre, CURP, score)
     - Vista detalle Scan
     - Reportes / exportación
     - Ajustes (plantilla de examen, mapeo de coordenadas)

4️⃣  Flow de usuario  
   - Diagrama de flujo (Mermaid flowchart) desde “Upload Photo” hasta “Descargar Reporte”.

5️⃣ Sistema visual  
   - Define paleta de colores (con contrast ratio recomendado)  
   - Tipografía (web-safe + escalas rem)  
   - Espaciado y grid (8 pt)  
   - Estilo de botones, inputs y feedback states  
   - Iconografía y uso de estados (éxito, error, progreso)

6️⃣ Design tokens JSON  
   - Colores primario, secundario, fondo, texto  
   - Spacing XS-XL  
   - Font sizes h1-body-small  
   - BorderRadius, sombras

7️⃣ Componente reutilizable clave  
   - Diseña un `<UploadCard>` con arrastrar-y-soltar, validación de tipo/size y barra de progreso.  
   - Diseña una `<EditableCell>` para la tabla (modo view ↔ edit).

8️⃣ Micro-interacciones  
   - Describir animaciones (subida, barra de progreso, toast “listo”).  
   - Preferir CSS transition de 200 ms, sin bloquear interacción.

9️⃣ Hand-off a dev  
   - Lista props y tipos TS de cada componente  
   - Señala dependencias recomendadas (Ant Design, React Hook Form, Zustand para estado).  
   - Checklist de accesibilidad (etiquetas `aria-`, roles, foco, contraste).

10️⃣ Futuras extensiones  
   - Ideas de dashboard analítico, multi-idioma, dark mode.
