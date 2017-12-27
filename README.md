APRENDE SOBRE BLOCKCHAIN CREANDO UNA
Este código fué realizado originalmente por Daniel van Flymen

Acá el artículo original:
https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

Instalación:
Asegurarse que la versión Python 3.6+ está instalada en el equipo.
Instalar pipenv.

$ pip install pipenv 

Crear un entorno virtual y especificar la versión a usar de Python.

$ pipenv --python=python3.6

Instalar requerimientos:

$ pipenv install 

Ejecutar el servidor:

$ pipenv run python blockchain.py
$ pipenv run python blockchain.py -p 5001
$ pipenv run python blockchain.py --port 5002
