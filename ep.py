import random
from typing import List, Dict, Tuple, Set
from collections import defaultdict

class Time:
    """Classe que representa um time de futebol"""
    def __init__(self, nome: str, cidade: str, torcedores: int):
        self.nome = nome
        self.cidade = cidade
        self.torcedores = torcedores

    def __repr__(self):
        return self.nome

class Partida:
    """Representa uma partida entre dois times"""
    def __init__(self, mandante: Time, visitante: Time, rodada: int):
        self.mandante = mandante
        self.visitante = visitante
        self.rodada = rodada

    def __repr__(self):
        return f"{self.mandante} x {self.visitante} (Rodada {self.rodada})"

class Campeonato:
    """Classe principal que implementa o algoritmo genético para organizar o campeonato"""

    def __init__(self, times: List[Time], num_rodadas: int = 26, tamanho_populacao: int = 100):
        self.times = times
        self.num_times = len(times)
        self.num_rodadas = num_rodadas
        self.tamanho_populacao = tamanho_populacao
        self.jogos_por_rodada = self.num_times // 2

        # Times grandes (5 maiores por torcida)
        self.times_grandes = sorted(times, key=lambda x: -x.torcedores)[:5]

        # Gerar todos os confrontos possíveis (turno e returno)
        self.todos_jogos = []
        for i in range(self.num_times):
            for j in range(self.num_times):
                if i != j:
                    self.todos_jogos.append((times[i], times[j]))

    def gerar_populacao_inicial(self) -> List[List[Partida]]:
        """Gera uma população inicial de calendários aleatórios"""
        populacao = []
        for _ in range(self.tamanho_populacao):
            calendario = []
            jogos_disponiveis = self.todos_jogos.copy()
            random.shuffle(jogos_disponiveis)

            for rodada in range(1, self.num_rodadas + 1):
                jogos_rodada = []
                times_na_rodada = set()
                cidades_na_rodada = set()

                while len(jogos_rodada) < self.jogos_por_rodada and jogos_disponiveis:
                    jogo = jogos_disponiveis.pop(0)
                    mandante, visitante = jogo

                    # Verifica restrições
                    if (mandante not in times_na_rodada and
                        visitante not in times_na_rodada and
                        mandante.cidade not in cidades_na_rodada):

                        jogos_rodada.append(Partida(mandante, visitante, rodada))
                        times_na_rodada.add(mandante)
                        times_na_rodada.add(visitante)
                        cidades_na_rodada.add(mandante.cidade)

                calendario.extend(jogos_rodada)

            populacao.append(calendario)

        return populacao

    def calcular_fitness(self, calendario: List[Partida]) -> float:
        """Calcula a qualidade de um calendário considerando as restrições"""
        penalidades = 0

        # Verifica se todos os jogos foram agendados
        if len(calendario) != len(self.todos_jogos):
            penalidades += 1000 * (len(self.todos_jogos) - len(calendario))

        # Verifica restrições por rodada
        rodadas = defaultdict(list)
        for partida in calendario:
            rodadas[partida.rodada].append(partida)

        for rodada, jogos in rodadas.items():
            times_rodada = set()
            cidades_rodada = set()
            classicos_rodada = 0

            for jogo in jogos:
                # 1. Time não pode jogar mais de uma vez por rodada
                if jogo.mandante in times_rodada or jogo.visitante in times_rodada:
                    penalidades += 100

                times_rodada.add(jogo.mandante)
                times_rodada.add(jogo.visitante)

                # 2. Cidade não pode ter mais de um jogo por rodada
                if jogo.mandante.cidade in cidades_rodada:
                    penalidades += 50

                cidades_rodada.add(jogo.mandante.cidade)

                # 3. Verifica clássicos (entre os 5 maiores times)
                if (jogo.mandante in self.times_grandes and
                    jogo.visitante in self.times_grandes):
                    classicos_rodada += 1

            # 4. Não pode ter mais de um clássico por rodada
            if classicos_rodada > 1:
                penalidades += 200 * (classicos_rodada - 1)

        # Verifica se todos os confrontos foram agendados (turno e returno)
        confrontos_agendados = defaultdict(int)
        for partida in calendario:
            confronto = (partida.mandante, partida.visitante)
            confrontos_agendados[confronto] += 1

        for jogo in self.todos_jogos:
            if confrontos_agendados[jogo] != 1:
                penalidades += 300

        # Fitness é inversamente proporcional às penalidades
        return 1 / (1 + penalidades)

    def selecionar_pais(self, populacao: List[List[Partida]]) -> List[List[Partida]]:
        """Seleção por torneio"""
        pais = []
        for _ in range(2):
            participantes = random.sample(populacao, 3)
            melhor = max(participantes, key=lambda x: self.calcular_fitness(x))
            pais.append(melhor)
        return pais

    def crossover(self, pai1: List[Partida], pai2: List[Partida]) -> List[Partida]:
        """Crossover personalizado para o problema"""
        # Escolhe um ponto de corte aleatório
        ponto_corte = random.randint(0, len(pai1) - 1)

        # Cria filho com a primeira parte do pai1
        filho = pai1[:ponto_corte]

        # Adiciona jogos do pai2 que não estão no filho e não violam restrições
        jogos_filho = {(p.mandante, p.visitante) for p in filho}

        for partida in pai2:
            confronto = (partida.mandante, partida.visitante)
            if confronto not in jogos_filho:
                filho.append(partida)
                jogos_filho.add(confronto)

        return filho

    def mutacao(self, calendario: List[Partida]) -> List[Partida]:
        """Operador de mutação"""
        if random.random() < 0.1:  # 10% de chance de mutação
            # Escolhe duas partidas aleatórias para trocar
            idx1, idx2 = random.sample(range(len(calendario)), 2)
            calendario[idx1], calendario[idx2] = calendario[idx2], calendario[idx1]

        return calendario

    def reparar_calendario(self, calendario: List[Partida]) -> List[Partida]:
        """Tenta consertar violações de restrições"""
        # Agrupa partidas por rodada
        rodadas = defaultdict(list)
        for partida in calendario:
            rodadas[partida.rodada].append(partida)

        calendario_reparado = []

        for rodada, jogos in rodadas.items():
            times_usados = set()
            cidades_usadas = set()
            jogos_validos = []

            for jogo in jogos:
                # Verifica se o jogo pode ser incluído sem violar restrições
                if (jogo.mandante not in times_usados and
                    jogo.visitante not in times_usados and
                    jogo.mandante.cidade not in cidades_usadas):

                    jogos_validos.append(jogo)
                    times_usados.add(jogo.mandante)
                    times_usados.add(jogo.visitante)
                    cidades_usadas.add(jogo.mandante.cidade)

            calendario_reparado.extend(jogos_validos)

        return calendario_reparado

    def executar(self, geracoes: int = 100) -> Tuple[List[Partida], float]:
        """Executa o algoritmo genético"""
        populacao = self.gerar_populacao_inicial()
        melhor_calendario = max(populacao, key=lambda x: self.calcular_fitness(x))
        melhor_fitness = self.calcular_fitness(melhor_calendario)

        print(f"Geração 0 - Melhor fitness: {melhor_fitness:.4f}")

        for geracao in range(1, geracoes + 1):
            nova_populacao = []

            # Elitismo: mantém o melhor indivíduo
            nova_populacao.append(melhor_calendario)

            while len(nova_populacao) < self.tamanho_populacao:
                # Seleciona pais
                pais = self.selecionar_pais(populacao)

                # Aplica crossover
                filho = self.crossover(pais[0], pais[1])

                # Aplica mutação
                filho = self.mutacao(filho)

                # Repara o calendário se necessário
                filho = self.reparar_calendario(filho)

                nova_populacao.append(filho)

            populacao = nova_populacao

            # Atualiza o melhor calendário
            melhor_atual = max(populacao, key=lambda x: self.calcular_fitness(x))
            fitness_atual = self.calcular_fitness(melhor_atual)

            if fitness_atual > melhor_fitness:
                melhor_calendario = melhor_atual
                melhor_fitness = fitness_atual

            if geracao % 10 == 0:
                print(f"Geração {geracao} - Melhor fitness: {melhor_fitness:.4f}")

        return melhor_calendario, melhor_fitness

