# SPEC: Acceso a conocimiento desde portal de empleado

## 1. Contexto
- Fecha de solicitud: 2026-05-14
- Alcance: revisar el error de permisos al acceder a
  `/employee/knowledge` con un usuario sin acceso de lectura a
  `document.page`.

## 2. Diagnóstico
- Las rutas de conocimiento del portal de empleado leen `document.page` con el
  entorno del usuario actual.
- El modelo `document.page` solo concede lectura al grupo
  `document_knowledge.group_document_user` o a grupos superiores.
- Ese grupo implica `base.group_user`, por lo que asignarlo a usuarios portal
  puede convertirlos en usuarios internos.
- La lógica propia de `portal_employee` ya limita el acceso mediante
  `res.users.knowledge_categories`, pero esa comprobación no se alcanza si
  Odoo bloquea antes la lectura del modelo.

## 3. Objetivos
- Permitir que `/employee/knowledge` muestre solo las categorías y documentos
  asignados al usuario en `knowledge_categories`.
- Evitar conceder permisos globales de `document.page` a usuarios que solo
  deben consultar documentos desde el portal.
- Mantener la descarga y firma de adjuntos restringidas a páginas permitidas
  para el usuario.

## 4. No objetivos
- No cambiar la seguridad estándar de los módulos OCA `document_page` ni
  `document_knowledge`.
- No dar acceso backend adicional al usuario salvo que se decida como
  configuración funcional.
- No ampliar el alcance de las categorías permitidas más allá de la asignación
  actual del usuario.

## 5. Diseño técnico propuesto
- Revisar las rutas en `controllers/portal.py` que leen `document.page`:
  - `/employee/knowledge`
  - `/employee/knowledge/category/<category>`
  - `/employee/knowledge/document/<page_id>`
  - `/employee/knowledge/document/<page_id>/sign`
  - `/employee/knowledge/attachment/download/<document>/<attachment>`
- Usar `sudo()` de forma acotada para leer páginas y adjuntos desde portal.
- Mantener siempre una validación explícita con:
  - usuario vinculado a empleado
  - categoría de la página dentro de `knowledge_categories` o sus hijas
  - compañía vacía, compañía del empleado o compañía padre de la compañía del
    empleado
  - tipo de página esperado
  - adjunto perteneciente a la página solicitada
- Para la firma, ejecutar la acción con permisos suficientes solo después de
  validar el acceso portal a la página.
- No añadir ACLs sobre `document.page` para `base.group_portal`, porque eso
  solo cambia el mensaje de error y no cubre usuarios empleados internos sin
  grupos de conocimiento.

## 6. Alternativa funcional inmediata
- Si el usuario debe ser usuario interno, asignarle el grupo
  `document_knowledge.group_document_user`
  ("Documents Knowledge / Document Knowledge user").
- Esta alternativa resuelve el error actual, pero también hereda
  `base.group_user`; no es la opción adecuada para un usuario portal externo.

## 7. Plan de validación
- Crear un usuario vinculado a empleado, sin grupo de conocimiento backend.
- Asignar una categoría de conocimiento en `knowledge_categories`.
- Confirmar que `/employee/knowledge` lista solo categorías permitidas.
- Confirmar que una página de una categoría no asignada redirige a `/my`.
- Confirmar que se muestran documentos sin compañía, de la compañía del
  empleado y de compañías padre de la compañía del empleado.
- Confirmar que no se muestran documentos de compañías ajenas.
- Confirmar que la descarga solo funciona para adjuntos de páginas permitidas.
- Confirmar que la firma solo funciona para páginas permitidas y firmables.
- Confirmar que un usuario sin empleado vinculado no accede al portal de
  conocimiento.

## 8. Riesgos y mitigaciones
- Riesgo: un `sudo()` demasiado amplio exponga páginas no asignadas.
  - Mitigación: centralizar la comprobación de acceso portal y filtrar todos
    los `search` con los IDs de categorías permitidas y compañías permitidas.
- Riesgo: descarga de adjuntos cruzados.
  - Mitigación: comprobar que el adjunto pertenece al `document.page`
    solicitado antes de devolver el contenido.

## 9. Entregables previstos
- Ajuste acotado en `portal_employee/controllers/portal.py`.
- Tests de acceso portal para usuario sin grupo de conocimiento backend.
- Sin cambios de i18n salvo que se añadan mensajes nuevos.
