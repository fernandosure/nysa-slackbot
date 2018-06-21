import timeago
import pytz
import requests
from datetime import datetime
from dateutil import parser
from secret_manager import get_secret


def handle_ecs_bot_cmd(command_param, cluster_param, service_param, tag_param):

    result = {}
    base_url = get_secret(u'NYSA_API_BASEURL')

    if command_param == "deploy" and cluster_param is not None and service_param is not None:

        url = "{}/v1/clusters/{}/services/{}/tags".format(base_url, cluster_param, service_param)
        rs = requests.get(url)
        if rs.status_code != 200:
            result["text"] = rs.json.get('message')
            return result

        tags = rs.json().get(u'content')
        if tag_param is None:
            result["text"] = "Sure...this is a list of the tags available for deploy"
            result["attachments"] = [{"text": "{}:{} created:{}"
                                     .format(service_param, img[u'tag'],
                                             timeago.format(parser.parse(img[u'pushed_at']), datetime.now(pytz.utc)))} for img in tags[:20]]
        else:
            found = next((img for img in tags if img[u'tag'] == tag_param), None)
            if not found:
                result["text"] = "Tag not found..."
            else:
                data = {"image_tag": tag_param}
                url = "{}/v1/clusters/{}/services/{}".format(base_url, cluster_param, service_param)
                rs = requests.put(url, json=data)
                if rs.status_code == 202:
                    result["text"] = rs.json().get('message')
                    return result

    return result
