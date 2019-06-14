# -*- coding: utf-8 -*-
"""API views."""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import jsonify, request, current_app, abort, send_from_directory, render_template, url_for
from datetime import datetime
from flask_restful import Resource, reqparse
from flask_login import current_user, login_required
from .models import Document, Image, Link
from pid.database import db, get_record_by_id_and_class
from pathlib import Path


def allowed_document(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() not in \
        current_app.config['ALLOWED_IMAGE_EXTENSIONS']


def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in \
        current_app.config['ALLOWED_IMAGE_EXTENSIONS']


def get_basepath(record_id, record_class, file_type):
    # Files go in for instance <PLAID>/uploads/designs/12/documents
    basepath = os.path.join(current_app.config['UPLOAD_FOLDER'], record_class, str(record_id), file_type)
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    return basepath


def formatUrl(url):
    # The following check is good for omission of http or https
    if not url.startswith('http'):
        return '{prefix}{url}'.format(prefix='http://', url=url)
    else:
        return url


class DocumentResource(Resource):

    @login_required
    def get(self, document_id, document_title):
        document = Document.get_by_id(document_id)
        if not document:
            abort(404, message='Document {} does not exist'.format(id))
        return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], filename=document.path,
                                   as_attachment=True, attachment_filename=document_title)


class ImageResource(Resource):

    @login_required
    def get(self, image_id, image_title):
        image = Image.get_by_id(image_id)
        if not image:
            abort(404, message='Image {} does not exist'.format(id))
        return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], filename=image.path,
                                   as_attachment=True, attachment_filename=image_title)


class LinkResource(Resource):

    @login_required
    def get(self, id):
        link = Link.get_by_id(id)
        if not link:
            abort(404, message='Link {} does not exist'.format(id))
        return link, 200


