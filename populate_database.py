#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import the sqlite3 library
# import sqlite3  # For SQLite
import psycopg2  # For PGSQL

# create the connection object
# conn = sqlite3.connect('dev.db')  # For SQLite
conn_string = "host='localhost' dbname='pid_db'"  # For PGSQL
conn = psycopg2.connect(conn_string)  # For PGSQL

# get a cursor object used to execute SQL commands
c = conn.cursor()

# CREATE USERS
user_admin = '''INSERT INTO users(username, email, first_name, last_name, roles)
  VALUES('admin', 'jarle+admin@planetaryresources.com', 'Admin', 'Adminsen', 'plaid-users, plaid-admins')'''
user_user = '''INSERT INTO users(username, email, first_name, last_name, roles)
  VALUES('user', 'jarle+user@planetaryresources.com', 'User', 'Usersen', 'plaid-users')'''
user_superuser = '''INSERT INTO users(username, email, first_name, last_name, roles)
  VALUES('superuser', 'jarle+superuser@planetaryresources.com', 'Super', 'Usersen', 'plaid-users, plaid-superusers')'''
user_all = '''INSERT INTO users(username, email, first_name, last_name, roles)
  VALUES('all', 'jarle+all@planetaryresources.com', 'All', 'Roles', 'plaid-users, plaid-superusers, plaid-admins')'''
anomaly_key_seq= '''CREATE SEQUENCE anomaly_key_seq INCREMENT BY 1 MINVALUE 100000 OWNED BY anomalies.key;'''
eco_key_seq= '''CREATE SEQUENCE eco_key_seq INCREMENT BY 1 MINVALUE 100000 OWNED BY ecos.key;'''
spec_number_seq= '''CREATE SEQUENCE specification_number_seq INCREMENT BY 1 MINVALUE 100000 OWNED BY specifications.specification_number;'''
proc_number_seq= '''CREATE SEQUENCE procedure_number_seq INCREMENT BY 1 MINVALUE 100000 OWNED BY procedures.procedure_number;'''
task_number_seq = '''CREATE SEQUENCE task_number_seq INCREMENT BY 1 MINVALUE 100000 OWNED BY tasks.task_number;'''
c.execute(user_admin)
c.execute(user_user)
c.execute(user_superuser)
c.execute(user_all)
# TODO: Add to alembic migrate script?
c.execute(anomaly_key_seq)
c.execute(eco_key_seq)
c.execute(spec_number_seq)
c.execute(proc_number_seq)
c.execute(task_number_seq)
# IMPORT REAL-ISH DATA
f = open('prod.db.sql', 'r')
sql = f.read()
# c.executescript(sql)  # For SQLite
c.execute(sql)  # For PGSQL

# Commit all executions
conn.commit()
# Close the database connection
conn.close()
