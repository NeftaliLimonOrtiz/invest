from flask import Flask, render_template, url_for, request, redirect, send_file, session, Response
import openai
import os
from dotenv import load_dotenv
load_dotenv()
importanceArray = [False, False, False, False]
import logging
import sys
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from flask import make_response

# Create a custom handler that directs the log output to stderr
handler = logging.StreamHandler(stream=sys.stderr)

# Create a formatter for the log messages (optional)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the root logger
logging.getLogger().addHandler(handler)

filename = ""

logging.warning('Assigning credentials')

flag = os.environ.get('RANDOM_FLAG')

logging.warning('Initiating bucket connection')

app = Flask(__name__)


secret_key = secrets.token_hex(16)
app.config['SECRET_KEY'] = secret_key

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/', methods=['GET', 'POST'])

def index():
    global imagePath
    global bucket
    global filename
    
    if request.method == 'POST' and request.form.get('form_name') == 'keywordsForm':
        keywords = []
        keywords.append(request.form["keyword1"])
        keywords.append(request.form["keyword2"])
        keywords.append(request.form["keyword3"])
        keywords.append(request.form["keyword4"])

        
        description = request.form["Description"]
        source_page = request.form["source_page"]
        nivel_deseo_str = request.form.get('nivelDeseo')        

        print(description)
    
        if source_page == "INVEST.html":
            language = request.form.get("language", "Spanish")
            if language == "english":
                system_message = "You are an expert in finance and you help people guide them to invest. Your answers are intended for people who use banorte and are medium-long in size"
                generate_prompt_func = generate_prompt_eng
            else:
                system_message = "eres un experto en finanzas y ayudas a las personas a orientarlas para invertir. Tus respuestas estan pensandas para personas que usan banorte y son de tamaño mediano-largo"
                generate_prompt_func = generate_prompt

        if language == "english":
            if nivel_deseo_str == "0":
                nivel_deseo = "1 año"
            elif nivel_deseo_str == "1":
                nivel_deseo = "más de 1 año"
            elif nivel_deseo_str == "2":
                nivel_deseo = "más de 2 años"        
            else:
                nivel_deseo = "Desconocido"
        else:
            if nivel_deseo_str == "0":
                nivel_deseo = "1 year"
            elif nivel_deseo_str == "1":
                nivel_deseo = "more than a year"
            elif nivel_deseo_str == "2":
                nivel_deseo = "more than 2 years"        
            else:
                nivel_deseo = "unknown"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
               {"role": "system", "content": system_message},
                {"role": "user", "content": generate_prompt_eng(keywords, description, importanceArray, nivel_deseo) if language == "english" else generate_prompt_func(keywords, description, importanceArray, nivel_deseo) }
                ],
            temperature = 0.6,
            max_tokens = 3000
        )
        result = response.choices[0].message.content

        result = result.replace("Hashtags sugeridos:", "")
        result = result.replace("Anuncio:", "")
        result = result.replace("\n", "<br>")
        
        print(result)

        return redirect(url_for("index", result=result, _anchor="instaPost", source_page=source_page, language=language))

    destination_blob_name = request.args.get("fileName")
    result = request.args.get("result")
    language = request.args.get("language", "Spanish")
    error = request.args.get("error")

    return render_template('INVEST.html', result=result, language=language)
        
@app.route('/importance_endpoint', methods=['POST'])
def importance_endpoint():

    try:
        data = request.get_json()
        importance = data['importance']
        id = data['id']
        if id == 'c1' and importance == True:
            importanceArray[0] = True
        elif id == 'c1' and importance == False:
            importanceArray[0] = False
        elif id == 'c2' and importance == True:
            importanceArray[1] = True
        elif id == 'c2' and importance == False:
            importanceArray[1] = False
        elif id == 'c3' and importance == True:
            importanceArray[2] = True
        elif id == 'c3' and importance == False:
            importanceArray[2] = False
        elif id == 'c4' and importance == True:
            importanceArray[3] = True
        elif id == 'c4' and importance == False:
            importanceArray[3] = False
        return {'success': True}
    except Exception as e:
        print(e)
        return {'success': False}
    
@app.route('/landing')
def landingPage():
    language = 'Spanish'  
    return render_template('landingPage.html', language=language)
   
@app.route('/landing_eng')
def landingPage_eng():
    language = 'english'  
    return render_template('landingPage.html', language=language)

@app.route('/invest')
def Invest():
    language = 'Spanish'  
    return render_template('INVEST.html', language=language)

@app.route('/invest_eng')
def Invest_eng():
    language = 'english'  
    return render_template('INVEST.html', language=language)

def generate_prompt(keywords, description, importanceArray, nivel_deseo):
    prompt = f"""Necesito una recomendación de inversión para mi cartera. Estoy buscando opciones que maximicen mis ganancias a 
    {nivel_deseo} de plazo y minimicen los riesgos. 
    Breve descripcion de lo que quiero hacer:{description}
    Algunos de mis objetivos son:{keywords}.Actualmente, tengo 
    inversiones en acciones, bonos y fondos indexados. Estoy dispuesto a considerar diferentes clases de activos, como bienes raíces, 
    materias primas o criptomonedas, si crees que son adecuadas.Por favor, proporciona una recomendación detallada que incluya la cantidad 
    de dinero que debería invertir en cada activo, el horizonte de inversión recomendado y cualquier estrategia específica que deba seguir.
    También me gustaría conocer tu opinión sobre el panorama económico actual y cómo podría afectar mis inversiones. Por favor, proporciona
    información basada en datos y análisis fundamentales.Recuerda que estoy buscando asesoramiento financiero profesional y aprecio tu experiencia 
    en este campo. No necesito frases de introducción adicionales en tu respuesta, simplemente comienza con tu recomendación de inversión"."""



    print(f"Prompt: {prompt}")


    
    return prompt

def generate_prompt_eng(keywords, description, importanceArray, nivel_deseo):
    
    prompt = f"""I need an investment recommendation for my portfolio. I am looking for options that maximize my profits at
    {nivel_deseo} term and minimize risks.
    Brief description of what I want to do:{description}
    Some of my goals are:{keywords}.Currently, I have
    investments in stocks, bonds and index funds. I am willing to consider different asset classes, such as real estate,
    commodities or cryptocurrencies, if you think they are suitable. Please provide a detailed recommendation including the amount
    of money you should invest in each asset, the recommended investment horizon and any specific strategies you should follow.
    I would also like to hear your opinion on the current economic landscape and how it could affect my investments. Please provide
    information based on fundamental data and analysis. Please remember that I am seeking professional financial advice and appreciate your expertise
    in this field. I don't need additional introductory sentences in your answer, just start with your investment recommendation."""
    
    print(f"Prompt: {prompt}")

    return prompt

if __name__ == "__main__":
    app.run(debug=True)

##<a href="{{ url_for('download_csv') }}" class="btn btn-primary">Descargar CSV</a>
