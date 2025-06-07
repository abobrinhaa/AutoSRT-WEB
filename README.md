# AutoSRT-WEB

Aplicação web simples para tradução de arquivos `.srt` utilizando Flask e Google Translate.

## Instalação

```bash
pip install -r requirements.txt
```

Configure a variável de ambiente `SECRET_KEY` para definir a chave da sessão:

```bash
export SECRET_KEY="minha-chave-super-secreta"
```

## Uso

Execute a aplicação localmente:

```bash
python app.py
```

Acesse `http://localhost:5000/welcome` no navegador e siga as instruções.

É possível escolher o idioma de destino no formulário principal. O progresso da tradução é exibido em tempo real.
