import requests
import json
from numu import app
import boto3

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
    with requests.get(url, stream=True) as r:
        client.upload_fileobj(
            r.raw,
            'numu',
            name
        )
        client.put_object_acl(ACL='public-read', Bucket='numu', Key=name)
