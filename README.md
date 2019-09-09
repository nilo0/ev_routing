# Electrical Vehicles (EV) Routing

## Installation

Using `setyp.py`:

```bash
$ git clone https://github.com/nilo0/ev_routing.git
$ cd ev_routing
$ python3 setup.py install # --user in case you want to install it locally
```

Using `pip`:

```bash
$ git clone https://github.com/nilo0/ev_routing.git
$ cd ev_routing
$ pip install . # --user in case you want to install it locally
$ pip3 install . # --user in case you want to install it locally
```

To install the package locally in editable mode, run:

```bash
$ pip install -e . --user
$ pip3 install -e . --user
```

## Usage

```
    >>> from ev_routing import EVRouting
```

## Running tests

To run the tests, execute the following command:

```bash
$ python3 ./setup.py test
```

or

```bash
$ py.test # -s to show stdout
```

from the root directory of the package.
