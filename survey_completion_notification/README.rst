.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============================
Survey completion notification
==============================

Este módulo extiende la funcionalidad de las encuestas de Odoo para permitir
notificar automáticamente a los seguidores cuando una encuesta es finalizada.

Incluye una opción de configuración global y una plantilla de correo
predeterminada para estandarizar las notificaciones de finalización.

Configuración
=============

1. Vaya a **Encuestas > Configuración > Ajustes**.
2. En la sección de encuestas, encontrará el campo **Notificar encuesta**.
3. Al marcar esta casilla, se activará el envío automático de correos a los seguidores de cada encuesta.

Funcionamiento
==============

Una vez activo el ajuste:
* El sistema detecta cuando un usuario pulsa el botón **Finalizar** en una encuesta.
* Se dispara un correo electrónico utilizando la plantilla **Survey: completed**.
* Los destinatarios de este correo serán todos los registros (partners) que estén marcados como **seguidores** en el modelo de la encuesta correspondiente.
* El cuerpo del mensaje incluye el nombre de la encuesta y el email del participante que la ha completado.

Instalación
===========

Para comprobar el funcionamiento en un entorno de pruebas:
1. Instale el módulo en una base de datos con **datos demo**.
2. Configure el check en ajustes.
3. Acceda a una encuesta demo (ej. "Feedback post-venta") y complétela.
4. Verifique en el chatter de la encuesta o en los mensajes salientes la notificación generada.

Autor
=====
.. image:: https://trey.es/logo.png
   :alt: License: Trey Kilobytes de Soluciones SL
`Trey Kilobytes de Soluciones SL <https://www.trey.es>`_
