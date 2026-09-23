======================
Chat GPT API Connector
======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Este módulo permite conectar Odoo con la API de Chat GPT de OpenAI. Permite 
enviar mensajes y recibir respuestas de la API de Chat GPT.

**Tabla de contenidos**

.. contents::
   :local:

Características
==============

* Configuración de la clave API de OpenAI desde los ajustes del sistema.
* Soporte para modelos GPT-3.5 y GPT-4 (según disponibilidad de la API).
* Gestión de errores y mensajes claros en caso de problemas de autenticación, límite de uso o parámetros incorrectos.
* Integración sencilla para desarrolladores: puedes llamar a la función `chat_completion` desde otros módulos Odoo.
* Traducción de mensajes y soporte multilenguaje.

Configuración
=============

1. Instala el módulo en tu instancia de Odoo.
2. Ve a **Ajustes > Técnicos > Parámetros del sistema** y añade el parámetro `chatgpt.api_key` con tu clave privada de OpenAI.
3. (Opcional) Configura el modelo por defecto con el parámetro `chatgpt.default_model` (por ejemplo, `gpt-3.5-turbo`).

Uso para desarrolladores
========================

Puedes utilizar el conector en tus propios módulos llamando a:

.. code-block:: python

    response = self.env['chatgpt.api.connector'].chat_completion(
        prompt="¿Cuál es la capital de Francia?",
        model="gpt-3.5-turbo",
        temperature=0.3,
        max_tokens=1500,
        system_message_content="Responde como un asistente técnico."
    )

El método devuelve la respuesta generada por ChatGPT.

Gestión de errores
==================

El módulo gestiona los siguientes errores comunes de la API de OpenAI:

* Falta de clave API o clave incorrecta.
* Límite de uso excedido.
* Permisos insuficientes.
* Parámetros inválidos.
* Errores generales de conexión.

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_

Colaboradores
~~~~~~~~~~~~~

* Equipo de Trey

Licencia
========

AGPL-3

Contacto y soporte
==================

Para soporte, contacta con el equipo de Trey en https://www.trey.es
