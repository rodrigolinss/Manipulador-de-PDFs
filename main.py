
import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import os

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


def dividir_pdf(arquivo):
    leitor = PdfReader(arquivo)
    arquivos_saida = []
    for i, pagina in enumerate(leitor.pages):
        escritor = PdfWriter()
        escritor.add_page(pagina)
        nome_arquivo = f"pagina_{i + 1}.pdf"
        with open(nome_arquivo, "wb") as f:
            escritor.write(f)
        arquivos_saida.append(nome_arquivo)
    return arquivos_saida

# Função para comprimir PDF com compressão real
def comprimir_pdf(arquivo, qualidade=50):
    documento = fitz.open(arquivo)
    caminho_saida = "pdf_comprimido.pdf"

    for pagina in documento:  # Itera pelas páginas
        imagens = pagina.get_images(full=True)  # Obtém todas as imagens
        for img_index, img in enumerate(imagens):
            xref = img[0]  # Referência da imagem no PDF
            base_image = documento.extract_image(xref)  # Extrai a imagem
            imagem_bytes = base_image["image"]

            # Converte para uma imagem mais compacta
            imagem = Image.open(BytesIO(imagem_bytes))
            buffer = BytesIO()
            imagem.save(buffer, format="JPEG", quality=qualidade)  # Ajusta a qualidade
            buffer.seek(0)

            # Substitui a imagem original pela comprimida
            documento.update_image(xref, buffer.read())

    # Salva o PDF comprimido
    documento.save(caminho_saida, deflate=True)  # `deflate=True` ajuda a reduzir mais
    documento.close()
    return caminho_saida



 

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
    if st.button("Dividir"):
        if arquivo:
            arquivos_saida = dividir_pdf(arquivo)
            st.success("PDF dividido com sucesso!")
            for nome_arquivo in arquivos_saida:
                with open(nome_arquivo, "rb") as f:
                    st.download_button(f"Baixar {nome_arquivo}", f, file_name=nome_arquivo)
                os.remove(nome_arquivo)
        else:
            st.error("Envie um arquivo PDF.")

elif opcao == "Comprimir PDF":
    st.header("Comprimir PDF")
    st.sidebar.write("Reduza o tamanho do seu PDF ajustando a qualidade das imagens.")
    qualidade = st.sidebar.slider("Qualidade da imagem (1-100)", min_value=1, max_value=100, value=50)

    arquivo = st.file_uploader("Envie o arquivo PDF que deseja comprimir", type="pdf")
    if st.button("Comprimir"):
        if arquivo:
            caminho_saida = comprimir_pdf(arquivo, qualidade)
            st.success("PDF comprimido com sucesso!")
            with open(caminho_saida, "rb") as f:
                st.download_button("Baixar PDF Comprimido", f, file_name="pdf_comprimido.pdf")
            os.remove(caminho_saida)
        else:
            st.error("Envie um arquivo PDF para comprimir.")
