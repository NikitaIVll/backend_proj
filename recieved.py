import pika
import redis
from backend.translation_files.translation_app import translate_document
import os

redis_host = 'localhost'
redis_port = 6379
redis_db = 0
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
rabbitmq_host = 'localhost'
rabbitmq_queue = 'file_processing'


def process_file(file_path, target, source):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist")
    projpath = os.path.abspath(os.path.join(file_path, "..", ".."))

    file_dir = os.path.abspath(os.path.join(projpath, 'out'))
    new_file_name = f'{os.path.splitext(os.path.basename(file_path))[0]}_translated{os.path.splitext(file_path)[1]}'
    new_file_path = os.path.join(file_dir, new_file_name)

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    # if os.path.exists(new_file_path):
    #     raise FileExistsError(f"File '{new_file_path}' already exists")

    if os.path.exists(new_file_path):
        os.remove(new_file_path)

    translate_document(os.path.basename(file_path), target, source)

    return new_file_path


def read_from_queue():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)

    def callback(ch, method, properties, body):
        request_id, file_path, target, source = body.decode().split(',')
        new_file_path = process_file(file_path, target, source)
        redis_client.set(request_id, 'completed')
        redis_client.set(f'{request_id}_path', new_file_path)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback)
    channel.start_consuming()


if __name__ == '__main__':
    read_from_queue()
