# Programa que realiza e controla o cadastro de nomes através das ações CRUD

nomes = []

def cadastro():
    nome = input("Digite um nome para cadastrar: ")
    nomes.append(nome)
    print(f"Nome ({nome}) cadastro com sucesso!")

def listar():
    if nomes:
        print("Nomes Cadastrados: ")
        for n, nome in enumerate(nomes):
            print(f"{n +1} - {nome}")
    else:
        print("Não há nome cadastrado")

def encontrar():
    nome = input("Digite o nome para conferir se está na lista: ")
    if nome in nomes:
        onde = [i for i, x in enumerate(nomes) if x == nome]
        print(f"O nome ({nome}) está cadastrado na posição {onde}.")
    else:
        print(f"O nome ({nome}) não está cadastrado.")

def excluir():
    nome = input("Digite o nome a ser excluído: ")
    if nome in nomes:
        nomes.remove(nome)
        print(f"O nome ({nome}) foi removido com sucesso!")
    else:
        print(f"O nome ({nome}) não foi encontrado.")

def ordem_alfabetica():
    nomes.sort()
    for n, nome in enumerate(nomes):
        print(f"{n +1} - {nome}")

def ordem_invertida():
    nomes.sort()
    nomes.reverse()
    for n, nome in enumerate(nomes):
        print(f"{n +1} - {nome}")



def menu():
    while True:
        print("\nMenu:")
        print("1. Cadastrar nome:")
        print("2. Listar nomes:")
        print("3. Consultar nome:")
        print("4. Excluir nome:")
        print("5. Ordenar por ordem Alfabética:")
        print("6. Ordenar por ordem Alfabética Invertida:")
        print("7. Sair:")

        opcao = input("Digite a opção desejada: ")

        if opcao == '1':
            cadastro()
        elif opcao == '2':
            listar()
        elif opcao == '3':
            encontrar()
        elif opcao == '4':
            excluir()
        elif opcao == '5':
            ordem_alfabetica()
        elif opcao == '6':
            ordem_invertida()
        elif opcao == '7':
            print("Saindo...")
            break
        else:
            print("Opção inválida!")
menu()