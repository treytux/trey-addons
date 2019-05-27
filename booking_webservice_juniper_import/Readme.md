Booking webservice juniper import from xml
==========================================
1. Hay que crear Webservice llamado:  Exportador Juniper

    + **Nombre**: Exportador Juniper
    + **Tipo**: Juniper
    + **Url**: url
    + **Nombre** usuario : juniper
    + **Contraseña**: no importa
2. Apareceran los siguientes botones:
    + **Importar reservas**: Asistente para importar desde ficheros xml las reservas de juniper.
    + **Asignar cuenta de cliente**: Asistente para asignar cuenta de cliente en Juniper en campo "cuenta cliente" en el apartado "Webservice Juniper" de la ficha de cliente. Necesita un archivo .xls donde:
        * Columna 1: Cuenta de cliente Juniper
        * Columna 2: Cuenta de cliente en iboosy/methabook
    + **Cancelar Reservas juniper**:  Asistente para marcar reservas como canceladas. Cancelará todos los localizadores indicados en una archivo .xls
    + **Cargar desde buffer**: Tras incorporar las cuentas de clientes que muestra el log del buffer. El botón lanza la importación de las reservas desde el buffer.
