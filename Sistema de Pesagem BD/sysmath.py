import serial
import re
import mysql.connector
from datetime import datetime
import os
from tkinter import *
from tkinter import messagebox
from tkinter import ttk

# Variável global da entrada serial
ser = None
ultimo_registrado = None
ultimo_peso_detectado = None

# Variáveis para armazenar os resultados das validações
peso_detectado = None
linha = None
local_perda = None
tipo_qr = None
maquina = None
motivo = None
cliente_id = None 

# Conectar ao banco SQL
conexao = mysql.connector.connect(
    host = "35.247.232.2",
    user = "admin_perdas",
    password = "Tututu@902",
    database = "registro_perdas"
)

# Verifica e conecta à porta COM
def conectar_porta_serial():
    global ser
    portas = ['COM10']
    for porta in portas:
        try:
            ser = serial.Serial(
                port=porta,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"Conexão estabelecida na {porta}.")
            return  
        except serial.SerialException:
            print(f"Erro: Não foi possível conectar à {porta}. Tentando a próxima porta...")
    
    print("Erro: Não foi possível conectar à nenhuma das portas (COM).")
    exit()

def validar_qr(tipo, entrada, campo_entry, proximo_campo):
    global linha, local_perda, tipo_qr, maquina, motivo, cliente_id

    # Dicionário para mapeamento do tipo de entrada para a tabela correspondente
    tabelas = {
        'Linha': 'linha',
        'Local': 'local_perda',
        'Tipo': 'tipo',
        'Máquina': 'maquina',
        'Motivo': 'motivo',
        'Cliente': 'cliente_id'
    }

    # Verifica se o tipo fornecido existe no dicionário de tabelas
    if tipo not in tabelas:
        print(f"Erro: Tipo '{tipo}' não encontrado nas tabelas definidas.")
        return

    # Pegar o nome da tabela correspondente a partir do dicionário tabelas
    tabela = tabelas[tipo]

    # Conectar ao banco e verificando se o valor existe
    try:
        cursor = conexao.cursor()  # O cursor permite executar comandos SQL no banco de dados

        # A consulta agora vai verificar o valor na coluna correspondente à tabela, que é o nome da tabela
        query = f"SELECT {tabela} FROM {tabela} WHERE {tabela} = %s"
        cursor.execute(query, (entrada,))  # Executa a consulta no banco de dados
        resultado = cursor.fetchone()  # Obtém o resultado da consulta
        cursor.close()  # Fecha o cursor após a execução

        # Se o resultado não for None, significa que o QR code existe no banco
        if resultado:
            campo_entry.delete(0, END)  # Remove qualquer texto dentro do campo de entrada (campo_entry)
            campo_entry.insert(0, entrada)  # Insere o valor válido do QR code diretamente no campo
            campo_entry.config(state='disabled')  # Desativa o campo para evitar edição manual

            # Atualiza a variável correspondente ao tipo
            if tipo == 'Linha':
                linha = entrada
            elif tipo == 'Local':
                local_perda = entrada
            elif tipo == 'Tipo':
                tipo_qr = entrada
            elif tipo == 'Máquina':
                maquina = entrada
            elif tipo == 'Motivo':
                motivo = entrada
            elif tipo == 'Cliente':
                cliente_id = entrada

            # Se o tipo for "Cliente", já realiza o registro automaticamente
            if tipo == 'Cliente':
                registrar_sql()  # Chama a função para registrar os dados no banco de dados

            # Pular para o próximo campo, se houver
            if proximo_campo:
                proximo_campo.focus_set()

        else:
            # Se QR code for inválido, limpa o campo e mantém o foco no campo atual
            campo_entry.delete(0, END)  # Limpa o campo de entrada
            campo_entry.focus_set()  # Retorna o foco para o campo de entrada, permitindo nova tentativa
            print(f"QR code '{entrada}' inválido para {tipo}. Tente novamente.")  # Mensagem de erro para o usuário

    except mysql.connector.Error as err:
        print(f"Erro ao validar {tipo}: {err}")

