import requests
import json
from numu import app
import boto3
from PIL import Image
from io import BytesIO

session = boto3.session.Session()
client = session.client(
    's3',
    region_name='sfo2',
    endpoint_url='https://sfo2.digitaloceanspaces.com',
    aws_access_key_id=app.config.get('DO_ACCESS_KEY'),
    aws_secret_access_key=app.config.get('DO_SECRET_KEY')
)


def grab_json(uri):
    try:
        response = requests.get(uri)
    except requests.ConnectionError:
        return None
    return json.loads(response.text)


def put_image_from_url(url, name):

    response = requests.get(url, stream=True)
    if response.status_code != 200:
        app.logger.error("Image at {} response code {}".format(url, response.status_code))
        raise IOError("Unable to retrieve image file.")

    try:
        image = Image.open(response.raw)
    except TypeError as err:
        app.logger.error(
            "Import of {} unsuccessful. Error message:".format(url, err))
        raise IOError("Unable to process image file.")

    app.logger.info("File size: {}".format(image.size))

    with BytesIO() as output:
        try:
            image.save(output, 'png')
        except IOError:
            app.logger.error("Save of {} failed, Error message:".format(url, err))

        output.seek(0)
        client.upload_fileobj(
            output,
            'numu',
            name
        )
        client.put_object_acl(ACL='public-read', Bucket='numu', Key=name)
