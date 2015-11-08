``ev3dev.sensors``
==================

The ``ev3dev.sensors`` modules gathers the definitions for supported sensors.

These classes are intended to be used by the developer of an ev3dev application.

.. automodule:: ev3dev.sensors

Module interface
----------------

.. autosummary::
    :nosignatures:

    Sensor
    I2cSensor
    TouchSensor
    ColorSensor
    UltrasonicSensor
    GyroSensor
    SoundSensor
    LightSensor
    InfraredSensor
    RemoteControl

Reference
---------

Generic sensors
^^^^^^^^^^^^^^^

.. autoclass:: Sensor
    :members:
    :show-inheritance:

.. autoclass:: I2cSensor
    :members:
    :show-inheritance:

Sensors
^^^^^^^

.. autoclass:: TouchSensor
    :members:
    :show-inheritance:

.. autoclass:: ColorSensor
    :members:
    :show-inheritance:

.. autoclass:: UltrasonicSensor
    :members:
    :show-inheritance:

.. autoclass:: GyroSensor
    :members:
    :show-inheritance:

.. autoclass:: SoundSensor
    :members:
    :show-inheritance:

.. autoclass:: LightSensor
    :members:
    :show-inheritance:

.. autoclass:: InfraredSensor
    :members:
    :show-inheritance:

.. autoclass:: RemoteControl
    :members:
    :inherited-members:
