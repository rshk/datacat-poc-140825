from flask import Blueprint, url_for, redirect
from werkzeug.exceptions import NotFound

from datacat.db import get_db
from datacat.ext.plugin import BasePlugin
from datacat.web.utils import json_view


class CorePlugin(BasePlugin):
    """
    "Core" plugin handling some standard functionality.
    """

    def setup(self):
        pass

    def make_dataset_metadata(self, dataset_id, config, metadata):
        if 'metadata' in config:
            metadata.update(config['metadata'])

        if 'resources' in config:
            metadata['resources'] = []
            for resource_id, resource in enumerate(config['resources']):
                metadata['resources'].append({
                    'url': url_for(__name__ + '.get_dataset_resource',
                                   dataset_id=dataset_id,
                                   resource_id=resource_id,
                                   _external=True)
                })

    blueprint = Blueprint(__name__, __name__)


@CorePlugin.blueprint.route('/resource/<int:resource_id>')
@json_view
def get_dataset_resource(dataset_id, resource_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, configuration FROM dataset WHERE id = %(id)s",
                    dict(id=dataset_id))
        row = cur.fetchone()
        if row is None:
            raise NotFound("The dataset was not found")
        dataset_conf = row['configuration']

    try:
        resource_conf = dataset_conf['resources'][resource_id]

    except (KeyError, IndexError):
        raise NotFound("The resource was not found")

    resource_type = resource_conf.get('type')
    if resource_type == 'internal':
        url = url_for('admin.get_resource_data',
                      resource_id=resource_conf['id'],
                      _external=True)

    elif 'url' in resource_conf:
        url = resource_conf['url']

    else:
        raise NotFound("Unable to find an URL for the resource")

    return '', 302, {'Location': url}
    # return redirect(url, code=302)
