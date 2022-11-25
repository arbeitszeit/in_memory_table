WARNING
=======

This package is part of the development effort of `arbeitszeitapp
<https://github.com/arbeitszeit/arbeitszeitapp>`_. It it not meant for
public consumption. No though went into the security aspects of this
package as its intended use is in the test suite of arbeitszeitapp. If
you need something similar to this in your application we recommend
using `pandas <https://github.com/pandas-dev/pandas>`_ or something
similar.

in_memory_table
===============

The goal of this package is provide an easy way have the behavior of a
relational database without the performance penalty that comes from
using one. The target application of this code is in testing where we
deal with a low volume of data.
