# Modulo para migraciones y carga de datos

## Caracteristicas
____

Este modulo agrega a los objetos mas importantes del sistema, una serie de 
campos para realizar importaciones de datos desde fuentes externas.

## Campos
____

### migration_id (fields.Integer)

Entero para almacenar un identificador unico del origen del dato.

### migration_key (fields.Char)

Cadena para almacenar un identificador unico del origen del dato.

### filename (fields.Char)

Cadena para almacenar el nombre del fichero importado.

### sheetname (fields.Char)

Cadena para almacenar el nombre de la hoja de calculo.

### row (fields.Char)

Cadena para almacenar el numero de fila de la hoja de calculo.


## Modulos mgt_
____

Son modulos que amplian la funcionalidad del modulo base, agregando estos 
campos en modulos opcionales en el sistema.

### mgt_product_brand
Marcas de producto

## Todo
____

[] Formularios para cada uno de los objetos en los que se visualizen los 
datos de carga. Estos datos solo estaran disponibles para el usuario admin a
 nivel de auditorias.


