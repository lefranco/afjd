""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser.local_storage import storage  # pylint: disable=import-error


# simplest is to hard code displays of variants here
INTERFACE_TABLE = {
    'standard': ['diplomania', 'diplomania_daltoniens', 'hasbro'],
    'duel': ['diplomania']
}


def get_inforced_interface_from_variant(variant):
    """ get_inforced_interface_from_variant """

    # takes the first
    return INTERFACE_TABLE[variant][0]


def get_interface_from_variant(variant):
    """ get_interface_from_variant """

    reference = f'DISPLAY_{variant}'.upper()
    if reference in storage:
        return storage[reference]

    # takes the first
    return INTERFACE_TABLE[variant][0]


def set_interface(variant_name, user_interface):
    """ set_interface """

    reference = f'DISPLAY_{variant_name}'.upper()
    storage[reference] = user_interface
