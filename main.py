import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import time
import os
import uuid  # Para gerar identificadores únicos
import subprocess  # Para compressão

import zipfile
import io


st.set_page_config(
    page_title="Manipulador de PDFs",
    page_icon="icon.png"
)

# Aplica estilos customizados
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


# Inicializa o identificador único da sessão
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Garante que arquivos sejam armazenados com nomes únicos
def gerar_caminho_temp(nome_arquivo):
    return os.path.join("arquivos_temporarios", f"temp_{st.session_state['session_id']}_{nome_arquivo}")




def juntar_pdfs(arquivos, ordem):
    merger = PdfMerger()
    for indice in ordem:
        merger.append(arquivos[indice])
    caminho_saida = gerar_caminho_temp("pdf_juntado.pdf")
    merger.write(caminho_saida)
    merger.close()
    return caminho_saida



@st.cache_data
def dividir_pdf(arquivo, num_partes):
    leitor = PdfReader(arquivo)
    total_paginas = len(leitor.pages)
    if num_partes > total_paginas or num_partes < 1:
        return None, total_paginas

    paginas_por_parte = total_paginas // num_partes
    resto = total_paginas % num_partes
    arquivos_saida = {}
    nome_base = os.path.basename(arquivo.name).split()[0].split('.')[0]
    inicio = 0

    for i in range(num_partes):
        escritor = PdfWriter()
        fim = inicio + paginas_por_parte + (1 if i < resto else 0)
        for pagina in range(inicio, fim):
            escritor.add_page(leitor.pages[pagina])
        nome_arquivo = f"{nome_base}_parte_{i + 1}.pdf"  # Nome ajustado conforme solicitado
        caminho_arquivo = gerar_caminho_temp(nome_arquivo)
        with open(caminho_arquivo, "wb") as f:
            escritor.write(f)
        arquivos_saida[nome_arquivo] = caminho_arquivo  # Salva o caminho para o arquivo
        inicio = fim
    return arquivos_saida, nome_base  # Retorna também o nome base do arquivo


def comprimir_pdf(input_pdf, output_pdf):
    gs_path = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
    comando = [
        gs_path,
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/screen',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        f'-sOutputFile={output_pdf}',
        input_pdf
    ]
    subprocess.run(comando, check=True)
    tamanho_original = os.path.getsize(input_pdf) / (1024 * 1024)
    tamanho_comprimido = os.path.getsize(output_pdf) / (1024 * 1024)
    return tamanho_original, tamanho_comprimido


# Interface do Streamlit


st.title("Manipulador de PDFs")
st.sidebar.title("Opções")
opcao = st.sidebar.selectbox("Escolha uma ação", ["Juntar PDFs", "Dividir PDF", "Comprimir PDF"])



if opcao == "Juntar PDFs":
    st.header("Juntar PDFs")
    arquivos = st.file_uploader("Envie os arquivos PDF que deseja juntar", type="pdf", accept_multiple_files=True, key="dividir_pdf_uploader")

    if arquivos:
        st.write("**Defina a ordem desejada para juntar os PDFs:**")
        nomes_arquivos = [arquivo.name for arquivo in arquivos]
        ordem = [i + 1 for i in range(len(nomes_arquivos))]

        for i, nome in enumerate(nomes_arquivos):
            nova_posicao = st.number_input(
                f"Posição para '{nome}'", 
                min_value=1, 
                max_value=len(arquivos), 
                value=ordem[i], 
                step=1, 
                key=f"posicao_{i}"
            )
            if nova_posicao in ordem and nova_posicao != ordem[i]:
                conflito_idx = ordem.index(nova_posicao)
                ordem[conflito_idx] = ordem[i]
            ordem[i] = nova_posicao

        ordem_final = [ordem.index(i + 1) for i in range(len(ordem))]

        if st.button("Juntar", key="juntar_button"):
            caminho_saida = juntar_pdfs(arquivos, ordem_final)
            st.success("PDFs juntados com sucesso!")
            with open(caminho_saida, "rb") as f:
                st.download_button("Baixar PDF Juntado", f, file_name="pdf_juntado.pdf", key="juntar_download_button")
            os.remove(caminho_saida)
    else:
        st.info("Envie os arquivos PDF para começar.")




elif opcao == "Dividir PDF":
    st.header("Dividir PDF")
    arquivo = st.file_uploader("Envie o arquivo PDF que deseja dividir", type="pdf", key="dividir_pdf_uploader")

    if arquivo:
        leitor = PdfReader(arquivo)
        total_paginas = len(leitor.pages)

        num_partes = st.number_input(
            "Escolha em quantas partes deseja dividir o PDF",
            min_value=1,
            max_value=total_paginas,
            value=2,
            step=1,
            key="num_partes_input"
        )

        if st.button("Dividir", key="dividir_button"):
            try:
                arquivos_saida, nome_base = dividir_pdf(arquivo, num_partes)
                st.success("PDF dividido com sucesso!")

                # Criação do arquivo ZIP em memória
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for nome_arquivo, caminho_arquivo in arquivos_saida.items():
                        zip_file.write(caminho_arquivo, nome_arquivo)  # Usa o nome do arquivo ajustado
                        os.remove(caminho_arquivo)  # Remove o arquivo temporário após adicionar ao zip

                zip_buffer.seek(0)

                # Nome do arquivo ZIP
                nome_arquivo_zip = f"{nome_base}_dividido.zip"

                # Botão para download do arquivo ZIP
                st.download_button(
                    label="Baixar todos os arquivos divididos",
                    data=zip_buffer,
                    file_name=nome_arquivo_zip,
                    mime="application/zip"
                )

            except Exception as e:
                st.error(f"Erro ao dividir o PDF: {e}")
    else:
        st.error("Envie um arquivo PDF.")


elif opcao == "Comprimir PDF":
    st.header("Comprimir PDF")
    
    arquivo = st.file_uploader(
        "Envie o arquivo PDF que deseja comprimir", 
        type="pdf", 
        key="comprimir_pdf_uploader"
    )
    
    if arquivo is not None:
        nome_original = arquivo.name
        primeira_palavra = nome_original.split()[0]
        caminho_entrada = gerar_caminho_temp("temp_pdf.pdf")
        caminho_saida = gerar_caminho_temp(f"{primeira_palavra}_comprimido.pdf")
        
        with open(caminho_entrada, "wb") as f:
            f.write(arquivo.read())

        if st.button("Comprimir", key="comprimir_button"):
            with st.spinner("Comprimindo o PDF... Isso pode levar algum tempo."):
                try:
                    comprimir_pdf(caminho_entrada, caminho_saida)

                    st.success("PDF comprimido com sucesso!")
                    tamanho_original = os.path.getsize(caminho_entrada) / (1024 * 1024)
                    tamanho_comprimido = os.path.getsize(caminho_saida) / (1024 * 1024)
                    st.write(f"Tamanho original: {tamanho_original:.2f} MB")
                    st.write(f"Tamanho comprimido: {tamanho_comprimido:.2f} MB")

                    with open(caminho_saida, "rb") as f:
                        st.download_button(
                            "Baixar PDF Comprimido", 
                            f, 
                            file_name=caminho_saida, 
                            key="comprimir_download_button"
                        )

                    os.remove(caminho_entrada)
                    os.remove(caminho_saida)

                except Exception as e:
                    st.error(f"Erro ao processar o PDF: {e}")
    else:
        st.error("Envie um arquivo PDF para comprimir.")
