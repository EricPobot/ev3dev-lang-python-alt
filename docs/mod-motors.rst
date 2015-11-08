``ev3dev.motors``
=================

The ``ev3dev.motors`` modules gathers modules gathers the definitions for supported motors.

These classes are intended to be used by the developer of an ev3dev application.

.. automodule:: ev3dev.motors

Module interface
----------------

.. autosummary::
    :nosignatures:

    BaseMotor
    PositionControlMixin
    DcMotor
    RegulatedMotor
    MediumMotor
    LargeMotor
    ServoMotor

Reference
---------

Base classes
^^^^^^^^^^^^

.. autoclass:: BaseMotor
    :members:

.. autoclass:: PositionControlMixin
    :members:

.. autoclass:: RegulatedMotor
    :members:

Concrete classes
^^^^^^^^^^^^^^^^

.. autoclass:: MediumMotor
    :members:
    :show-inheritance:

.. autoclass:: LargeMotor
    :members:
    :show-inheritance:

.. autoclass:: DcMotor
    :members:
    :show-inheritance:

.. autoclass:: ServoMotor
    :members:
    :show-inheritance:
