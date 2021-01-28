#!/usr/bin/env python3

import kubernetes



formatter = logging.Formatter(
    "%(asctime)s  [%(name)s:%(lineno)d] (%(levelname)s): %(message)s"
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger("k3s-nodid-update-service")
logger.setLevel(logging.INFO)
logger.addHandler(handler)




def updateConfigMap(node_id):

    #KUBECONFIG=/etc/rancher/k3s/k3s.yaml


    kubernetes.config.load_kube_config(config_file="/etc/rancher/k3s/k3s.yaml")

    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))



    metadata = kubernetes.client.V1ObjectMeta(
        name="waggle-config"
    )

    configmap = kubernetes.client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        data=dict(WAGGLE_NODE_ID = node_id),
        metadata=metadata
    )

    v1 = kubernetes.client.CoreV1Api()    
    
    try:
        cm = v1.read_namespaced_config_map("waggle-config", "default")
    except kubernetes.client.exceptions.ApiException:
        cm = None
        

    #print(cm)
    if cm: 
        if cm.data["WAGGLE_NODE_ID"] == node_id :
            logger.info("ConfigMap is already up-to-date")
            return

        api_response = v1.replace_namespaced_config_map(
            name="waggle-config",
            namespace="default",
            body=configmap,
            pretty = 'pretty_example',
        )
        logger.info("Reloaded ConfigMap with new value")
        return

   
    api_response = v1.create_namespaced_config_map(
            namespace="default",
            body=configmap,
            pretty = 'pretty_example',
        )
    logger.info("Loaded ConfigMap")
    return


def main():

    updateConfigMap(node_id)