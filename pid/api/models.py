# -*- coding: utf-8 -*-
"""Shared models."""
import datetime as dt
import os
import uuid
from flask import current_app, url_for
from flask_login import current_user
from pid.database import Column, Model, SurrogatePK, db, relationship, reference_col
from shutil import copyfile
from pathlib import Path


class Document(SurrogatePK, Model):
    """A document that can be tied to a design item, part, ECO, anomaly...etc"""
    __tablename__ = 'documents'
    path = Column(db.String, nullable=False, unique=True)
    title = Column(db.String)
    description = Column(db.Text)
    uploaded_by_id = reference_col('users', nullable=False)
    uploaded_by = relationship('User')
    uploaded_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def __init__(self, uploaded_by=current_user, **kwargs):
        """Create instance."""
        db.Model.__init__(self, uploaded_by=uploaded_by, **kwargs)

    def get_url(self):
        return url_for('api.documents', document_id=self.id, document_title=self.title)

    def clone_document(self, record):
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.path)
        new_basepath = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    record.get_class_name(), str(record.id), 'documents')
        new_path = os.path.join(new_basepath, self.path.split('/')[-1])
        if not os.path.exists(new_basepath):
            os.makedirs(new_basepath)
        copyfile(old_path, new_path)
        document = Document.create(path=new_path, title=self.title, description=self.description,
                                   uploaded_by=self.uploaded_by, uploaded_at=self.uploaded_at)
        extension = ''.join(Path(document.title).suffixes)  # Should get extensions like .tar.gz as well
        filename = '{0}{1}'.format(document.id, extension)
        filepath = os.path.join(new_basepath, filename)
        os.rename(new_path, filepath)
        document.path = os.path.relpath(new_basepath, current_app.config['UPLOAD_FOLDER']) + '/' + filename
        document.save()
        return document

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Document({title!r},{path!r})>'.format(title=self.title, path=self.path)


class Image(SurrogatePK, Model):
    """A document that can be tied to a design item, part, ECO, anomaly...etc"""
    __tablename__ = 'images'
    path = Column(db.String, nullable=False, unique=True)
    title = Column(db.String)
    description = Column(db.Text)
    uploaded_by_id = reference_col('users', nullable=False)
    uploaded_by = relationship('User')
    uploaded_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def __init__(self, uploaded_by=current_user, **kwargs):
        """Create instance."""
        db.Model.__init__(self, uploaded_by=uploaded_by, **kwargs)

    def get_url(self):
        return url_for('api.images', image_id=self.id, image_title=self.title)

    def clone_image(self, record):
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.path)
        new_basepath = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    record.get_class_name(), str(record.id), 'images')
        new_path = os.path.join(new_basepath, self.path.split('/')[-1])
        if not os.path.exists(new_basepath):
            os.makedirs(new_basepath)
        copyfile(old_path, new_path)
        image = Image.create(path=new_path, title=self.title, description=self.description,
                             uploaded_by_id=self.uploaded_by_id, uploaded_at=self.uploaded_at)
        extension = ''.join(Path(image.title).suffixes)  # Should get extensions like .tar.gz as well
        filename = '{0}{1}'.format(image.id, extension)
        filepath = os.path.join(new_basepath, filename)
        os.rename(new_path, filepath)
        image.path = os.path.relpath(new_basepath, current_app.config['UPLOAD_FOLDER']) + '/' + filename
        image.save()
        return image

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Image({title!r},{path!r})>'.format(title=self.title, path=self.path)


class Link(SurrogatePK, Model):
    """A link that can be tied to a design item, part, ECO, anomaly...etc"""
    __tablename__ = 'links'
    url = Column(db.String, nullable=False)
    description = Column(db.Text)
    created_by_id = reference_col('users', nullable=False)
    created_by = relationship('User')

    def __init__(self, url, title, description, created_by_id, **kwargs):
        """Create instance."""
        db.Model.__init__(self, url=url, description=description, created_by_id=created_by_id, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Link({url!r})>'.format(url=self.url)
