import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import random
from selenium.webdriver.chrome.options import Options

# Título da aplicação
st.title("Pesquisa de preço")

# Escopo global para o driver
driver = None

def iniciar_driver():
    """Inicia o driver do Chrome com opções para manter o navegador aberto."""  
    global driver
    if driver is None:
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("detach", True)  # Mantenha o navegador aberto
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            st.success("Driver inicializado com sucesso.")
        except Exception as e:
            st.error(f"Erro ao inicializar o driver: {e}")

def abrir_site(url):
    """Abre o site especificado."""  
    if driver is not None:
        driver.get(url)

def clicar_elemento(by, value, tempo=10):
    """Espera até que o elemento esteja clicável e realiza o clique."""  
    if driver is not None:
        elemento = WebDriverWait(driver, tempo).until(
            EC.element_to_be_clickable((by, value))
        )
        elemento.click()

def inserir_texto(by, value, texto, tempo=10):
    """Espera até que o campo esteja visível e insere o texto."""  
    if driver is not None:
        campo = WebDriverWait(driver, tempo).until(
            EC.visibility_of_element_located((by, value))
        )
        campo.send_keys(texto)

def preparar_pesquisa():
    """Prepara o campo de entrada principal para pesquisa."""  
    clicar_elemento(By.ID, "fake-sbar")
    time.sleep(2)

def executar_codigo():
    # Inicializa o driver
    iniciar_driver()
    
    # Abre o site
    abrir_site("https://precodahora.ba.gov.br")

    # Clica nos botões de navegação e localização
    clicar_elemento(By.CSS_SELECTOR, "i.material-icons")
    time.sleep(3)

    clicar_elemento(By.CSS_SELECTOR, "button.btn-danger.nav-location")
    time.sleep(3)

    clicar_elemento(By.ID, "add-center")
    time.sleep(3)

    # Insere o nome da cidade e seleciona
    inserir_texto(By.CLASS_NAME, "sbar-municipio", "conqu")
    time.sleep(2)
    clicar_elemento(By.CLASS_NAME, "set-mun")
    time.sleep(2)

    # Clica no botão 'APLICAR'
    clicar_elemento(By.ID, "aplicar")
    time.sleep(2)

    # Prepara o campo de entrada para as pesquisas de produto
    preparar_pesquisa()

    # Executa a pesquisa para os produtos adicionados
    if st.session_state.products:  # Verifica se há produtos na lista
        dados_produtos = []  # Lista para armazenar os dados dos produtos

        for produto in st.session_state.products:
            if driver is None:
                st.error("O driver do Selenium não foi inicializado corretamente.")
                break  # Encerra o loop se o driver for None

            try:
                campo_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "top-sbar"))
                )
                campo_input.click()
                campo_input.send_keys(produto)
                time.sleep(random.uniform(1, 3))

                botao_pesquisa = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "i.fa.fa-search"))
                )
                botao_pesquisa.click()
                time.sleep(random.uniform(3, 7))

                # O HTML fornecido
                html = driver.page_source
                # Cria um objeto BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')

                # Encontra a div com a classe flex-item2
                produtos = soup.find_all('div', class_='flex-item2')

                for produto in produtos:
                    dados_produto = {
                        'nome': produto.find('strong').text.strip() if produto.find('strong') else "Não informado",
                         'preco' : produto.find_all('div')[1].text.strip() if len(produto.find_all('div')) > 1 else "Não informado",
                        'codigo_barras' : produto.find_all('div')[2].text.strip().replace("Código de barras: ", "") if len(produto.find_all('div')) > 2 else "Não informado",
                        'data_emissao': produto.find_all('div')[3].text.strip() if len(produto.find_all('div')) > 3 else "Não informado",
                        'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Data e hora da extração
                        'empresa': produto.find_all('div')[4].text.strip() if len(produto.find_all('div')) > 4 else "Não informado",
                        'endereco': produto.find_all('div')[5].text.strip() if len(produto.find_all('div')) > 5 else "Não informado"
                    }

                    # Adiciona os dados do produto à lista
                    dados_produtos.append(dados_produto)

            except Exception as e:
                st.error(f"Ocorreu um erro ao pesquisar o produto '{produto}': {e}")

        # Cria um DataFrame com os dados coletados
        if dados_produtos:
            df_produtos = pd.DataFrame(dados_produtos)

            # Salva os dados em um arquivo CSV, adicionando ao existente
            df_produtos.to_csv('dados_produtos.csv', mode='a', index=False, header=False, encoding='utf-8')

            st.success("Dados salvos em 'dados_produtos.csv'.")
        else:
            st.warning("Nenhum dado foi coletado durante a pesquisa.")
    else:
        st.warning("Nenhum produto na lista para pesquisar.")

# Título do aplicativo
st.subheader("Lista de Produtos")

# Criação de um formulário para entrada de dados do produto
product_input = st.text_input("Nome do Produto (use _ para espaços)")

# Lista para armazenar os produtos
if 'products' not in st.session_state:
    st.session_state.products = []

# Função para formatar a entrada do usuário
def format_product_names(input_string):
    # Substitui underscores por espaços
    formatted_string = input_string.replace("_", " ")
    # Substitui espaços por vírgulas
    formatted_string = formatted_string.replace(" ", ", ")
    # Remove espaços extras ao redor das vírgulas e divide os nomes
    names = [name.strip() for name in formatted_string.split(",") if name.strip()]
    return names

# Adiciona os produtos à lista quando o botão é pressionado
if st.button("Adicionar Produtos"):
    if product_input:  # Verifica se o campo de entrada não está vazio
        new_products = format_product_names(product_input)
        
        for product_name in new_products:
            # Adiciona o nome do produto à lista
            if product_name not in st.session_state.products:
                st.session_state.products.append(product_name)
                st.success(f"Produto '{product_name}' adicionado com sucesso!")
            else:
                st.warning(f"O produto '{product_name}' já está na lista.")
    
    else:
        st.warning("Por favor, insira um nome de produto.")

# Exibe a lista de nomes dos produtos separados por vírgulas
if st.session_state.products:
    product_list = ", ".join(st.session_state.products)
    st.write("### Produtos Adicionados:")
    st.write(product_list)
else:
    st.write("Nenhum produto adicionado ainda.")

# Executa a pesquisa quando o botão for clicado
if st.button('Iniciar Pesquisa'):
    executar_codigo()
