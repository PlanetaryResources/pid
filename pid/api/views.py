# -*- coding: utf-8 -*-
"""API views."""
from flask import Blueprint
from pid.extensions import restful_api
from .resources import (DocumentResource, ImageResource, LinkResource, GenericDocumentResource,
                        GenericImageResource, GenericLinkResource)

blueprint = Blueprint('api', __name__, url_prefix='/api', static_folder='../static')

# Link to flasgger:
# http://127.0.0.1:5000/apidocs/index.html

restful_api.add_resource(DocumentResource,
                         '/documents',
                         '/documents/<int:document_id>',
                         '/documents/<int:document_id>/<string:document_title>',
                         endpoint="documents")
restful_api.add_resource(ImageResource,
                         '/images',
                         '/images/<int:image_id>',
                         '/images/<int:image_id>/<string:image_title>',
                         endpoint="images")
restful_api.add_resource(LinkResource,
                         '/links',
                         '/links/<int:id>',
                         endpoint="links")

restful_api.add_resource(GenericDocumentResource,
                         '/<string:record_class>/<int:record_id>/documents',
                         '/<string:record_class>/<int:record_id>/documents/<int:document_id>',
                         endpoint="generic_documents")
restful_api.add_resource(GenericImageResource,
                         '/<string:record_class>/<int:record_id>/images',
                         '/<string:record_class>/<int:record_id>/images/<int:image_id>',
                         endpoint="generic_images")
restful_api.add_resource(GenericLinkResource,
                         '/<string:parent_class>/<int:id>/links',
                         '/<string:parent_class>/<int:id>/links/<int:link_id>',
                         endpoint="generic_links")
