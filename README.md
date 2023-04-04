# LTest

*Simple forking server for testing with reusable context*

## Overview

**ltest** is extremeply simple forking server based on PyTest for local
testing. The main goal of the project is to preload "fat" libraries like JAX or
TensorFlow in execution context of PyTest. It is written from scratch with
naked Python standard library and, of course, [pytest][1].

It seems that it should be rewritten to use IPython kernel for better coherence
with Jupyter since a lot of machine learning practitioners and researchers use
it for development and testing. So, IPython could reduce possible unexpected
side effects.

### Usage Example

Here's an example usage of the `ltest` local PyTest server.

Suppose you have a project that uses JAX and you want to run your tests with
PyTest. However, importing JAX takes a significant amount of time, which slows
down your tests. To speed up your tests, you can use the PyTest testing server
to preload JAX before running the tests.

First, create a Python script that defines your PyTest tests. Here's an example.

```python
# simple_test.py
import jax, jax.numpy as jnp
from numpy.testing import assert_array_equal


def test_jitting():
    def mul2(xs):
        return xs * 2
    xs = jnp.ones(10)
    ys = jax.jit(mul2)(xs)
    assert_array_equal(2 * xs, ys)
```

Next, start the PyTest testing server.

```shell
ltest -l -m jax
```

This starts the testing server on the default interface `127.0.0.1` and port
`7070` and preloads the `jax` package.

Finally, run your tests using the client.

```shell
ltest -- -s -v
```

This sends a request to the testing server to run the PyTest tests. The `-s`
and `-v` options after `--` are passted to PyTest and used to display output
from the tests. The server responds with a JSON object that contains the exit
code of the tests.

### Command Line Interface (CLI)

#### Starting Server

```shell
ltest -l -m preloaded_pkg -m another.preloaded.pkg
```

#### Run Test on Local Server

```shell
ltest -- --co
```

#### Run Tests with Arguments on Local Server

```shell
ltest -- -v --tb=full -m slow -- path/to/suite/my_test.py
```

[1]: https://github.com/pytest-dev/pytest.git
