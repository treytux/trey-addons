===================
Account move import
===================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Descripción
===========

`account_move_import` es un módulo base para importar asientos contables
desde ficheros. Proporciona la interfaz de usuario, el modelo de acceso y el
contrato de despacho de importación que utilizan los módulos específicos de
cada formato.

Este módulo no incluye por sí mismo un parser concreto de fichero.

Alcance funcional
=================

- Añade el campo booleano `import_account_moves` en los diarios contables.
- Muestra un botón `Import Moves` en el dashboard del diario cuando el campo
  está activado.
- Abre un asistente para subir un fichero y seleccionar un tipo de
  importación.
- Ejecuta el proceso de importación y redirige al usuario a los asientos
  importados.

Comportamiento técnico
======================

Modelo del asistente
--------------------

Modelo transitorio: `account.move.import_file`

- Campos:
  - `file` (binario, obligatorio)
  - `filename` (char)
  - `type` (selection, obligatorio)

Flujo de importación
--------------------

1. `import_file()` llama a `_import_file()`.
2. `_import_file()` despacha a un método con nombre
   `_import_file_<type_value>`.
3. El diario seleccionado se obtiene del contexto (`active_model`,
   `active_ids`).
4. El método debe devolver un recordset de `account.move`.
5. El asistente devuelve una acción filtrada a esos asientos importados.

Ayuda para decodificar ficheros
-------------------------------

`get_file_content()` decodifica los ficheros binarios subidos usando este
orden de fallback:

1. `utf-8`
2. `iso8859-1`
3. `latin-1`

Si la decodificación falla en todas las opciones, se lanza un `UserError`.

Contrato de extensión
=====================

Los módulos específicos de formato deben heredar `account.move.import_file` y:

- Extender `type` con `selection_add`.
- Implementar `_import_file_<new_type>(journal, content)`.
- Opcionalmente sobrescribir `get_file_content()` cuando el formato no sea
  texto plano, por ejemplo para parsear binarios Excel.

Sin esas extensiones, el método base `_import_file_none()` lanza:
"The type of file to import has not been defined."

Permisos de acceso
==================

- `account.group_account_manager`: acceso completo al modelo del asistente.
- `account.group_account_invoice`: acceso de solo lectura al modelo del
  asistente.

Dependencias
============

- `account`

Tests
=====

Los tests incluidos cubren:

- Decodificación de ficheros (`utf-8` y fallback a `latin-1`).
- Comportamiento de error cuando no existe implementación para el tipo de
  importación.
- Despacho de la importación a `_import_file_<type>`.
- Acción devuelta con dominio restringido a los IDs importados.

Autor
=====

- `Trey <https://www.trey.es>`__
