
How To Deploy PLAID
-------------------

The preferred method of deploying PLAID in a production environment is via Docker and Docker Compose.
``docker-compose.yml`` in this folder includes instructions for PLAID, RabbitMQ, and an NGINX server. You should use
NGINX for testing out this setup only, not in production.

To deploy on a server, ensure Docker and Docker Compose is installed. Instructions to install can be found here:
https://docs.docker.com/engine/installation/
https://docs.docker.com/compose/install/

It is also recommended that NGINX is installed on the server:
https://www.nginx.com/resources/wiki/start/topics/tutorials/install/

Then copy the following files from this folder to your server, at PRI the path would be ``/opt/pr/docker/plaid``:
``docker-compose.yml``
``dockerfile``
``run_celery.sh``
``run_gunicorn.sh``

Create ``logs`` and ``uploads`` directory with sub-directories:

.. code-block:: bash

    mkdir logs && mkdir logs/celery && mkdir logs/gunicorn && mkdir logs/plaid && mkdir logs/rabbitmq
    mkdir uploads && mkdir uploads/images && mkdir uploads/documents

Copy the NGINX configuration to the server and symlink it to ``sites-enabled``:
``plaid.conf.nginx``

All you need to do now to build the PLAID Docker image and container is:

.. code-block:: bash

    sudo su
    cd /opt/pr/docker/plaid
    docker-compose up -d plaid
