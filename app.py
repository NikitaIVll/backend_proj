from flask import Flask, request, jsonify, send_from_directory, send_file
import base64
from backend import app_logger
from werkzeug.serving import run_simple
import pika
import os
import uuid
import redis
# from backend.model import translator
from flask_socketio import SocketIO, emit
import ssl

translation = []

app = Flask(__name__, static_url_path='/static', static_folder='frontend/build')
app.config["DEBUG"] = True  # turn off in prod
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# RabbitMQ
rabbitmq_host = 'localhost'
rabbitmq_queue = 'file_processing'

# Redis
redis_host = 'localhost'
redis_port = 6379
redis_db = 0

redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

logger = app_logger.get_logger("web-server")


def send_to_queue(file_path, source, target, request_id):
    try:
        with pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=rabbitmq_queue)
            channel.basic_publish(
                exchange='',
                routing_key=rabbitmq_queue,
                body=f'{request_id},{file_path},{target}, {source}',
                properties=pika.BasicProperties(delivery_mode=2))
        emit('status', {'status': 'task_queued', 'request_id': request_id})
    except Exception as e:
        logger.error("Ошибка при отправке задачи в очередь: %s", e)
        raise


@app.route('/', methods=["GET"])
def health_check():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/translate', methods=["POST"])
def get_prediction():
    source = request.json['source']
    target = request.json['target']
    text = request.json['text']
    logger.info("manual translation from %s to %s", source, target)
    logger.info("input text length is %d", len(text))
    # translation = translator.translate_text(source, target, text)
    res = jsonify({"translated": translation})
    logger.info("manual translation complete. text length is %d", len(translation))
    return res


@app.route('/api/translate_text', methods=["POST"])
def api_translate_text():
    source = request.json['source']
    target = request.json['target']
    text = request.json['text']
    decoded_text = base64.b64decode(text).decode('utf-8')
    logger.info("API translation from %s to %s", source, target)
    logger.info("input text length is %d", len(decoded_text))
    # translation = translator.translate_text(source, target, decoded_text)
    text_bytes = translation.encode('utf-8')
    base64_encoded_string = base64.b64encode(text_bytes).decode('utf-8')
    res = jsonify({"translated": base64_encoded_string})
    logger.info("API translation complete. text length is %d", len(translation))
    return res


@app.route('/translate_file', methods=['POST'])
def process():
    source = request.form.get('source')
    target = request.form.get('target')
    file = request.files['file']
    request_id = str(uuid.uuid4())
    input_path = os.path.abspath(os.path.join(__file__, "..", "in"))
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    file_path = os.path.join(input_path, file.filename)
    try:
        file.save(file_path)
    except Exception as e:
        logger.error("Ошибка при сохранении файла: %s", e)
        return jsonify({'error': f'Ошибка при сохранении файла: {e}'}), 500
    if not os.path.exists(file_path):
        return jsonify({'error': 'Файл не был сохранен'}), 500
    try:
        send_to_queue(file_path, source, target, request_id)
    except Exception as e:
        logger.error("Ошибка при отправке задачи в очередь: %s", e)
        return jsonify({'error': 'Ошибка при отправке задачи в очередь'}), 500
    redis_client.set(request_id, 'processing')
    return jsonify({'request_id': request_id})


@app.route('/check_status/<request_id>', methods=['GET'])
def check_status(request_id):
    try:
        status = redis_client.get(request_id)
        if status:
            if status.decode() == 'completed':
                file_path = redis_client.get(f'{request_id}_path').decode()
                if not file_path or not os.path.exists(file_path):
                    return jsonify({'error': 'Файл не найден или не готов к загрузке'}), 404
                return jsonify({'status': 'completed', 'file_path': file_path})
            else:
                return jsonify({'status': 'processing'})
        else:
            return jsonify({'error': 'Request ID not found'}), 404
    except Exception as e:
        logger.error("Ошибка при проверке статуса: %s", e)
        return jsonify({'error': 'Ошибка при проверке статуса'}), 500


@app.route('/download/<request_id>', methods=['GET'])
def download_file(request_id):
    try:
        file_path = redis_client.get(f'{request_id}_path').decode()
        if file_path:
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found or not ready for download'}), 404
    except Exception as e:
        logger.error("Ошибка при скачивании файла: %s", e)
        return jsonify({'error': 'Ошибка при скачивании файла'}), 500

@socketio.on('connect')
def handle_connect():
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('server.crt', 'server.key')
    # serve(app, host='0.0.0.0', port=7060, url_scheme='https')
    # run_simple(hostname='0.0.0.0', port=7070, application=app, ssl_context='adhoc')
    # socketio.run(app, host='0.0.0.0', port=7070, ssl_context=context)
    socketio.run(app, host='0.0.0.0', port=7070)
    # run_simple(hostname='0.0.0.0', port=7060, application=app)
