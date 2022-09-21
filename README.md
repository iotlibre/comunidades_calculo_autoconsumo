# comunidades_calculo_autoconsumo
**calculo_autoconsumido_v9.py **

Este escript calcula la energía consumida, autoconsumida y exportada cada hora partiendo de un servidor emonCMS

Se parte de dos registros de energía, la energía consumida y la energía generada, entendiendo como energía generada la correspondinte incluyendo el coeficiente de reparto

El resultado se trasmite al servidor con la información de la hora para que se pueda guardar y posteriormete visualizar

Los ficheros de configuración son:
* **config_autoconsumido.ini**  con la información del servidor para extraer los datos necesarios
* **reading_register.txt** donde se almacenan las últimas lecturas realizadas para tenerlas en cuenta la siguiente vez que se corre el escript

Lo ideal es ejecutar este escript automaticamente desde el crontab de un servidor aunque también se puede hacer manualmente

Para cubrir las necesidades de proyectos que tienen que interactuar con bases de datos MySQL se han desarrollado los siguentes scripts:
* **actualizacion_db_v00.py** Es para escrir en una base de datos MySQL los calclulos de energía autoconsumida
* **borrar_registros.py** Herramienta para simplificar el borrado de resgistros