def main():
    # Definindo os times do campeonato
    times = [
        Time("Campos FC", "Campos", 23000),
        Time("Guardiões FC", "Guardião", 40000),
        Time("CA Protetores", "Guardião", 20000),
        Time("SE Leões", "Leão", 40000),
        Time("Simba EC", "Leão", 15000),
        Time("SE Granada", "Granada", 10000),
        Time("CA Lagos", "Lagos", 20000),
        Time("Solaris EC", "Ponte-do-Sol", 30000),
        Time("Porto FC", "Porto", 45000),
        Time("Ferroviária EC", "Campos", 38000),
        Time("Portuários AA", "Porto", 12000),
        Time("CA Azedos", "Limões", 18000),
        Time("SE Escondidos", "Escondidos", 50000),
        Time("Secretos FC", "Escondidos", 25000)
    ]

    # Configuração do algoritmo genético
    campeonato = Campeonato(times, num_rodadas=26, tamanho_populacao=100)

    # Executa o algoritmo
    melhor_calendario, fitness = campeonato.executar(geracoes=50)

    # Exibe os resultados
    print("\n=== Melhor Calendário Encontrado ===")
    print(f"Fitness: {fitness:.4f}")
    print(f"Total de jogos agendados: {len(melhor_calendario)}")
    print(f"Jogos esperados: {len(campeonato.todos_jogos)}")

    # Organiza por rodada para exibição
    rodadas = defaultdict(list)
    for partida in melhor_calendario:
        rodadas[partida.rodada].append(partida)

    print("\n=== Jogos por Rodada ===")
    for rodada in sorted(rodadas.keys()):
        print(f"\nRodada {rodada}:")
        for jogo in rodadas[rodada]:
            print(f"  {jogo.mandante} x {jogo.visitante} ({jogo.mandante.cidade})")

if __name__ == "__main__":
    main()