# Busca o último peso registrado na tabela perdas
def ultimo_peso_registrado():
    try:
        cursor = conexao.cursor()
        query = f"SELECT peso FROM perdas ORDER BY data_perda DESC, hora DESC LIMIT 1"
        cursor.execute(query) # Executa a consulta
        resultado = cursor.fetchone() # Obtém o resultado da consulta
        cursor.close()

        # Se encontrar um peso, retorna o valor
        if resultado:
            return resultado[0] # Retorna o peso encontrado
        else:
            return None # Se não houver registros, retorna None
    except mysql.connector.Error as err:
        print(f"Erro ao buscar último peso: {err}")
        return None
    
# Função para exibir mensagem de sucesso ao registrar pesagem
def exibir_mensagem_sucesso():
    sucesso_janela = Toplevel()
    sucesso_janela.title("Sucesso")
    sucesso_janela.geometry("300x100")
    sucesso_janela.config(bg="#2ecc71") # Cor de fundo verde (sucesso)

    Label(sucesso_janela, text="A pesagem foi registrada!", font=("Arial", 12), fg="white", bg="#2ecc71").pack(expand=True)

    # Fechar automaticamente após 1,5 segundos
    sucesso_janela.after(1500, sucesso_janela.destroy)

# Registrar a pesagem no banco de dados
def registrar_sql():
    global peso_detectado, linha, local_perda, tipo_qr, maquina, motivo, cliente_id

    if not (peso_detectado and linha and local_perda and tipo_qr and maquina and motivo and cliente_id):
        messagebox.showerror("Erro", "Preencha todos os campos")
        return
    
    peso_formatado = float(peso_detectado) / 100000000
    peso_formatado = f"{peso_formatado:.2f}"

    # Verifica o último peso registrado para evitar duplicidade
    ultimo_peso = ultimo_peso_registrado()
    if peso_formatado == ultimo_peso:
        messagebox.showwarning("Aviso", f"Peso {peso_formatado} já foi registrado. Registro não realizado.")
        return
    
    try:
        cursor = conexao.cursor()

        # Inserir no banco de dados
        query = """INSERT INTO perdas (data_perda, hora, peso, linha, local_perda, tipo, maquina, motivo, cliente_id) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        data_atual = datetime.now().strftime('%Y-%m-%d')
        hora_atual = datetime.now().strftime('%H:%M:%S')


        # Executar a query de inserção
        cursor.execute(query, (data_atual, hora_atual, peso_formatado, linha, local_perda, tipo_qr, maquina, motivo, cliente_id))
        conexao.commit() # Confirma a transação

        cursor.close()
    
        # Exibir mensagem de conclusão com a função
        exibir_mensagem_sucesso()

        # Limpa os campos e reinicia o sistema de leitura
        limpar_campos()
        reiniciar_leitura()
        recarregar_sistema()

        # Atualizar a interface com a lista de registros
        atualizar_lista_registros()
    
    except mysql.connector.Error as err:
        print(f"Erro ao registrar dados: {err}")
        messagebox.showerror("Erro", "Erro ao registrar dados no banco de dados SQL")


# Função para ler o peso da balança
def ler_peso():
    global ultimo_registrado, ultimo_peso_detectado, peso_detectado

    if ser and ser.in_waiting > 0:
        data = ser.read(ser.in_waiting).decode('ascii', errors='ignore').strip()
        pesos = re.findall(r'\d+', data)
        
        if pesos:
            ultimo_peso = pesos[-1]
            ultimo_peso_sem_zero = str(int(ultimo_peso))

            if ultimo_peso_detectado == ultimo_peso_sem_zero:
                messagebox.showwarning("Aviso", f"Peso duplicado detectado: {ultimo_peso_sem_zero}")
                reiniciar_leitura()  # Reinicia a leitura para não esperar pela confirmação do usuário
                return

            if (ultimo_peso_sem_zero 
                and ultimo_peso_sem_zero != ultimo_registrado 
                and int(ultimo_peso_sem_zero) != 0 
                and (len(ultimo_peso_sem_zero) in [8, 9, 10])):

                peso_detectado = ultimo_peso_sem_zero

                # Formatação para exibição na interface
                peso_formatado = float(peso_detectado) / 100000000
                peso_formatado = f"{peso_formatado:.3f}".replace(".", ",")
                peso_label.config(text=f"Peso detectado: {peso_formatado} kg")

                ultimo_peso_detectado = ultimo_peso_sem_zero

                # Ao ler o peso, o foco vai automaticamente para o campo "Linha"
                entry_linha.focus_set()

            else:
                reiniciar_leitura()  # Reinicia a leitura ao invés de mostrar a mensagem de erro

        else:
            reiniciar_leitura()  # Reinicia a leitura ao invés de mostrar a mensagem de erro
    else:
        messagebox.showinfo("Aguardando", "Aguardando peso...")

# Função para limpar os campos de entrada
def limpar_campos():
    global peso_detectado, linha, local, tipo_qr, maquina, motivo, cliente_id
    
    peso_detectado = None
    linha = None
    local = None
    tipo_qr = None
    maquina = None
    motivo = None
    cliente_id = None

    for entry in entries.values():
        entry.delete(0, END)
        entry.config(state=NORMAL)

    peso_label.config(text="Peso não detectado.")

# Função para reiniciar a leitura de peso
def reiniciar_leitura():
    global ser
    if ser:
        ser.reset_input_buffer()  # Limpa o buffer para garantir uma nova leitura limpa

# Função para recarregar o sistema (limpar todos os campos)
def recarregar_sistema():
    limpar_campos()
    peso_label.config(text="Peso não detectado.")
    ser.reset_input_buffer()  # Limpa o buffer para nova leitura

# Função para atualizar a lista de registros na interface
def atualizar_lista_registros():
    # Limpa todos os registros existentes na Treeview
    for row in treeview.get_children():
        treeview.delete(row)

    # Conecta ao banco de dados
    conexao = mysql.connector.connect(
        host="35.247.232.2",
        user="admin_perdas",
        password="Tututu@902",
        database="registro_perdas"
    )
    cursor = conexao.cursor()

    # Busca os últimos 50 registros da tabela 'perdas', ordenando pelas colunas 'data_perda' e 'hora' (mais recentes primeiro)
    query = "SELECT * FROM perdas ORDER BY data_perda DESC, hora DESC LIMIT 50"
    cursor.execute(query)
    registros = cursor.fetchall()


    # Insere os registros na Treeview
    for registro in registros:
        treeview.insert("", "end", values=registro)

    # Fecha a conexão com o banco de dados
    cursor.close()
    conexao.close()

# Iniciar a conexão
conectar_porta_serial()

# Criação da interface gráfica com Tkinter
janela = Tk()
janela.title("Registro de Peso")
janela.config(bg="#0d2a47") # Azul mais escuro

# Estilo da interface
font = ("Arial", 12)
label_color = "#ecf0f1"
button_color = "#3498db"  # Azul mais claro
button_color_sair = "#ff0000"
entry_bg = "#34495e"
entry_fg = "#ecf0f1"

peso_label = Label(janela, text="Peso não detectado.", font=("Arial", 14), fg=label_color, bg="#1f3a5f")
peso_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="nsew")

ler_button = Button(janela, text="Ler Peso", font=font, bg=button_color, fg=label_color, command=ler_peso)
ler_button.grid(row=1, column=0, columnspan=2, pady=5, sticky="nsew")

# Campos de entrada com validação automática e legendas
campos = ['Linha', 'Local', 'Tipo', 'Máquina', 'Motivo', 'Cliente']
entries = {}

# Campo de entrada para Linha
label_linha = Label(janela, text="Bipe o QR code da Linha:", font=("Arial", 15), fg=label_color, bg="#1f3a5f", width=50)
label_linha.grid(row=2, column=0, sticky="w", padx=10, pady=5)
entry_linha = Entry(janela, font=font, bg=entry_bg, fg=entry_fg, width=60)
entry_linha.grid(row=2, column=1, pady=5, sticky="nsew")
entries['Linha'] = entry_linha

# Campos para os outros QR codes
for i, campo in enumerate(campos[1:], start=3):  # Começa de 'Local' em diante
    label = Label(janela, text=f"Bipe o QR code de {campo}:", font=("Arial", 15), fg=label_color, bg="#1f3a5f", width=50)
    label.grid(row=i, column=0, sticky="w", padx=10, pady=5)
    entry = Entry(janela, font=font, bg=entry_bg, fg=entry_fg, width=60)
    entry.grid(row=i, column=1, pady=5, sticky="nsew")
    entries[campo] = entry

# Função para mover o foco para o próximo campo
def mudar_foco(campo_atual, proximo_campo):
    if proximo_campo:
        proximo_campo.focus_set()

# Vincula o evento de "Enter" para mudar de campo
for i, campo in enumerate(campos):
    entry = entries[campo]
    proximo_campo = entries[campos[i + 1]] if i + 1 < len(campos) else None
    
    # Ao pressionar "Enter", chama a função para validar e mudar de campo
    entry.bind("<Return>", lambda event, campo=campo, entry=entry, proximo_campo=proximo_campo: (
        validar_qr(campo, entry.get(), entry, proximo_campo)
    ))

# Botão de sair
sair_button = Button(janela, text="Sair", font=font, bg=button_color_sair, fg=label_color, command=janela.quit)
sair_button.grid(row=len(campos)+3, column=0, columnspan=2, pady=5, sticky="nsew")

# Botão de recarregar
recarregar_button = Button(janela, text="Recarregar", font=font, bg=button_color, fg=label_color, command=recarregar_sistema)
recarregar_button.grid(row=len(campos)+4, column=0, columnspan=2, pady=5, sticky="nsew")

# Tabela para exibir registros
treeview = ttk.Treeview(janela, columns=["Data", "Hora", "Peso", "Linha", "Local", "Tipo", "Máquina", "Motivo", "Cliente"], show="headings")
treeview.grid(row=len(campos)+5, column=0, columnspan=2, pady=10, sticky="nsew")

treeview.heading("Data", text="Data")
treeview.heading("Hora", text="Hora")
treeview.heading("Peso", text="Peso")
treeview.heading("Linha", text="Linha")
treeview.heading("Local", text="Local")
treeview.heading("Tipo", text="Tipo")
treeview.heading("Máquina", text="Máquina")
treeview.heading("Motivo", text="Motivo")
treeview.heading("Cliente", text="Cliente") 

# Ajuste o sticky para expandir em todas as direções
treeview.grid(row=len(campos)+5, column=0, columnspan=2, pady=10, sticky="nsew")

# Permitir que a linha do treeview se expanda verticalmente
janela.grid_rowconfigure(len(campos)+5, weight=1)

# Criando a barra de rolagem horizontal (opcional, caso necessário)
scrollbar_horizontal = ttk.Scrollbar(janela, orient="horizontal", command=treeview.xview)
scrollbar_horizontal.grid(row=len(campos)+6, column=0, columnspan=2, sticky="ew")

# Configurando a Treeview para usar as barras de rolagem
treeview.configure(xscrollcommand=scrollbar_horizontal.set)

# Ajustando a linha para permitir a expansão da Treeview
janela.grid_rowconfigure(len(campos)+5, weight=1)
janela.grid_columnconfigure(0, weight=1)
janela.grid_columnconfigure(1, weight=1)

# Inicia o loop da interface gráfica
janela.mainloop()
