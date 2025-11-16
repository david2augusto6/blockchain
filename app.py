import json
from blockchain import Blockchain
from time import time
from textwrap import dedent
from uuid import uuid4

from flask import Flask, jsonify, request

# Instanciando nó
app = Flask(__name__)

# Gera um endereço globalmente único para este nó
node_identifier = str(uuid4()).replace('-', '')

#Instanciando a Blockchain
blockchain = Blockchain()


@app.route('/node/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'A cadeia foi substituída',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'A cadeia é autoritativa',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/node/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "ERRO: Forneça uma lista válida de nós", 400
    
    for node in nodes:
        blockchain.register_node(node)
    
    response = {
        'message': 'Novos nós foram adicionados',
        'total_nodes': list(blockchain.nodes)
    }

    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    # Executar o algoritmo PoW para obter a proxima proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Devemos receber uma recompensa por encontrar a proof
    # O remetente é "0" para simbolizar que aquele nó minerou uma nova moeda
    blockchain.new_transaction(
        sender = "0",
        recipient = node_identifier,
        amount = 1,
    )

    #Forjar o novo Bloco adicionando-o à blockchain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    #checar se os campos requisitados estão nos dados POSTados
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Valores faltantes', 400

    # Criar uma nova transação
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transação será adicionada ao bloco {index}'}
    return jsonify(response), 201


@app.route("/chain", methods=['GET'])
def full_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }

    return jsonify(response), 200


if __name__ == "__main__":
    port = int(input("Insira o número da porta: "))
    app.run(host = "0.0.0.0", port=port)

