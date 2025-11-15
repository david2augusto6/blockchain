import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4
from urllib.parse import urlparse

from flask import Flask


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Cria o bloco "gênese"
        self.new_block(previous_hash=1, proof=100)
    
    def register_node(self, address):
        """
            Adiciona um nó à lista de nós
            :param address: <str> Endereço do nó. Ex.: 'htp://192.168.0.5:5000'
            :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_transaction(self, sender, recipient, amount):
        """
            Cria uma nova transação que irá para o próximo bloco minerado
            :param sender: <str> Endereço do remetente (Sender)
            :param recipient: <str> Endereço do receptor (Recipient)
            :param amount: <int> Quantidade
            :return: <int> O índice do bloco que manterá essa transação
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1
    
    def new_block(self, proof, previous_hash=None):
        """
            Adiciona um novo bloco à Blockchain
            :param proof: <init>  A 'proof' dada pelo algoritmo Proof of Work
            :param previous_hash: (Opcional) <str> Hash do bloco anterior
            :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []
        
        self.chain.append(block)
        return block

    @property
    def last_block(self):
        return self.chain[-1]
    
    @staticmethod
    def hash(block):
        """
            Cria um hash SHA-256 de um bloco
            :param block: <dict> Block
            :return: <str>
        """

        # Deve-se garantir que o Dicionário está Ordenado, ou haverá hashes inconstistentes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def proof_of_work(self, last_proof):
        """
            Algoritmo de Proof of Work simples:
                - Encontrar um número p' tal que hash(pp') contenha 4 zeros no início
                - p é a proof anterior e p' é a nova proof
            
            :param: last_proof: <int>
            :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
            Valida a prova: hash(last_proof, proof) contém 4 zeros no início?
            :param last_proof: <init> Proof anteiror
            :param proof: <int> Proof atual
            :return: <bool> True se correto, False se não.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


    def valid_chain(self, chain):
        """
            Determina se uma blockchain é válida
            :param chain: <list> Uma blockchain
            :return: <bool> True se válido, False se não.
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")

            #Checa se o hash está correto
            if block['previous_hash'] != self.hash(last_block):
                return False
            
            #Checa se a Proof of Work está correta
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            
            last_block = block
            current_index += 1
        
        return True
    
    def resolve_conflicts(self):
        """
            Algoritmo de Consenso. Ele resolve conflitos substituindo
            nossa cadeia pela mais longa da rede.
            :return: <bool> True se a cadeia foi substituída, False se não
        """

        neighbours = self.nodes
        new_chain = None
        
        # Procuramos apenas por cadeias mais longas
        max_lenght = len(self.chain)

        # Seleciona e verifica cadeias de todos os nós da rede
        for node in neighbours:
            response = request.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # checa se o comprimento é maior e se a cadeia é válida
                if length > max_length and self.valid_chain(chain):
                    max_lenght = length
                    new_chain = chain
            
            # Substitui nossa cadeia se descobrirmos uma nova cadeia válida e maior
            if new_chain:
                self.chain = new_chain
                return True
            
            return False