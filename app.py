import os
import pysrt
import chardet
import re
import textwrap
import tempfile
from flask import Flask, render_template, request, send_file, redirect, flash, url_for
from deep_translator import GoogleTranslator
from langdetect import detect

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

LINE_WIDTH = 42

LANG_NAME = {
    "en": "Inglês", "es": "Espanhol", "pt": "Português", "cs": "Tcheco",
    "fr": "Francês", "de": "Alemão", "it": "Italiano", "nl": "Holandês",
    "ru": "Russo", "ja": "Japonês", "ar": "Árabe", "tr": "Turco",
    "pl": "Polonês", "sv": "Sueco", "fi": "Finlandês", "da": "Dinamarquês",
    "no": "Norueguês", "he": "Hebraico", "hi": "Hindi", "th": "Tailandês",
    "vi": "Vietnamita", "id": "Indonésio", "ms": "Malaio", "hu": "Húngaro",
    "ro": "Romeno", "bg": "Búlgaro", "uk": "Ucraniano", "hr": "Croata",
    "sr": "Sérvio", "sk": "Eslovaco", "sl": "Esloveno", "lt": "Lituano",
    "mt": "Maltês", "sq": "Albanês", "is": "Islandês", "ga": "Irlandês",
}

CURRENT_PROGRESS = 0

def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        return chardet.detect(f.read())["encoding"]

def convert_to_utf8_if_needed(input_path):
    encoding = detect_encoding(input_path)
    if encoding and encoding.lower() != "utf-8":
        with open(input_path, "r", encoding=encoding) as f:
            content = f.read()
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(content)

def clean_text(text):
    text = re.sub(r"<.*?>", "", text)
    emoji_pattern = re.compile("[" 
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text.replace("\ufeff", "").replace("\u200b", "").strip()

def format_line(line, width=LINE_WIDTH):
    return "\n".join(textwrap.wrap(line, width=width))

def detect_language(input_path):
    convert_to_utf8_if_needed(input_path)
    subs = pysrt.open(input_path, encoding="utf-8")
    return detect(" ".join([sub.text for sub in subs[:10]]))

def translate_srt(input_path, target_lang="pt", progress_callback=None):
    convert_to_utf8_if_needed(input_path)
    subs = pysrt.open(input_path, encoding="utf-8")
    total = len(subs)
    lang_code = detect_language(input_path)
    lang_name = LANG_NAME.get(lang_code, lang_code.upper())
    batch_size = 300
    translator = GoogleTranslator(source=lang_code, target=target_lang)

    for i in range(0, total, batch_size):
        batch = subs[i:i + batch_size]
        texts = [clean_text(sub.text.replace("\n", " ")) for sub in batch]
        try:
            translated = translator.translate_batch(texts)
        except Exception as e:
            print("Erro na tradução:", e)
            translated = texts
        for j, sub in enumerate(batch):
            sub.text = format_line(translated[j]) if j < len(translated) else format_line(sub.text)
        if progress_callback:
            progress_callback(min(i + batch_size, total), total)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as out_tmp:
        subs.save(out_tmp.name, encoding="utf-8")
        output_path = out_tmp.name
    return output_path, lang_name, total

@app.route("/")
def root():
    return redirect(url_for("welcome"))

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

@app.route("/tradutor", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "srt_file" not in request.files:
            flash("Nenhum arquivo enviado")
            return redirect(request.url)
        file = request.files["srt_file"]
        target_lang = request.form.get("target_lang", "pt")
        if file.filename == "":
            flash("Nenhum arquivo selecionado")
            return redirect(request.url)
        global CURRENT_PROGRESS
        CURRENT_PROGRESS = 0
        def progress_cb(done, total):
            global CURRENT_PROGRESS
            CURRENT_PROGRESS = int(done / total * 100)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp:
            file.save(tmp.name)
            output_path, lang, total = translate_srt(tmp.name, target_lang, progress_cb)
            CURRENT_PROGRESS = 100
            flash(f"Arquivo traduzido com sucesso: {total} linhas ({lang} → {target_lang.upper()})")
            return send_file(output_path, as_attachment=True, download_name=file.filename)
    return render_template("index.html", languages=LANG_NAME)

@app.route("/progress")
def progress():
    return {"progress": CURRENT_PROGRESS}

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(app.root_path, 'static', 'icon.ico'))

if __name__ == "__main__":
    app.run(debug=True)
