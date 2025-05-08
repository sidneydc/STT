from flask import Flask, request, jsonify, Response
import speech_recognition as sr
from io import BytesIO
import tempfile
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Criar a aplicação Flask
app = Flask(__name__)

# Função para transcrever áudio usando SpeechRecognition
def transcribe_audio(audio_file):
    """Transcrever áudio para texto usando a API de reconhecimento de fala do Google"""
    recognizer = sr.Recognizer()
    
    # Ajustar parâmetros de reconhecimento
    recognizer.energy_threshold = 300  # Aumentar a sensibilidade
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # Pausa maior indica fim da frase
    
    audio = sr.AudioFile(audio_file)
    with audio as source:
        logger.debug("Gravando áudio do arquivo")
        audio_data = recognizer.record(source)
        
    logger.debug(f"Duração do áudio: {len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)} segundos")
    
    # Tentar primeiro com o português (Brasil)
    try:
        logger.debug("Tentando reconhecimento de fala com pt-BR")
        text = recognizer.recognize_google(audio_data, language="pt-BR")
        logger.debug(f"Áudio transcrito com sucesso (pt-BR): {text}")
        return text
    except sr.UnknownValueError:
        logger.debug("Falha com pt-BR, tentando com o inglês (en-US)")
        # Se o português falhar, tentar o inglês
        try:
            text = recognizer.recognize_google(audio_data, language="en-US")
            logger.debug(f"Áudio transcrito com sucesso (en-US): {text}")
            return text
        except sr.UnknownValueError:
            logger.error("Não foi possível entender o áudio em nenhum idioma")
            return "Não foi possível transcrever o áudio"
        except sr.RequestError as e:
            logger.error(f"Erro ao acessar o serviço de reconhecimento de fala (en-US): {e}")
            return f"Erro ao tentar acessar o serviço de reconhecimento de fala: {e}"
    except sr.RequestError as e:
        logger.error(f"Erro ao acessar o serviço de reconhecimento de fala (pt-BR): {e}")
        return f"Erro ao tentar acessar o serviço de reconhecimento de fala: {e}"

# Rota para transcrição de áudio
@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Ponto de API para transcrever áudio em texto"""
    if 'file' not in request.files:
        logger.error("Nenhum arquivo encontrado na solicitação")
        return jsonify({"error": "Arquivo não encontrado"}), 400

    file = request.files['file']
    
    if file.filename == '':
        logger.error("Nenhum arquivo selecionado")
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    audio_format = file.filename.split('.')[-1].lower()
    logger.debug(f"Arquivo de áudio recebido: {file.filename}, formato: {audio_format}")
    
    # Verificar se o formato é suportado
    if audio_format in ['ogg', 'oga', 'opus', 'm4a', 'wav', 'mp3']:
        try:
            # Salvar o arquivo temporariamente para garantir que ele seja totalmente legível
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp_orig:
                file.save(tmp_orig.name)
                logger.debug(f"Arquivo salvo temporariamente em {tmp_orig.name}, tamanho: {os.path.getsize(tmp_orig.name)} bytes")
            
            # Transcrever o áudio
            with open(tmp_orig.name, 'rb') as audio_file:
                text = transcribe_audio(audio_file)
            
            # Remover o arquivo temporário
            if os.path.exists(tmp_orig.name):
                os.remove(tmp_orig.name)
                
            return jsonify({"transcription": text})
        except Exception as e:
            logger.error(f"Erro ao processar o áudio: {e}")
            return jsonify({"error": f"Erro ao processar o áudio: {str(e)}"}), 500
    else:
        logger.error(f"Formato de áudio não suportado: {audio_format}")
        return jsonify({"error": "Formato de áudio não suportado. Use ogg, oga, opus, m4a, wav ou mp3"}), 400

if __name__ == '__main__':
    # Rodar a aplicação Flask na porta 8002
    app.run(host='0.0.0.0', port=8002, debug=True)
