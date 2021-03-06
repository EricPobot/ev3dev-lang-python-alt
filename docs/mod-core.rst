``ev3dev.core``
===============

The ``ev3dev.core`` modules gathers the base definitions used by the other modules of the layer.

Most of these classes are not intended to be used by the developer of an ev3dev application.

.. automodule:: ev3dev.core

.. toctree::
   :maxdepth: 2

Module interface
----------------

.. autosummary::
    :nosignatures:

    Device
    Led
    PowerSupply
    ButtonManagerBase
    ButtonManagerEVIO

Reference
---------

.. autoclass:: Device
    :members:

.. autoclass:: Led
    :members:

.. autoclass:: PowerSupply
    :members:


.. autoclass:: ButtonManagerBase
    :members:
    :inherited-members:

.. autoclass:: ButtonManagerEVIO
    :members:
    :inherited-members:
