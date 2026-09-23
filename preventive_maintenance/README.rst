======================
Preventive maintenance
======================

Contiene una colección de scripts destinados a evaluar el estado de las
instalaciones de Odoo de clientes captando problemas de datos, procesos,
integridad, vistas, informes...

Scripts presentes y su funcionamiento
-------------------------------------
- Record integrity: Verifica los contactos y productos de una instancia
    comparando en masa por su nombre, con un grado configurable de parecido,
    correos, precios, variantes, etc. Generando un .json con el resultado.

    - MAX_GROUPS: Número máximo de grupos duplicados que se revisan
    - MAX_IDS_PER_GROUP: Número máximo de IDs duplicadas devueltas
    - FUZZY_NAME_THRESHOLD: Grado de diferencia al comparar posibles nombres
    duplicados
    - REPORT_FILENAME: Nombre de lo exportado
- Storage usage: Devuelve un informe con posibles gastos innecesarios de
    almacenamiento como un exceso de entradas inactivas,
    tablas excesivamente grandes, adjuntos desconectados...

    - INNACTIVE_LIMIT: Cantidad mínima de archivados que marca como excesivo
    - LARGE_ATTACHMENT_LIMIT: Tamaño mínimo que marca como preocupante
    - NUM_MAX_SIZE_TABLES: Cantidad de tablas por tamaño devueltas
    - REPORT_FILENAME: Nombre de lo exportado

Contribuidor
------------
- Trey Kilobytes de Soluciones SL <https://www.trey.es>

Créditos
========

Autor
~~~~~

* `Trey <http://www.trey.es>`_
