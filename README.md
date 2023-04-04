# LTest

*Simple forking server for testing with reusable context*

## Usage

**ltest** is extremeply simple forking server based on PyTest for local
testing. The main goal of the project is to preload "fat" libraries like JAX or
TensorFlow in execution context of PyTest. It is written from scratch with
naked Python standard library and, of course, [pytest][1].

It seems that it should be rewritten to use IPython kernel for better coherence
with Jupyter since a lot of machine learning practitioners and researchers use
it for development and testing. So, IPython could reduce possible unexpected
side effects.

#### Starting Server

```shell
ltest -l -m preloaded_pkg -m another.preloaded.pkg
```

#### Run Test on Local Server

```shell
ltest -- --co

#### Run Tests with Arguments on Local Server

```shell
ltest -- -v --tb=full -m slow -- path/to/suite/my_test.py
```

[1]: https://github.com/pytest-dev/pytest.git
