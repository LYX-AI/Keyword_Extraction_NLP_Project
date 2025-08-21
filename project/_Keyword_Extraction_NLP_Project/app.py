from flask import Flask, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
import logging
import os
import  langdetect
from keybert import KeyBERT
import jieba
import PyPDF2
from docx import Document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf','docx','txt'}
key_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')
logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s'
)
def extract_text_from_pdf(pdf_path):
    with open(pdf_path,"rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = [page.extract_text()for page in reader.pages]
    return ' '.join(text)

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return ' '.join([para.text for para in doc.paragraphs])

def extract_text_from_txt(txt_path):
    with open(txt_path,'r') as file:
        return file.read()

def process_text(text):
    try :
        lang = langdetect.detect(text)
        if lang == 'en':
            keywords = key_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1,2),
                stop_words='english',
                highlight=False
            )
        elif lang.startswith('zh'):
            words = " ".join(jieba.cut(text))
            keywords = key_model.extract_keywords(
                words,
                keyphrase_ngram_range=(1,2),
                stop_words=None,
                highlight=False
            )
        else:# other language
            keywords = key_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1,2),
                stop_words=None,
                highlight=False
            )
        keyword_phrases = [kw[0] for kw in keywords]

        return " ".join(keyword_phrases)
    except Exception as e:
        return f"Error processing text:{str(e)}"



def allowed_file(filename:str):
    return '.' in filename and filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods = ['GET','POST'])
def upload_file():
    if request.method == "POST":
        file = request.files.get('file')
        text = request.form.get('text')

        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                logging.info(f'File save to {file_path}')
                processed_text = f'File saved to {file_path}'
            else:
                flash('File type is not allowed')
                return redirect(request.url)
        elif text:
                processed_text = process_text()
                logging.info('Text data processed.')
                return redirect(request.url)
        return  processed_text
if __name__ == "__main__":
    app.run(debug=True)