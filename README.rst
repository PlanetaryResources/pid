**PLAnetary Information Database (PLAID)**
==========================================

PLAID is a direct response to the common plight of small companies with
operations that span both hardware design and production; how do they
fulfill their need for basic PLM and ERP functionality without the
crushing cost and overhead of implementing two separate enterprise
software packages.

PLAID is based on lessons learned during a decade of Mars rover
hardware development and delivery at NASA’s Jet Propulsion Laboratory
and half a decade of satellite development and operation at Planetary
Resources, Inc.  PLAID is the software I wished JPL had and that
Planetary Resources allowed to happen.

PLAID is a database and front end designed to capture, archive and
present data related to the design, production and testing of hardware
– in broad terms, it is used to answer:

1. How do I make X?  

   - Collect and relate all the information that describes the design of a product

2. Is X okay / ready to use?  

   - Collect and relate all the information that describes the pedigree of a specific instance of a product


In particular, PLAID is intended to:

1. Allow every in the company to access and contribute to:

   - Design Information
   - Product Information
   - Status of Designs and Products

2. Create a controlled, searchable repository for company infrastructure and standards
3. Standardize data type terms and definitions
4. Encourage Ownership
5. Manage Design Numbers
6. Manage peer review of critical data
7. Revision control and freeze database records
8. Help everyone in the company answer critical questions during spacecraft development and delivery

   - What do I need to make?
   - What do I plan to make?
   - What did I make?
   - Does what I made match what I planned to make?
   - Does what I made do what it needs to do?

PLAID is structured around a very particular set of data types that are
specifically defined to cover the full range of hardware development
activities and all of the “what-if” situations I’ve ever encountered
during my career.   It is critical that anyone using PLAID, or developing
hardware, have a clear and common understanding of the data types being
managed.  Those data types include::

|RECORD TYPE|RECORD ID FORMAT|RECORD DESCRIPTION / DEFINITION|
|-----------|----------------|------------------------------------------------|
|**Design**|1234567 (w/ revision)|A description of one or more related items in response to a particular set of requirements|
|**Part**|1234567-1, -2|One or more objects defined by a particular Design; variants are uniquely identified by a -#|
|**Revision**|A, B...|An update to a Design for the purpose of correction, improvement or to meet updated requirements|
|**Product, S/N**|1234567-1 S/N 001|A physical instance of a Part|
|**Product, LOT**|1234567-1 LOT 001|A group of interchangeable physical instances of a Part|
|**Build**|1234567-1 B001|A convenience; A batch of Products purchased, fabricated or built together|
|**Vendor Part**|(anything)|A catalog part offered for purchase by a third-party vendor, not per a internal company design.|
|**Vendor Product**|(anything)|A physical instance, or group of instances, of a Vendor Part|
|**Discrepancy**|(product_num)-##|Any deviation of a Product from its drawing or other design description (i.e. not built as designed)|
|**Anomaly**|A-123456|Any deviation of a Product from expected behavior or performance (i.e. built as designed but not designed correctly)|
|**ECO**|ECO-123456|Description of and justification for a change to a Design - an intermediate step towards a Revision
|**Procedure**|DOC-123456 (w/ revision)|Instructions for doing work|
|**As-Run**|DOC-123456-001|A numbered instance of a Procedure - the record of actually doing the work as instructed|
|**Specification**|PRI-12345|General Company standards and/or process description|
|**Task**|T-123456|A request for someone to do / make / fix / test / etc. something|
 
*Sean Haggart, PLAID task manager and Senior Mechanical Engineer for Planetary Resources, Inc.*


*Provided to the open-source community by ConsenSys, June 2019.*
*Chris Lewicki, former CEO, Planetary Resources, Inc. / Co-Founder ConsenSys Space*

Quickstart
----------

On OSX, ensure you have Homebrew installed: http://brew.sh/

Install Python3, PostgreSQL and RabbitMQ:

.. code-block:: bash

    brew install python3
    brew install postgresql
    brew install rabbitmq

Then configure RabbitMQ:

.. code-block:: bash

    sudo rabbitmq-server -detached
    sudo rabbitmqctl add_user plaid_dev_rabbit complicated-password-here
    sudo rabbitmqctl add_vhost plaid_dev_amqp
    sudo rabbitmqctl set_permissions -p plaid_dev_amqp plaid_dev_rabbit ".*" ".*" ".*"

These commands will need to be run each time you've rebooted:

.. code-block:: bash

    pg_ctl -D /usr/local/var/postgres start
    sudo rabbitmq-server -detached
    celery -A celery_worker.celery worker --loglevel=info

Once you have installed your DBMS, run the following to create your app's database tables and perform the initial migration:

.. code-block:: bash

    python manage.py db init
    python manage.py db migrate
    python manage.py db upgrade
    python magic_import.py
    python manage.py server

Then run the following commands to bootstrap your environment and start the server:

.. code-block:: bash

    git clone https://github.com/pri-web/pid.git
    cd pid
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements/dev.txt
    python manage.py server

You will see a pretty welcome screen.

If you want to use Flask commands instead, add the following to ``.bashrc`` or ``.bash_profile``.

.. code-block:: bash

    export FLASK_APP=/path/to/pid/autoapp.py
    export FLASK_DEBUG=1

Then you can execute the same commands as above with:

::

    flask db init
    flask db migrate
    flask db upgrade
    flask run


Deployment
----------

In your production environment, make sure the ``PLAID_ENV`` environment variable is set to ``"prod"``.

Follow the steps described in deployment/README.rst


Shell
-----

To open the interactive shell, run ::

    python manage.py shell

By default, you will have access to ``app``, ``db``, and the ``User`` model.


Running Tests
-------------

To run all tests, run ::

    python manage.py test


Migrations
----------

Whenever a database migration needs to be made. Run the following commands:
::

    python manage.py db migrate

This will generate a new migration script. Then run:
::

    python manage.py db upgrade

To apply the migration.

For a full migration command reference, run ``python manage.py db --help``.
