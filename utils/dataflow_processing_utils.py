import datetime
from orjson import orjson

def extract_job_id(document):
    doc = orjson.loads(document)
    return doc.get('metadata', {}).get('job_id', 'default_job_id')

def prepare_payload(keyed_item) -> any:
    """
    Transform the keyed data item into the required JSON structure for the FastAPI endpoint.

    :param keyed_item: Tuple containing the key (job_id) and the item dictionary.
    :return: Dictionary formatted for the FastAPI endpoint.
    """

    rtn = []
    for item in keyed_item:
        item["created_at"] = datetime.datetime.now().isoformat()
        item["updated_at"] = datetime.datetime.now().isoformat()
        rtn.append(item)

    return rtn