# SPEC: Creación de estudiantes desde el portal de academia

## 1. Contexto

- Fecha de solicitud: 2026-08-03
- Módulo afectado: `portal_academy`
- Página afectada: `/my/students`

## 2. Objetivos

- Mostrar un botón para crear un estudiante en el listado de estudiantes del tutor.
- Mostrar el botón de creación junto al breadcrumb de la página de estudiantes.
- Permitir introducir apellidos y nombre, fecha de nacimiento y curso.
- Facilitar al tutor un acceso visible para editar sus propios datos de cliente.
- Crear el contacto como estudiante y vincularlo al tutor autenticado.
- Restringir la operación a usuarios portal con perfil de tutor.

## 3. Diseño técnico

- Añadir las rutas `/my/student/new` y `/my/student/new/save` con `auth='user'`.
- Crear `res.partner` con `is_student=True` y `tutor_ids` apuntando al tutor actual.
- Validar nombre y provincia antes de crear el contacto.
- Limitar el selector de curso a formaciones compatibles con estudiantes.
- Reutilizar el formulario estándar de Odoo en `/my/account` para editar los
  datos del cliente y evitar duplicar su validación.
- Exigir la aceptación de las condiciones SEPA al añadir una cuenta bancaria
  desde el portal.
- Solicitar únicamente el IBAN en el alta de la cuenta bancaria y obtener
  automáticamente la entidad bancaria a partir de él.
- Mostrar debajo de la aceptación SEPA la información legal del mandato de
  domiciliación de GADER FORMACION Y EVENTOS SL desde un campo HTML del sitio
  web, editable y traducible en la configuración del sitio.
- Rechazar matrículas con fecha de inicio anterior al día actual o fuera del
  rango de fechas de la actividad.
- Enlazar desde la aceptación de matrícula los términos del servicio y la
  política de privacidad.
- Mostrar y permitir la cancelación de una matrícula solo mientras la
  actividad no haya finalizado, además de respetar el estado de la matrícula.
- Usar los estados de `res.country.state` para el selector de provincia.

## 5. Matrículas con datos fiscales y mandato SEPA

- La matrícula desde el portal usa los datos fiscales del tutor/pagador.
- El tutor debe tener cumplimentados el nombre y el NIF antes de poder
  matricularse, independientemente de dónde se hayan introducido.
- La matrícula requiere una cuenta bancaria activa del tutor asociada a un
  mandato de `account.banking.mandate` en estado `valid`.
- El bloqueo se comprueba al enviar el formulario del portal.
- La creación, firma y validación del mandato no forman parte de este cambio.

## 4. Plan de validación

- Verificar que un tutor ve el botón y el formulario.
- Verificar que el envío crea el estudiante con todos los datos y la relación
  al tutor.
- Verificar que un usuario no tutor no puede acceder ni crear estudiantes.
- Ejecutar las pruebas de `portal_academy` y actualizar el módulo.

## 5. Matrículas del tutor en el inicio del portal

- Añadir el contador `enrollment_count` para las matrículas de los estudiantes
  vinculados al tutor autenticado.
- Mostrar una entrada `Enrollments` en `portal_my_home_students` cuando existan
  matrículas.
- Añadir `/my/enrollments` con paginación y acceso restringido a tutores.
- Mostrar estudiante, matrícula, actividad, plan formativo, fechas y estado,
  enlazando el estudiante con su listado de actividades.
