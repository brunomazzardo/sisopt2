# coding=utf-8

# Bruno Barcellos Mazzardo e Lucas Demoliner
# Sistema de paginacao usando lru e aleatorio
# 26/06/2018


from struct import Process, Page
import time
from random import randint
from numpy.random import choice
from threading import Thread


class Logic:
    def __init__(self):
        # Tempo base para o LRU
        self.contador_tempo = time.clock()
        # Maximo de processos que podem existir
        self.MAX_PROCS = 15
        # Numero que threads que podem existir
        self.num_threads = 4
        # Chance de um processo morrer a cada comando
        self.chance_morrer = 0.01
        # Chance de um processo querer alocar mais memoria
        self.chance_alocar = 0.2

    # Funcao que deve ser executada pela thread, recebe o id da thread por parametro
    def thread_func(self, idThread):
        self.criar(idThread, randint(15, 25))
        comando = self.comando_aleatorio()
        while comando != 1:
            if comando == 0:
                self.acessar(idThread, randint(1, 30))
            else:
                self.modificar(idThread, randint(1, 25))
            comando = self.comando_aleatorio()
        self.matar_processo(idThread)

    # Funcao que retorna o comando a ser executado, sendo 0 acessar,1 matar, 2 alocar mais memoria
    def comando_aleatorio(self):
        chance_acessar = 1 - (self.chance_morrer + self.chance_alocar)
        # Uso da biblioteca numpy, que fornece o metodo choice, que permite balancear os odds de uma geracao randomica
        return choice(3, 1, p=[chance_acessar, self.chance_morrer, self.chance_alocar])

    # Funcao que executa o progama, faz leitura do arquivo, inicializa as listas e decide o modo a ser executado
    def run(self):
        f = open('./entrada.txt', 'r')
        # Leitura do modo de execucao
        self.modo = f.readline().rstrip()
        # Leitura do algoritmo
        self.alg = f.readline().rstrip()
        # Leitura do tamanho da pagina
        self.tamanho_pagina = int(f.readline())
        # Leitura do tamanho da memoria
        self.tamanho_memoria = int(f.readline()) / self.tamanho_pagina
        # Leitura do tamanho do disco
        self.tamanho_disco = int(f.readline()) / self.tamanho_pagina
        # Inicializando a lista de processos
        self.processos = [
            Process(0, 0, 0, [Page(0, 0, 0, 0, 0, 0) for _ in range(0, self.tamanho_memoria + self.tamanho_disco)]) for
            _ in range(self.MAX_PROCS)]
        # Inicializando a memoria
        self.memory = [Page(0, 0, 0, 0, 0, 0) for _ in range(0, self.tamanho_memoria)]
        # Inicializando o disco
        self.disk = [Page(0, 0, 0, 0, 0, 0) for _ in range(0, self.tamanho_disco)]
        # Definindo a quantidade de disco livre
        self.disco_livre = self.tamanho_disco
        # Definindo a quantidade de disco livre
        self.memoria_livre = self.tamanho_memoria

        print 'Tamanho da pagina: ' + str(self.tamanho_memoria)
        print 'Tamanho da memoria: ' + str(self.tamanho_memoria)
        print 'Tamanho do disco: ' + str(self.tamanho_disco)

        # Dependendo do modo, procede com os comandos
        if self.modo == 'sequencial':
            for linha in f:
                data = linha.split(' ')
                acao = data[0]
                nome = data[1]
                if data.__len__() > 2:
                    tam = data[2]
                    tam = tam.rstrip()
                if acao == 'C':
                    print '[C p{} {}]'.format(int(nome[1:2]), int(tam))
                    self.criar(int(nome[1:2]), int(tam))
                elif acao == 'A':
                    print '[A p{} {}]'.format(int(nome[1:2]), int(tam))
                    self.acessar(int(nome[1:2]), int(tam))
                elif acao == 'M':
                    print '[M p{} {}]'.format(int(nome[1:2]), int(tam))
                    self.modificar(int(nome[1:2]), int(tam))
                elif acao == 'T':
                    print '[T p{}]'.format(int(nome[1:2]))
                    self.matar_processo(int(nome[1:2]))
        elif self.modo == 'aleatorio':
            for _ in range(self.num_threads):
                Thread(target=self.thread_func, args=[_]).start()

    # Funcao que cria um processo, recebe seu id e seu nome
    def criar(self, nome, tam):
        if nome > self.MAX_PROCS or nome < 0:
            print 'Não deu pra criar o processo de id ' + str(nome[1:2])
            return
        if self.processos[nome].em_uso:
            print 'processo existe'
            return
        page_req = tam / self.tamanho_pagina
        page_fault = False
        if tam % self.tamanho_pagina != 0:
            page_req += 1
        if page_req > (self.memoria_livre + self.disco_livre):
            print 'Não da pra criar, pouca memoria'
            return
        if page_req > self.memoria_livre:
            print 'Pages in memory required\nBefore:\n'
            self.status()
            self.envia_para_disco(page_req - self.memoria_livre)
            page_fault = True

        self.processos[nome].qtd_byte = tam
        self.processos[nome].em_uso = True
        self.processos[nome].qtd_paginas = page_req

        self.processos[nome].paginas = [Page(0, 0, 0, 0, 0, 0) for _ in range(page_req)]
        for cnt in range(0, len(self.processos[nome].paginas)):
            i = 0
            for page in self.memory:
                if not page.usando:
                    page.usando = True
                    page.na_memoria = True
                    page.ultimo_acesso = time.clock() - self.contador_tempo
                    page.dono = nome
                    page.posicao_lista = cnt
                    page.posicao_memoria = i
                    self.processos[nome].paginas[cnt] = page
                    break
                i += 1

        if page_fault:
            print 'Depois '
            self.status()
        print str(nome) + ' processo criado com ' + str(tam) + ' bytes com sucesso'
        self.memoria_livre -= page_req

    # Funcao que acessa um processo, recebe seu nome e o byte que quer acessar
    def acessar(self, nome, tam):

        if nome > self.MAX_PROCS or nome < 0:
            print 'OUT OF BOUNDS' + str(nome[1:2])
            return
        if not self.processos[nome].em_uso:
            print 'Não foi possivel acessar o processo {}: Processo não inicializado\n'.format(nome)
            return
        if tam >= self.processos[nome].qtd_byte or tam < 0:
            print 'Não foi possivel acessar o processo {}: Tentou acessar byte invalida{} [0, {}]\n'.format(nome, tam,
                                                                                                            self.processos[
                                                                                                                nome].qtd_byte - 1)
            return
        page_req = tam / self.tamanho_pagina
        if not self.processos[nome].paginas[page_req].na_memoria:
            print '\nPage Fault: Pagina {} do processo{} não está em memoria\nAntes:\n'.format(page_req, nome)
            self.status()
            self.pega_no_disco(nome, page_req)
            print 'Depois'
            self.status()
        self.memory[self.processos[nome].paginas[page_req].posicao_memoria].ultimo_acesso = time.clock()
        print  'Processo {} accessou o byte numero {} da pagina {}\n '.format(nome, tam, page_req)

    # funcao que modifica um processo, alocando mais espaço, recebe um nome e um espaço extra que é desejado
    def modificar(self, nome, tam):
        novo_tam = self.processos[nome].qtd_byte + tam
        page_fault = 0

        if nome > self.MAX_PROCS or nome < 0:
            print 'Impossivel criar o processo de id ' + str(nome[1:2])
            return
        if not self.processos[nome].em_uso:
            print 'Processo não existente'
            return
        if novo_tam < self.tamanho_pagina * self.processos[nome].qtd_paginas:
            self.processos[nome].qtd_byte = novo_tam
            print 'Processo {} modificado. {} novos bytes [{}]. 0 novas paginas [{}]'.format(nome, tam, novo_tam,
                                                                                             self.processos[
                                                                                                 nome].qtd_paginas)
            return
        tam_extra = novo_tam - self.tamanho_pagina * self.processos[nome].qtd_paginas

        page_req = tam_extra / self.tamanho_pagina

        if tam_extra % self.tamanho_pagina != 0:
            page_req += 1
        if page_req > (self.memoria_livre + self.disco_livre):
            print 'Não é possivel modificar, pouca memoria'
            return
        if page_req > self.memoria_livre:
            print 'Page Fault: {} Necessita de mais memória, enviando processo para disco \n Antes: \n'.format(
                page_req - self.memoria_livre)
            self.status()
            self.envia_para_disco(page_req - self.memoria_livre)
            page_fault = True
        self.processos[nome].qtd_byte = novo_tam
        self.processos[nome].qtd_paginas += page_req

        for i in range(page_req):
            self.processos[nome].paginas.append(Page(0, 0, 0, 0, 0, 0))

        for cnt in range(len(self.processos[nome].paginas) - page_req, len(self.processos[nome].paginas)):
            i = 0
            for page in self.memory:
                if not page.usando:
                    page.usando = True
                    page.na_memoria = True
                    page.ultimo_acesso = time.clock() - self.contador_tempo
                    page.dono = nome
                    page.posicao_lista = cnt
                    page.posicao_memoria = i
                    self.processos[nome].paginas[cnt] = page
                    break
                i += 1

        if page_fault:
            print 'Depois '
            self.status()
        print 'Processo {} modificado. {} novos bytes [{}]. {} novas Paginas [{}]\n'.format(nome, tam, novo_tam,
                                                                                            page_req,
                                                                                            self.processos[
                                                                                                nome].qtd_paginas)
        self.memoria_livre -= page_req

    # funcao que imprime a memoria e disco formatados com seu conteudo
    def status(self):
        print 'Memoria:     Disco:'
        if self.tamanho_memoria > self.tamanho_disco:
            max = self.tamanho_memoria
        else:
            max = self.tamanho_disco
        for i in range(max):
            if i < self.tamanho_memoria:
                if self.memory[i].usando:
                    print '[{}] = p {}, {}          '.format(i, self.memory[i].dono, self.memory[i].posicao_lista),
                else:
                    print '[{}] = --          '.format(i)
            else:
                print '              ',
            if i < self.tamanho_disco:
                if self.disk[i].usando:
                    print '[{}] = p {}, {}          '.format(i, self.disk[i].dono, self.disk[i].posicao_lista),
                else:
                    print '[{}] = --          '.format(i),

            print ''

    # funcao que pega processo do disco,
    def pega_no_disco(self, nome, page):
        time_now = 22222
        print self.alg
        print self.alg == 'lru'
        if self.alg == 'lru':
            for i in range(self.tamanho_memoria):
                if self.memory[i].ultimo_acesso < time_now:
                    lru = i
                    time_now = self.memory[i].ultimo_acesso
        else:
            lru = self.posicao_aleatoria()

        outro_nome = self.memory[lru].dono
        outra_page = self.memory[lru].posicao_lista
        disk_pos = self.processos[nome].paginas[page].posicao_memoria
        print 'Pagina {} do processo {}, no frame {} vai para disco\n\n'.format(self.memory[lru].posicao_lista,
                                                                                self.memory[lru].dono, lru)
        if not self.memory[lru].usando:
            self.memoria_livre -= 1
            self.disco_livre += 1

        temp = self.memory[lru]
        self.memory[lru] = self.disk[disk_pos]
        self.disk[disk_pos] = temp

        self.memory[lru].na_memoria = True
        self.memory[lru].posicao_memoria = lru
        self.memory[lru].dono = nome
        self.memory[lru].posicao_lista = page

        self.disk[disk_pos].na_memoria = False
        self.disk[disk_pos].posicao_memoria = disk_pos
        self.disk[disk_pos].dono = temp.dono
        self.disk[disk_pos].posicao_lista = temp.posicao_lista

        self.processos[nome].paginas[page] = self.memory[lru]
        self.processos[outro_nome].paginas[outra_page] = self.disk[disk_pos]

    def posicao_aleatoria(self):
        for _ in range(self.tamanho_memoria):
            lru = randint(0, self.tamanho_memoria)
            try:
                if self.memory[lru] is not None:
                    return lru
            except IndexError:
                pass

    # funcao que envia para o disco
    def envia_para_disco(self, amount):
        time_now = 22222
        disk_pos = 0
        lru = self.posicao_aleatoria()
        for i in range(amount):
            for j in range(0, self.tamanho_memoria):
                if self.alg == 'lru':
                    if self.memory[j].usando and self.memory[j].ultimo_acesso < time_now:
                        lru = j
                        time_now = self.memory[j].ultimo_acesso
            for c in range(0, self.tamanho_disco):
                if not self.disk[c].usando:
                    disk_pos = c
                    break
            print 'Pagina {} do processo {}, no frame {} vai para disco...\n\n'.format(self.memory[lru].posicao_lista,
                                                                                       self.memory[lru].dono,
                                                                                       lru)
            self.disk[disk_pos].na_memoria = False
            self.disk[disk_pos].usando = True
            self.disk[disk_pos].ultimo_acesso = self.memory[lru].ultimo_acesso
            self.disk[disk_pos].posicao_lista = self.memory[lru].posicao_lista
            self.disk[disk_pos].dono = self.memory[lru].dono
            self.disk[disk_pos].posicao_memoria = disk_pos

            self.memory[lru].usando = False

            self.processos[self.disk[disk_pos].dono].paginas[self.disk[disk_pos].posicao_lista] = self.disk[disk_pos]

        self.memoria_livre += amount
        self.disco_livre -= amount

    # funcao que mata o processo, seta como nao usando, tanto em disco como em memoria, e libera a memoria
    def matar_processo(self, nome):
        self.processos[nome].em_uso = False
        for i in range(0, self.tamanho_memoria):
            if self.memory[i].dono == nome:
                self.memory[i].usando = False
                self.memoria_livre += 1
        for i in range(0, self.tamanho_disco):
            if self.disk[i].dono == nome:
                self.disk[i].usando = False
                self.disco_livre += 1

        print 'Processo {} finalizado'.format(nome)
