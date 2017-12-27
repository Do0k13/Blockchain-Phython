import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

#Proyecto de prueba de Cadena de Bloques en Python con comentarios en español

#Creado por Daniel van Flymen: https://github.com/dvf/blockchain/blob/master/blockchain.py

#Artículo original: https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Creación del bloque génesis
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
		Agrega un nuevo nodo a la lista de nodos
        :address: Dirección del nodo, Ejemplo: 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determinar si una cadena de bloques dada es válida
        :chain: Una cadena de bloques 
        :return: True si es válida, False si no lo es 
		"""

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Validar que el hash del bloque es correcto
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Valida rque la prueba de trabajo es correcta
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Éste es el algoritmo de concenso, resuelve los conflictos 
        reemplazando nuestra cadena con la cadena más larga en la red 
        :return: True si la cadena fué reemplazada, False si no lo fué
        """

        neighbours = self.nodes
        new_chain = None

        # Sólo estamos buscando cadenas más largas que la nuestra 
        max_length = len(self.chain)

        # Toma y verifica las cadenas de todos los nodos de nuestra red
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Valida si la cadena es la más larga y si es válida
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Reemplaza nuestra cadena si descubrimos una cadena válida más larga que la nuestra
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Genera un nuevo bloque en la cadena de bloques 
        :proof: La prueba dada por el algoritmo de prueba de trabajo
        :previous_hash: Hash del bloque previo 
        :return: Nuevo bloque
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reinicia la actual lista de transacciones
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Genera una nueva transaccción para agregar en el próximo bloque minado
        :sender: Dirección del emiosor 
        :recipient: Dirección del destinatario
        :amount: Monto
        :return: El índice del bloque que contendrá esta transacción 
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Genera un hash SHA-256 de un bloque
        :block: Bloque
        """

        # Debemos asegurarnos de que el diccionario se encuentre ordenado o tendremos hashes inconsistentes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Algoritmo sencillo de Prueba de Trabajo (PoW):
         - Encontrar un número p' asegurarse que ese hash(pp') contenga al principio 4 ceros, donde p es el anterior p'
         - p es la prueba previa, y p' es la nueva prueba 
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Valida la prueba 
        :last_proof: Prueba previa 
        :proof: Prueba actual 
        :return: True si es correcta, False si no lo es
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Iniciar el nodo
app = Flask(__name__)

# Generar una dirección global única para este nodo
node_identifier = str(uuid4()).replace('-', '')

# Iniciar la cadena de bloques
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # Ejecutamos el algoritmo de prueba de trabajo para obtener la siguiente prueba
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Debemos recibir una recompensa por encontrar la prueba
    # El emisor es "0" para identificar que este nodo ha minado una nueva moneda
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Crear el nuevo bloque agregándolo a la cadena
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "Nuevo bloque creado",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Validar que los campos requeridos están en los datos de POST
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Valores faltantes', 400

    # Crear una nueva transacción
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'La transacción será añadida al bloque {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Favor de proporcionar un número válido de nodos", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Nuevos nodos han sido añadidos',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'La cadena fué reemplazada',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'La cadena tiene prioridad',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='puerto de escucha')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)