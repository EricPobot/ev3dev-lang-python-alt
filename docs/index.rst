.. python-ev3dev documentation master file

An alternative version of the ev3dev_ Python binding, written without using autogen.

.. _ev3dev: http://ev3dev.org

Target independent modules
--------------------------

They build the base layer of the library, and are not specific to any
target (e.g. EV3, BrickPi, PiStorm,...).

It has been chosen to split the
definitions into several distinct modules rather than having all of them
in a single module to limit its size, since as time passes and
features were added this module has passed the 1 klocs threshold. The modules
are organized by main concerns, and it is thus possible to import only a part
of them if the application does not use all the features. For instance, an application
which does not use the LCD does not need to import the ``ev3dev.display`` module.

.. toctree::
   :maxdepth: 1

   mod-core
   mod-sensors
   mod-motors
   mod-display
   mod-sound

Target support modules
----------------------

These modules implement the parts of the support which are specific to targets,
based on their individual features and characteristics.

.. toctree::
   :maxdepth: 1

   mod-ev3
   mod-brickpi

Extensions
----------

These modules and packages are extensions to the base services.

.. toctree::
   :maxdepth: 1

   mod-navigation

Demos
-----

Some demos illustrating use cases of the library and complete applications.

They are gathered in the `demos` sub-folder of the project.

.. toctree::
   :maxdepth: 1

   demo-basic
   demo-complex

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

