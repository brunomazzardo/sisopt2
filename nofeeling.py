# coding=utf-8
from codigo.struct import Process, Page
import time
import sys


class Logic:
    def __init__(self):
        self.contador_tempo = time.clock()
        self.MAX_PROCS = 15

    def run(self):

        sys.stdout = open('file', 'w')
        f = open('./entrada.txt', 'r')

        self.tamanho_pagina = int(f.readline())
        self.tamanho_memoria = int(f.readline()) / self.tamanho_pagina
        self.tamanho_disco = int(f.readline()) / self.tamanho_pagina
        self.processos = [
            Process(0, 0, 0, [Page(0, 0, 0, 0, 0, 0) for _ in range(0, self.tamanho_memoria + self.tamanho_disco)]) for
            _ in range(self.MAX_PROCS)]
        self.memory = [Page(0, 0, 0, 0, 0, 0) for _ in range(0, self.tamanho_memoria)]
        self.disk = [Page(0, 0, 0, 0, 0, 0) for _ in range(0, self.tamanho_disco)]

        self.disco_livre = self.tamanho_disco
        self.memoria_livre = self.tamanho_memoria

        print 'Tamanho da pagina: ' + str(self.tamanho_memoria)
        print 'Tamanho da memoria: ' + str(self.tamanho_memoria)
        print 'Tamanho do disco: ' + str(self.tamanho_disco)

        for linha in f:
            acao, nome, tam = linha.split(' ')
            tam = tam.rstrip()
            if acao == 'C':
                self.criar(int(nome[1:2]), int(tam))
            elif acao == 'A':
                self.acessar(int(nome[1:2]), int(tam))
            else:
                self.modificar(int(nome[1:2]), int(tam))

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
            print 'Não da pra cirar, puca memoria'
            return
        if page_req > self.memoria_livre:
            print 'Pages in memory required\nBefore:\n'
            self.status()
            self.send_to_disk(page_req - self.memoria_livre)
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
        print str(nome) + ' processo criado com ' + str(tam) + 'com sucesso'
        self.memoria_livre -= page_req

    def acessar(self, nome, tam):

        if nome > self.MAX_PROCS or nome < 0:
            print 'OUT OF BOUNDS' + str(nome[1:2])
            return
        if not self.processos[nome].em_uso:
            print 'cannot access p{}: processo não inicializado\n'.format(nome)
            return
        if tam >= self.processos[nome].qtd_byte or tam < 0:
            print 'Cannot access p{}: Tried to access byte {} [0, {}]\n'.format(nome, tam,
                                                                                self.processos[nome].qtd_byte - 1)
            return
        page_req = tam / self.tamanho_pagina
        if not self.processos[nome].paginas[page_req].na_memoria:
            print '\nPage Fault: Page {} from p{} not in memory\nBefore:\n'.format(page_req, nome)
            self.status()
            self.bring_from_disk(nome, page_req)
            print 'Depois'
            self.status()
        self.memory[self.processos[nome].paginas[page_req].posicao_memoria].ultimo_acesso = time.clock()
        print  'p{} accessed byte {} from page {}\n '.format(nome, tam, page_req)

    def modificar(self, nome, tam):
        novo_tam = self.processos[nome].qtd_byte + tam
        page_fault = 0

        if nome > self.MAX_PROCS or nome < 0:
            print 'Não deu pra criar o processo de id ' + str(nome[1:2])
            return
        if not self.processos[nome].em_uso:
            print 'processo não existe'
            return
        if novo_tam < self.tamanho_pagina * self.processos[nome].qtd_paginas:
            self.processos[nome].qtd_byte = novo_tam
            print 'p{}d modified. {} new bytes [{}]. 0 new Pages [{}]'.format(nome, tam, novo_tam,
                                                                              self.processos[nome].qtd_paginas)
            return
        tam_extra = novo_tam - self.tamanho_pagina * self.processos[nome].qtd_paginas

        page_req = tam_extra / self.tamanho_pagina

        if tam_extra % self.tamanho_pagina != 0:
            page_req += 1
        if page_req > (self.memoria_livre + self.disco_livre):
            print 'não da pra modificar, pouca memoria'
            return
        if page_req > self.memoria_livre:
            print 'Page Fault: {} Pages in memory required \n Before: \n'.format(page_req - self.memoria_livre)
            self.status()
            self.send_to_disk(page_req - self.memoria_livre)
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
        print 'p{} modified. {} new bytes [{}]. {} new Pages [{}]\n'.format(nome, tam, novo_tam, page_req,
                                                                            self.processos[nome].qtd_paginas)
        self.memoria_livre -= page_req

    def status(self):
        print 'Memoria:     Disk:'
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

    def bring_from_disk(self, nome, page):
        time_now = 22222
        for i in range(self.tamanho_memoria):
            if self.memory[i].ultimo_acesso < time_now:
                lru = i
                time_now = self.memory[i].ultimo_acesso

        outro_nome = self.memory[lru].dono
        outra_page = self.memory[lru].posicao_lista
        disk_pos = self.processos[nome].paginas[page].posicao_memoria
        print 'Page {} from p{}, on Frame {} goes to disk...\n\n'.format(self.memory[lru].posicao_lista,
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

    def send_to_disk(self, amount):
        time_now = 22222
        disk_pos = 0
        for i in range(amount):
            for j in range(0, self.tamanho_memoria):
                print time_now
                if self.memory[j].usando and self.memory[j].ultimo_acesso < time_now:
                    lru = j
                    time_now = self.memory[j].ultimo_acesso
            for c in range(0, self.tamanho_disco):
                if not self.disk[c].usando:
                    disk_pos = c
                    break
            print 'Page {} from {}, on Frame {} goes to disk...\n\n'.format(self.memory[lru].posicao_lista,
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
