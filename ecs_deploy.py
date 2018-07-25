import timeago
import pytz
import requests
from datetime import datetime
from dateutil import parser
from secret_manager import get_secret


def handle_ecs_bot_cmd(command_param, cluster_param, service_list_param):

    result = {}
    base_url = get_secret(u'NYSA_API_BASEURL')

    if command_param == "deploy" and cluster_param is not None and service_list_param is not None:

        if len(service_list_param) == 1 and service_list_param[0]["service"].lower() != "all":
            url = "{}/v1/clusters/{}/services/{}/tags".format(base_url, cluster_param, service_list_param[0]["service"])
            rs = requests.get(url)
            if rs.status_code != 200:
                result["text"] = rs.json.get('message')
                return result

            tags = rs.json().get(u'content')
            if service_list_param[0]["tag"] is None:
                result["text"] = "Sure...this is a list of the tags available for deploy"
                result["attachments"] = [{"text": "{}:{} created:{}"
                                         .format(service_list_param[0]["service"], img[u'tag'],
                                                 timeago.format(parser.parse(img[u'pushed_at']), datetime.now(pytz.utc)))} for img in tags[:10] if img.get(u'tag') is not None]
            else:
                found = next((img for img in tags if img[u'tag'] == service_list_param[0]["tag"]), None)
                if not found:
                    result["text"] = "Tag not found..."
                else:
                    data = {"image_tag": service_list_param[0]["tag"]}
                    url = "{}/v1/clusters/{}/services/{}".format(base_url,
                                                                 cluster_param,
                                                                 service_list_param[0]["service"]
                                                                 )
                    rs = requests.put(url, json=data)
                    if rs.status_code == 202:
                        result["text"] = rs.json().get('message')
                        return result
        else:
            url = "{}/v1/clusters/{}/config".format(base_url, cluster_param)
            rs = requests.get(url)
            if rs.status_code == 200:
                cluster_config = rs.json()

                if service_list_param[0]["service"] != "all":
                    for service in service_list_param:
                        svc = next((x for x in cluster_config.get('services') if x.keys()[0] == service["service"]), None)
                        if svc is not None:
                            svc = svc[svc.keys()[0]]
                            if service["tag"]:
                                svc[u'image'] = "{}:{}".format(svc[u'image'].rsplit(u':', 1)[0], service["tag"])

                if service_list_param[0]["service"] == "all":
                    for svc in cluster_config.get('services'):
                        svc = svc[svc.keys()[0]]
                        if service_list_param[0]["tag"]:
                            svc[u'image'] = "{}:{}".format(svc[u'image'].rsplit(u':', 1)[0], service_list_param[0]["tag"])

                url = "{}/v1/clusters/{}/config".format(base_url, cluster_param)
                rs = requests.put(url, json=cluster_config)
                if rs.status_code == 202:
                    result["text"] = rs.json().get('message')
                    return result

    return result