class GenericDocumentResource(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('description', type=str, default='', location='form')
        super(GenericDocumentResource, self).__init__()

    @login_required
    def post(self, record_id, record_class, document_id=None):
        if record_id and document_id:
            return self.put(record_id, document_id)

        file = request.files['file']
        if file and allowed_document(file.filename):
            title = secure_filename(file.filename)
            extension = ''.join(Path(file.filename).suffixes)  # Should get extensions like .tar.gz as well
            basepath = get_basepath(record_id, record_class, 'documents')

            # Save file with temp UUID to begin with
            tmp_filename = uuid.uuid4().hex + '-' + title
            tmp_filepath = os.path.join(basepath, tmp_filename)
            file.save(tmp_filepath)
            document = Document.create(path=tmp_filepath, title=title)

            # Update filepath and DB entry based on PK
            filename = '{0}{1}'.format(document.id, extension)
            filepath = os.path.join(basepath, filename)
            os.rename(tmp_filepath, filepath)
            document.path = os.path.relpath(basepath, current_app.config['UPLOAD_FOLDER']) + '/' + filename
            document.save()

            record = get_record_by_id_and_class(record_id, record_class)
            record.documents.append(document)
            log_entry = 'Document added: <strong>{0}</strong>'.format(document.title or '')
            record.add_change_log_entry(action='Add', field='Document', new_value=log_entry)
            record.save()

            variables = {
                'document': document,
                'parent_object': record,
                'api_url': url_for('api.generic_documents', record_id=record_id, record_class=record_class)
            }
            return render_template('shared/document_row.html', **variables)

        return "<strong>{0}</strong> is not a document file.".format(file.filename), 500

    @login_required
    def put(self, record_id, record_class, document_id):
        document = Document.get_by_id(document_id)
        if not document:
            abort(404, message='Document {} does not exist'.format(document_id))
        data = self.reqparse.parse_args()
        description = data.description
        old_desc = '{0}<br><i>{1}</i>'.format(document.description or '', document.title)
        new_desc = '{0}<br><i>{1}</i>'.format(description or '', document.title)
        document.update(description=description)
        record = get_record_by_id_and_class(record_id, record_class)
        field = 'Description<br>Document'
        record.add_change_log_entry(action='Edit', field=field, original_value=old_desc, new_value=new_desc)
        variables = {
            'document': document,
            'parent_object': record,
            'api_url': url_for('api.generic_documents', record_id=record_id, record_class=record_class)
        }
        return render_template('shared/document_row.html', **variables)

    @login_required
    def delete(self, record_id, document_id, record_class):
        parent = get_record_by_id_and_class(record_id, record_class)
        document = Document.get_by_id(document_id)
        document_path = Path(os.path.join(current_app.config['UPLOAD_FOLDER'], document.path))
        if not document:
            abort(404, message='Document {} does not exist'.format(record_id))
        if document_path.is_file():
            document_path.unlink()
        # Delete 'documents' directory if empty
        document_path = document_path.parent
        if not os.listdir(str(document_path)):
            document_path.rmdir()
        # Delete PK directory if empty
        document_path = document_path.parent
        if not os.listdir(str(document_path)):
            document_path.rmdir()
        parent.documents.remove(document)
        log_entry = 'Document deleted: <strong>{0}</strong>'.format(document.title or '')
        parent.add_change_log_entry(action='Remove', field='Document', original_value=log_entry)
        document.delete()
        db.session.add(parent)
        db.session.commit()
        return jsonify({'message': 'Successfully deleted Document {}'.format(id)})


class GenericImageResource(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(GenericImageResource, self).__init__()

    @login_required
    def post(self, record_id, record_class, image_id=None):
        if record_id and image_id is not None:
            return self.put(record_id, record_class, image_id)

        file = request.files['file']
        if file and allowed_image(file.filename):

            title = secure_filename(file.filename)
            extension = ''.join(Path(file.filename).suffixes)
            basepath = get_basepath(record_id, record_class, 'images')

            # Save file with temp UUID to begin with
            tmp_filename = uuid.uuid4().hex + '-' + title
            tmp_filepath = os.path.join(basepath, tmp_filename)
            file.save(tmp_filepath)
            image = Image.create(path=tmp_filepath, title=title)

            # Update filepath and DB entry based on PK
            filename = '{0}{1}'.format(image.id, extension)
            filepath = os.path.join(basepath, filename)
            os.rename(tmp_filepath, filepath)
            image.path = os.path.relpath(basepath, current_app.config['UPLOAD_FOLDER']) + '/' + filename
            image.save()

            record = get_record_by_id_and_class(record_id, record_class)
            record.images.append(image)
            log_entry = 'Image added: <strong>{0}</strong>'.format(image.title or '')
            record.add_change_log_entry(action='Add', field='Image', new_value=log_entry)
            record.save()

            variables = {
                'image': image,
                'api_url': url_for('api.generic_images', record_id=record_id, record_class=record_class)
            }
            return render_template('shared/image_gallery_item.html', **variables)

        return '<strong>{0}</strong> is not an image file.'.format(file.filename), 500

    @login_required
    def put(self, record_id, record_class, image_id):
        image = Image.get_by_id(image_id)
        if not image:
            abort(404, message='Image {} does not exist'.format(image_id))
        field = request.form['name'].split('-')[0]
        value = request.form['value']
        old_value = ''
        new_value = ''
        if field == 'title':
            old_value = image.title
            image.update(title=value)
            new_value = value
        if field == 'description':
            old_value = '{0}<br><i>{1}</i>'.format(image.description or '', image.title)
            image.update(description=value)
            new_value = '{0}<br><i>{1}</i>'.format(value or '', image.title)
        record = get_record_by_id_and_class(record_id, record_class)
        field_edit = '{0}<br>Image'.format(field.capitalize())
        record.add_change_log_entry(action='Edit', field=field_edit, original_value=old_value, new_value=new_value)
        record.save()
        variables = {
            'image': image,
            'api_url': url_for('api.generic_images', record_id=record_id, record_class=record_class)
        }
        return render_template('shared/image_gallery_item.html', **variables)

    @login_required
    def delete(self, record_id, image_id, record_class):
        record = get_record_by_id_and_class(record_id, record_class)
        image = Image.get_by_id(image_id)
        image_path = Path(os.path.join(current_app.config['UPLOAD_FOLDER'], image.path))
        if not image:
            abort(404, message='Image {} does not exist'.format(id))
        if image_path.is_file():
            image_path.unlink()
        # Delete 'images' directory if empty
        image_path = image_path.parent
        if not os.listdir(str(image_path)):
            image_path.rmdir()
        # Delete PK directory if empty
        image_path = image_path.parent
        print(str(image_path))
        if not os.listdir(str(image_path)):
            image_path.rmdir()
        record.images.remove(image)
        log_entry = 'Image deleted: <strong>{0}</strong>'.format(image.title or '')
        record.add_change_log_entry(action='Remove', field='Image', original_value=log_entry)
        image.delete()
        record.save()
        return jsonify({'message': 'Successfully deleted Image {}'.format(id)})


class GenericLinkResource(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('url', type=str, default="",
                                   location="form")
        self.reqparse.add_argument('title', type=str, default="",
                                   location="form")
        self.reqparse.add_argument('description', type=str, default="",
                                   location="form")
        super(GenericLinkResource, self).__init__()

    @login_required
    def post(self, id, parent_class, link_id=None):
        if id and link_id is not None:
            return self.put(id, parent_class, link_id)
        data = self.reqparse.parse_args()
        title = data.title
        description = data.description
        url = formatUrl(data.url)
        link = Link(url, title, description, current_user.id)
        db.session.add(link)
        db.session.commit()
        parent = get_record_by_id_and_class(id, parent_class)
        parent.links.append(link)
        log_entry = '<a href="{0}" target="new">{1}</a>'.format(url, description or url)
        parent.add_change_log_entry(action='Add', field='URL', new_value=log_entry)
        db.session.add(parent)
        db.session.commit()
        variables = {
            'link': link,
            'parent_object': parent,
            'api_url': url_for("api.generic_links", id=id, parent_class=parent_class)
        }
        return render_template('shared/link_row.html', **variables)

    @login_required
    def put(self, id, parent_class, link_id):
        link = Link.get_by_id(link_id)

        if not link:
            abort(404, message="Link {} doesn't exist".format(id))
        data = self.reqparse.parse_args()
        description = data.description
        url = formatUrl(data.url)
        old_url = '<a href="{0}" target="new">{1}</a>'.format(link.url, link.description or link.url)
        new_url = '<a href="{0}" target="new">{1}</a>'.format(url, description or url)
        link.update(url=url, description=description)
        link.save()
        parent = get_record_by_id_and_class(id, parent_class)
        parent.add_change_log_entry(action='Edit', field='URL', original_value=old_url, new_value=new_url)
        variables = {
            'link': link,
            'parent_object': get_record_by_id_and_class(id, parent_class),
            'api_url': url_for("api.generic_links", id=id, parent_class=parent_class)
        }
        return render_template('shared/link_row.html', **variables)

    @login_required
    def delete(self, id, link_id, parent_class):
        parent = get_record_by_id_and_class(id, parent_class)
        link = Link.get_by_id(link_id)
        if not link:
            abort(404, message="Link {} doesn't exist".format(id))
        parent.links.remove(link)
        log_entry = '<a href="{0}" target="new">{1}</a>'.format(link.url, link.description or link.url)
        parent.add_change_log_entry(action='Remove', field='URL', original_value=log_entry)
        link.delete()
        db.session.add(parent)
        db.session.commit()
        return jsonify({'message': "Successfully deleted Link {}".format(id)})
