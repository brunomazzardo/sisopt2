class Page:

    def __init__(self,na_memoria,usando,dono,posicao_lista,posicao_memoria,ultimo_acesso):
        self.na_memoria = na_memoria
        self.usando = usando
        self.dono = dono
        self.posicao_lista = posicao_lista
        self.posicao_memoria = posicao_memoria
        self.ultimo_acesso = ultimo_acesso


class Process:

    def __init__(self,qtd_byte,qtd_paginas,em_uso,paginas):
        self.qtd_byte = qtd_byte
        self.qtd_paginas = qtd_paginas
        self.em_uso = em_uso
        self.paginas = paginas

#######################################CODIGO#########################################















