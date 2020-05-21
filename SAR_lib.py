# -*- coding: utf-8 -*-

import json
from nltk.stem.snowball import SnowballStemmer
import os
import re
import math


class SAR_Project:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de noticias
        
        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm + ranking de resultado

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """

    # Campos a tokenizar
    fields = [("title", True), ("date", True),
              ("keywords", True), ("article", True),
              ("summary", True)]

    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 10

    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas 

        """
        self.index = {'title': {},
                      'date': {},
                      'keywords': {},
                      'article': {},
                      'summary': {}
                      }  # hash para el indice invertido de terminos --> clave: termino, valor: posting list.
        # Si se hace la implementacion multifield, se pude hacer un segundo nivel de hashing de tal forma que:
        # self.index['title'] seria el indice invertido del campo 'title'.
        self.sindex = {'title': {},
                       'date': {},
                       'keywords': {},
                       'article': {},
                       'summary': {}
                       }  # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {'title': {},
                        'date': {},
                        'keywords': {},
                        'article': {},
                        'summary': {}
                        }  # hash para el indice permuterm.
        # diccionario de terminos --> clave: entero(docid),  valor: ruta del fichero.
        self.docs = {}
        # hash de terminos para el pesado, ranking de resultados. puede no utilizarse
        self.weight = {}
        # hash de noticias --> clave entero (newid), valor: la info necesaria para diferencia la noticia dentro de su fichero
        self.news = {}
        # expresion regular para hacer la tokenizacion
        self.tokenizer = re.compile(r'\W+')
        self.stemmer = SnowballStemmer('spanish')  # stemmer en castellano
        self.show_all = False  # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False  # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False  # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()
        self.doc_cont = 0
        self.new_cont = 0


    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################

    def set_showall(self, v):
        """

        Cambia el modo de mostrar los resultados.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v

    def set_snippet(self, v):
        """

        Cambia el modo de mostrar snippet.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v

    def set_stemming(self, v):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v

    def set_ranking(self, v):
        """

        Cambia el modo de ranking por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON RANKING DE NOTICIAS

        si self.use_ranking es True las consultas se mostraran ordenadas, no aplicable a la opcion -C

        """
        self.use_ranking = v


    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################

    def index_dir(self, root, **args):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Recorre recursivamente el directorio "root"  y indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """

        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']

        # Variable secuencial que representa el id de un fichero
        for dir, _, files in os.walk(root):
            for filename in files:
                if filename.endswith('.json'):
                    fullname = os.path.join(dir, filename)
                    self.index_file(fullname)

        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################
        if self.stemming:
            self.make_stemming()
        if self.permuterm:
            self.make_permuterm()

    def index_file(self, filename):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Indexa el contenido de un fichero.

        Para tokenizar la noticia se debe llamar a "self.tokenize"

        Dependiendo del valor de "self.multifield" y "self.positional" se debe ampliar el indexado.
        En estos casos, se recomienda crear nuevos metodos para hacer mas sencilla la implementacion

        input: "filename" es el nombre de un fichero en formato JSON Arrays (https://www.w3schools.com/js/js_json_arrays.asp).
                Una vez parseado con json.load tendremos una lista de diccionarios, cada diccionario se corresponde a una noticia


        """
        # IMPORTANTE: Se ha implementado el extra 'multifield' y 'positional'
        # Un fichero esta compuesto por noticias, cada noticia por cinco campos y cada campo por unos tokens
        with open(filename) as fh:
            jlist = json.load(fh)
            self.docs[self.doc_cont] = filename

            # Contador de la posición de una noticia en un fichero
            contador_noticia = 0
            for noticia in jlist:
                # Se añade al diccionario de noticias la noticia con clave -> self.new_cont, valor -> (filename, contador_noticia)
                self.news[self.new_cont] = [self.doc_cont, contador_noticia]

                # Campos a tratar
                if self.multifield:
                    multifield = ['title', 'date',
                                  'keywords', 'article', 'summary']
                else:
                    multifield = ['article', 'date']
                for field in multifield:
                    # Se tokeniza el cotenido de cada campo (menos el de date)
                    if field != 'date':
                        contenido = self.tokenize(noticia[field])
                    else:
                        contenido = [noticia[field]]
                    # Contador de la posición de un token en una noticia
                    posicion_token = 0
                    for token in contenido:
                        # Si el token no esta en el diccionario de tokens, se añade
                        if token not in self.index[field]:
                            self.index[field][token] = {
                                self.new_cont: [posicion_token]}
                        # Si el token esta ya
                        else:
                            # Si no existe la noticia en el token
                            if self.new_cont not in self.index[field][token]:
                                self.index[field][token][self.new_cont] = [
                                    posicion_token]
                            else:
                                # Se añade a la entrada del token-noticia la posición donde se ha encontrado
                                self.index[field][token][self.new_cont] += [posicion_token]

                        posicion_token += 1

                self.new_cont += 1

                contador_noticia += 1

            self.doc_cont += 1


    def tokenize(self, text):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens

        """
        return self.tokenizer.sub(' ', text.lower()).split()


    def make_stemming(self):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING.

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        self.stemmer.stem(token) devuelve el stem del token

        """
        # Campos a tratar
        if self.multifield:
            multifield = ['title', 'date', 'keywords', 'article', 'summary']
        else:
            multifield = ['article']
        for field in multifield:
            for token in self.index[field].keys():
                token_s = self.stemmer.stem(token)
                if token_s not in self.sindex[field]:
                    self.sindex[field][token_s] = [token]
                else:
                    if token not in self.sindex[field][token_s]:
                        self.sindex[field][token_s] += [token]
    def make_permuterm(self):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        """
        # Campos a tratar
        if self.multifield:
            multifield = ['title', 'date', 'keywords', 'article', 'summary']
        else:
            multifield = ['article']
        for field in multifield:
            for token in self.index[field]:
                token_p = token + '$'
                permuterm = []
                for _ in range(len(token_p)):
                    token_p = token_p[1:] + token_p[0]
                    permuterm += [token_p]

                for permut in permuterm:
                    if permut not in self.ptindex[field]:
                        self.ptindex[field][permut] = [token]
                    else:
                        if token not in self.ptindex[field][permut]:
                            self.ptindex[field][permut] += [token]

    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Muestra estadisticas de los indices
        
        """
        # Campos a tratar
        if self.multifield:
            multifield = ['title', 'date', 'keywords', 'article', 'summary']
        else:
            multifield = ['article']
        print('\n========================================')
        print('Number of indexed days: {}'.format(
            len(self.index['date'].keys())))
        print('----------------------------------------')
        print('Number of indexed news: {}'.format(len(self.news.keys())))
        print('----------------------------------------')
        print('TOKENS:')
        for field in multifield:
            if field:
                print('     # of tokens in \'{}\': {}'.format(
                    field, len(self.index[field])))
        print('----------------------------------------')
        if self.permuterm:
            for field in multifield:
                if field:
                    print('     # of permuterms in \'{}\': {}'.format(
                        field, len(self.ptindex[field])))
            print('----------------------------------------')
        if self.stemming:
            for field in multifield:
                if field:
                    print('     # of stems in \'{}\': {}'.format(
                        field, len(self.sindex[field])))
            print('----------------------------------------')
        if self.positional:
            print('Positional queries are allowed.')
        else:
            print('Positional queries are NOT allowed.')
        print('========================================')

    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################

    def solve_query(self, query, prev={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """
        # De momento se asume que solo hay NOT, AND y OR
        if query is None or len(query) == 0:
            return []
        else:
            query_aux = query.split(' ')
            procesado = False

            # Primero se resuelven las subconsultas (de forma recursiva por si hay parentesis anidados).
            # Al final, un (...), se transforma en un posting list ([...])
            if '(' in query:
                total_subs = query.count('(')
                while total_subs > 0 and '(' in ' '.join(query_aux):
                    print(query_aux)
                    cont = 0
                    encontrado = False
                    for t in (x for x in query_aux if not encontrado):
                        # Una sola palabra (este caso es sucio, pero bueno...)
                        if t.count('(') + t.count(')') == 2:
                            t = t.replace('(', '')
                            t = t.replace(')', '')
                            query_aux[cont] = self.get_posting(t)
                            encontrado = True
                            total_subs -= 1
                        else:
                            print('NO')
                            s_cont = 1
                            ani_cont = 0
                            while not encontrado:
                                if '(' in query_aux[cont + s_cont]:
                                    ani_cont += 1
                                if ')' in query_aux[cont + s_cont]:
                                    if ani_cont > 0:
                                        ani_cont -= 1
                                    else:
                                        query_aux[cont] = query_aux[cont].replace(
                                            '(', '')
                                        query_aux[s_cont + cont] = query_aux[s_cont +
                                                                             cont].replace(')', '')
                                        query_aux = query_aux[:cont] + self.solve_query(
                                            ' '.join(query_aux[cont: s_cont + cont + 1])) + query_aux[cont + s_cont + 1:]
                                        encontrado = True
                                        total_subs -= 1

                                s_cont += 1

                        cont += 1

            # Luego los posicionals ('"...""')
            if '"' in query:
                print('Pos')
                while '"' in ' '.join(query_aux):
                    cont = 0
                    for t in query_aux:
                        # Una positional de una sola palabra (este caso es sucio, pero bueno...)
                        if t.count('"') == 2:
                            query_aux[cont] = self.get_posting(query_aux[cont])
                        else:
                            s_cont = 1
                            while not ('"') in query_aux[cont + s_cont]:
                                s_cont += 1

                            query_aux = query_aux[:cont] + self.get_posting(
                                ' '.join(query_aux[cont: s_cont + cont + 1])) + query_aux[cont + s_cont + 1:]
                            break

                        cont += 1

                    a = ' '.join(query_aux[cont + 1:])

            # Segundo se procesan los comodines
            # PUEDE QUE SE HAGA SOLO YA
            # if '*' in query or '?' in query:
            #     while '"' in ' '.join(query_aux) or '?' in ' '.join(query_aux):
            #         cont = 0
            #         for t in query_aux:
            #             if '*' in t or '?' in t:
            #                 f, t = t.split(':')
            #                 query_aux[cont] = self.get_posting(t, f)

            #             cont += 1

            # Tercero se procesan los multifield
            if ':' in query:
                if len(query_aux) == 1:
                    procesado = True
                    f, t = query_aux[0].split(':')
                    query_aux[0] = [self.get_posting(t, f)]
                else:
                    a = ' '.join(query_aux)
                    while ':' in a:
                        cont = 0
                        for t in query_aux:
                            if ':' in t:
                                f, t = t.split(':')
                                query_aux[cont] = self.get_posting(t, f)

                            cont += 1

                        a = ' '.join(query_aux[cont + 1:])

            # Si se busca solo una palabras
            if len(query_aux) == 1 and isinstance(query_aux[0], str) and not procesado:
                return self.get_posting(query_aux[0])

            # Primero se procesan los NOT
            while 'NOT' in query_aux:
                pos = query_aux.index('NOT')
                query_aux[pos] = self.reverse_posting(
                    self.get_posting(query_aux[pos + 1]))
                query_aux.pop(pos + 1)

            while 'AND' in query_aux or 'OR' in query_aux:
                pos_and = 999999
                pos_or = 999999
                if 'AND' in query_aux:
                    pos_and = query_aux.index('AND')
                if 'OR' in query_aux:
                    pos_or = query_aux.index('OR')

                pos = min(pos_and, pos_or)

                if pos == pos_and:
                    if not isinstance(query_aux[pos - 1], list):
                        query_aux[pos -
                                  1] = self.get_posting(query_aux[pos - 1])
                    if not isinstance(query_aux[pos + 1], list):
                        query_aux[pos +
                                  1] = self.get_posting(query_aux[pos + 1])

                    query_aux[pos] = self.and_posting(
                        query_aux[pos - 1], query_aux[pos + 1])
                    query_aux.pop(pos + 1)
                    query_aux.pop(pos - 1)

                else:
                    pos = query_aux.index('OR')
                    if not isinstance(query_aux[pos - 1], list):
                        query_aux[pos -
                                  1] = self.get_posting(query_aux[pos - 1])
                    if not isinstance(query_aux[pos + 1], list):
                        query_aux[pos +
                                  1] = self.get_posting(query_aux[pos + 1])

                    query_aux[pos] = self.or_posting(
                        query_aux[pos - 1], query_aux[pos + 1])
                    query_aux.pop(pos + 1)
                    query_aux.pop(pos - 1)

            return query_aux[0]

    def get_posting(self, term, field='article'):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve la posting list asociada a un termino. 
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        res = []

        if '"' in term:
            aux = term.split('"')
            res = self.get_positionals(aux[1].split(' '), field)
        elif '*' in term or '?' in term:
            res = self.get_permuterm(term, field)
        elif self.stemming:
            res = self.get_stemming(term, field)
        else:
            if term in self.index[field]:
                res = list(self.index[field][term].keys())

        return res

    def get_positionals(self, terms, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        Devuelve la posting list asociada a una secuencia de terminos consecutivos.

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        res = []

        # Se comprueba que se ha indexado el primer termino
        if terms[0] in self.index[field]:
            # Se recorre la posting list del primer termino (quitando el número de documentos)
            for post in self.index[field][terms[0]].items():
                seguido = True
                # Obtenemos la noticia y la posición
                new, pos = post
                # Se comprueba que, para los siguientes terminos, eixste una entrada con ese noticia y una posición más
                for term in terms[1:] and seguido:
                    if term in self.index[field]:
                        if new in self.index[field][term]:
                            if pos + 1 in self.index[field][term][new]:
                                pos += 1
                            else:
                                seguido = False
                if seguido:
                    res += new

        return res

    def get_stemming(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING

        Devuelve la posting list asociada al stem de un termino.

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario si se hace la ampliacion de multiples indices

        return: posting list

        """
        stem = self.stemmer.stem(term)
        res = []

        if stem in self.sindex[field]:
            for token in self.sindex[field][stem]:
                res = self.or_posting(
                    res, list(self.index[field][token].keys()))

        return res

    def get_permuterm(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        res = []
        if '*' in term:
            term_a, term_b = term.split('*')
        else:
            term_a, term_b = term.split('?')

        term_a = term_a + '$'
        term_b = '$' + term_b
        
        terms = [term_a, term_b]
        # Se hace la unión de las diferentes posting list de cada termino al que apunta un indice permuterm
        for term in terms:
            if term in self.ptindex[field]:
                for token in self.ptindex[field][term]:
                    res = self.or_posting(
                        res, list(self.index[field][token].keys()))

        return res


    def reverse_posting(self, p):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los newid exceptos los contenidos en p

        """
        # Obtenemos lista de todas las noticias
        res = list(self.news.keys())
        # Recorremos la posting list
        for post in p:
            # Eliminamos la noticia de la lista de todas las noticias
            res.remove(post)

        return res


    def and_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos en p1 y p2

        """
        res = []
        i = 0
        j = 0
        # El pseudocodigo de teoria pasado a Python
        while i < len(p1) and j < len(p2):
            if p1[i] == p2[j]:
                res.append(p1[i])
                i += 1
                j += 1
            elif p1[i] <= p2[j]:
                i += 1
            elif p1[i] >= p2[j]:
                j += 1

        return res


    def or_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 o p2

        """
        res = []
        i = 0
        j = 0

        # El pseudocodigo de teoria pasado a Python
        while i < len(p1) and j < len(p2):
            if p1[i] == p2[j]:
                res.append(p1[i])
                i += 1
                j += 1
            elif p1[i] <= p2[j]:
                res.append(p1[i])
                i += 1
            elif p1[i] >= p2[j]:
                res.append(p2[j])
                j += 1

        for pos in range(i, len(p1)):
            res.append(p1[pos])

        for pos in range(j, len(p2)):
            res.append(p2[pos])

        return res

    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se propone por si os es util, no es necesario utilizarla.

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 y no en p2

        """

        pass
        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################


    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################

    def solve_and_count(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados 

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        result = self.solve_query(query)
        print("%s\t%d" % (query, len(result)))
        return len(result)  # para verificar los resultados (op: -T)

    def solve_and_show(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra informacion de las noticias recuperadas.
        Consideraciones:

        - En funcion del valor de "self.show_snippet" se mostrara una informacion u otra.
        - Si se implementa la opcion de ranking y en funcion del valor de self.use_ranking debera llamar a self.rank_result

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T
        
        """
        result = self.solve_query(query)
        if self.use_ranking:
            result = self.rank_result(result, query)

        print('========================================')

        print('Query: \'{}\''.format(query))
        print('Number of results: {}'.format(len(result)))

        i = 1
        for new in result:
            aux = self.news[new]

            with open(self.docs[self.news[new][0]]) as fh:
                jlist = json.load(fh)
                aux = jlist[self.news[new][1]]

            if not self.show_snippet:
                print('#{:<4} ({}) ({}) ({}) {} ({})'.format(i, self.coseno_rank(
                    result, query), new, aux['date'], aux['title'], aux['keywords']))
            else:
                print('#{}'.format(i))
                print('Score: {}'.format(self.coseno_rank(result, query)))
                print(new)
                print('Date: {}'.format(aux['date']))
                print('Title: {}'.format(aux['title']))
                print('Keywords: {}'.format(aux['keywords']))
                print('{}\n'.format(self.snippet(aux, query)))

            i += 1

            if not self.show_all and i > self.SHOW_MAX:
                break

    def rank_result(self, result, query):
        """
        NECESARIO PARA LA AMPLIACION DE RANKING

        Ordena los resultados de una query.

        param:  "result": lista de resultados sin ordenar
                "query": query, puede ser la query original, la query procesada o una lista de terminos


        return: la lista de resultados ordenada

        """
        res = []

        for new in result:
            res += (new, self.coseno_rank(new, query))

        res.sort(key=lambda tup: tup[1])

        return res

    def coseno_rank(self, new, query):
        '''
        AMPLIACIÓN DE RANKING

        Dada una noticia y una consulta, devuelve su similitud coseno en el rango [0, 1].
        '''
        if not self.use_ranking:
            return 0
        else:
            return -1

    def snippet(self, new, query):
        '''
        Obtiene el snippet de una noticia.
        '''
        words = new['article'].split(' ')
        query = query.split(' ')

        snippet = '"'

        l_cont = 0
        for word in query:
            local = words

            word = word.replace('"', '')
            word = word.replace('*', '')
            word = word.replace('(', '')
            word = word.replace(')', '')
            word = word.replace('?', '')

            if ':' in word:
                field, word = word.split(':')
                if field == 'date':
                    local = new[field].split('-')
                elif field == 'keywords':
                    local = new[field].split(',')
                else:
                    local = new[field].split(' ')

            if word in local:
                pos = local.index(word)
                min_p = pos - 4
                if min_p < 0:
                    min_p = 0
                max_p = pos + 5
                if max_p > len(local) - 1:
                    max_p = len(local) - 1

                snippet_aux = ''
                if min_p > 0:
                    snippet_aux += '...'

                snippet_aux += " ".join(local[min_p:max_p + 1])

                if max_p < len(local) - 1:
                    snippet_aux += '...'

                l_cont += 1

                if l_cont != len(query) - 1 and len(query) > 1 and len(snippet_aux.lstrip()) > 0:
                    snippet_aux += '\n'

                snippet += snippet_aux

        return snippet + '"'