import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import time
import os

# -- comprimir (Ghostscript)
import subprocess


def aplicar_estilo():
    estilo = """
    <style>
    h1 {
        color: #e4312c;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
    }
    [data-testid="stSidebar"] {
        background-color: #f7f7f7;
    }
    button {
        background-color: #e4312c !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
    }
    body {
        color: #000000;
    }
    </style>
    """
    st.markdown(estilo, unsafe_allow_html=True)
aplicar_estilo()


def juntar_pdfs(arquivos):
    merger = PdfMerger()

    for arquivo in arquivos:
        merger.append(arquivo)
    caminho_saida = "pdf_juntado.pdf"
    merger.write(caminho_saida)
    merger.close()

    return caminho_saida


@st.cache_data
def dividir_pdf(arquivo, num_partes):
    leitor = PdfReader(arquivo)
    total_paginas = len(leitor.pages)

    # Verificação de divisão
    if num_partes > total_paginas or num_partes < 1:
        return None, total_paginas

    paginas_por_parte = total_paginas // num_partes
    resto = total_paginas % num_partes
    arquivos_saida = {}

    nome_arquivo_original = os.path.basename(arquivo.name) 
    primeira_palavra = nome_arquivo_original.split()[0].split('.')[0]  # Pega a primeira palavra do arquivo original

    inicio = 0
    for i in range(num_partes):
        escritor = PdfWriter()
        fim = inicio + paginas_por_parte + (1 if i < resto else 0)
        for pagina in range(inicio, fim):
            escritor.add_page(leitor.pages[pagina])
        nome_arquivo = f"{primeira_palavra}_parte_{i + 1}.pdf"
        with open(nome_arquivo, "wb") as f:
            escritor.write(f)
        with open(nome_arquivo, "rb") as f:
            arquivos_saida[nome_arquivo] = f.read()
        os.remove(nome_arquivo)
        inicio = fim

    return arquivos_saida, total_paginas


def comprimir_pdf(input_pdf, output_pdf):
    try:
        # Caminho completo para o Ghostscript
        gs_path = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"  # Verifique o caminho correto na sua máquina

        comando = [
            gs_path,  # Use o caminho completo para o Ghostscript
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/screen',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_pdf}',
            input_pdf
        ]
        
        # Executa o comando no sistema
        subprocess.run(comando, check=True)
        print(f"PDF comprimido com sucesso: {output_pdf}")
        
        # Retorna os tamanhos do arquivo original e comprimido
        tamanho_original = os.path.getsize(input_pdf) / (1024 * 1024)  # MB
        tamanho_comprimido = os.path.getsize(output_pdf) / (1024 * 1024)  # MB
        
        return tamanho_original, tamanho_comprimido
    
    except subprocess.CalledProcessError as e:
        print(f"Erro ao processar o PDF: {e}")
        return None, None


# Interface do Streamlit

st.title("Manipulador de PDFs")
st.sidebar.title("Opções")
opcao = st.sidebar.selectbox("Escolha uma ação", ["Juntar PDFs", "Dividir PDF", "Comprimir PDF"])


if opcao == "Juntar PDFs":
    st.header("Juntar PDFs")
    arquivos = st.file_uploader("Envie os arquivos PDF que deseja juntar", type="pdf", accept_multiple_files=True)
    if st.button("Juntar"):
        if arquivos and len(arquivos) > 1:
            caminho_saida = juntar_pdfs(arquivos)
            st.success("PDFs juntados com sucesso!")
            with open(caminho_saida, "rb") as f:
                st.download_button("Baixar PDF Juntado", f, file_name="pdf_juntado.pdf")
            os.remove(caminho_saida)
        else:
            st.error("Envie pelo menos dois arquivos PDF.")


elif opcao == "Dividir PDF":
    st.header("Dividir PDF")
    arquivo = st.file_uploader("Envie o arquivo PDF que deseja dividir", type="pdf")

    if arquivo:
        leitor = PdfReader(arquivo)
        total_paginas = len(leitor.pages)

        # Input para o número de partes
        num_partes = st.number_input(
            "Escolha em quantas partes deseja dividir o PDF",
            min_value=1,
            max_value=total_paginas,
            value=2,
            step=1,
            key="num_partes_input"
        )

        if st.button("Dividir"):
            try:
                arquivos_saida, _ = dividir_pdf(arquivo, num_partes)
                st.success("PDF dividido com sucesso!")
                for nome_arquivo, conteudo in arquivos_saida.items():
                    st.download_button(
                        f"Baixar {nome_arquivo}",
                        data=conteudo,
                        file_name=nome_arquivo
                    )
            except Exception as e:
                st.error(f"Erro ao dividir o PDF: {e}")
    else:
        st.error("Envie um arquivo PDF.")


elif opcao == "Comprimir PDF":
    st.header("Comprimir PDF")
    
    arquivo = st.file_uploader("Envie o arquivo PDF que deseja comprimir", type="pdf", key="comprimir_pdf_uploader")
    
    if arquivo is not None:
        nome_original = arquivo.name
        primeira_palavra = nome_original.split()[0]
        caminho_entrada = "temp_pdf.pdf"
        caminho_saida = f"{primeira_palavra}_comprimido.pdf"
        
        # salva o arquivo temporariamente
        with open(caminho_entrada, "wb") as f:
            f.write(arquivo.read())

        # Comprimir o arquivo
        if st.button("Comprimir"):
            with st.spinner("Comprimindo o PDF... Isso pode levar algum tempo."):
                try:
                    # Chama a função de compressão
                    comprimir_pdf(caminho_entrada, caminho_saida)

                    # Exibe os resultados após a compressão
                    st.success(f"PDF comprimido com sucesso!")

                    # Exibe o tamanho original e comprimido
                    tamanho_original = os.path.getsize(caminho_entrada) / (1024 * 1024)  # em MB
                    tamanho_comprimido = os.path.getsize(caminho_saida) / (1024 * 1024)  # em MB
                    st.write(f"Tamanho original: {tamanho_original:.2f} MB")
                    st.write(f"Tamanho comprimido: {tamanho_comprimido:.2f} MB")

                    # Botão para download do arquivo comprimido
                    with open(caminho_saida, "rb") as f:
                        st.download_button("Baixar PDF Comprimido", f, file_name=caminho_saida)

                    # Remove os arquivos temporários
                    os.remove(caminho_entrada)
                    os.remove(caminho_saida)

                except Exception as e:
                    st.error(f"Erro ao processar o PDF: {e}")
    else:
        st.error("Envie um arquivo PDF para comprimir.")
