==========
Healthcare
==========

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo permite la gestión del cuidado de la salud.

- Grupos de usuario:
    - Permitir acceso a información de usuario.
    - Permitir acceso a información sensible/protegida de usuario.
    - Permitir acceso al histŕorico del usuario.

Uso
---
- Tipos de contacto:

    - Para cada usuario que reciba atenciones de cuidado de la salud hay que crear un contacto de tipo "Individuo" y debe marcarse el check "¿Es usuario?".

    - Los usuarios pueden tener asociado uno o varios familiares, para cada familiar hay que crear un contacto de tipo "Individuo" y debe marcarse el check "¿Es familiar?".

    - Los usuarios deben tener asociados uno o varios socios (que puede ser el mismo usuario). Para cada socio hay que crear un contacto y debe marcarse uno de los checks para indicar si es "¿Es socio de número?" o "¿Es socio colaborador?".

- Relaciones del contacto usuario:
    Cada usuario se relacionará con su/s socio/s y familiar/es creando relaciones con ellos a través del botón "Relaciones" de la ficha de contacto. Previamente se deben crear los tipos de relaciones desde el menú "Contactos/Relaciones/Tipos de relaciones"

- Usuarios que acceden al sistema:
    - Técnico psicólogo.
    - Técnico integrador social.
    - Técnico trabajador social.
  Existen plantillas de usuario para cada rol con los permisos establecidos preparados para ser duplicados y asignar el nombre y correo de la persona que va a conectarse.

- Gestión de cuidados de la salud para cada usuario:
    Desde el formulario de un contacto marcado como "¿Es usuario?", se puede acceder a diferentes secciones dependiendo de los permisos del usuario que acceda a Odoo:
        - Datos información: contiene los datos básicos del usuario.
        - Datos protegidos: contiene los datos sensibles del usuario
        - Historial del usuario: contiene información para cada intervención con el usuario.


**Tabla de contenidos**

.. contents::
   :local:


Autor
~~~~~

* `Trey <https://www.trey.es>`__:
