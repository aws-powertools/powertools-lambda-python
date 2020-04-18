from typing import AnyStr, Dict, Tuple, Type


class RegisterMeta(type):
    _instances = {}

    def __call__(cls: Type, *args: Tuple, **kwargs: Dict):
        """Register class instance at initialization

        It only returns an existing instance via `instance`
        method  e.g. `Tracer.instance()`.

        Not a Singleton per se as it only returns an existing
        instance via the `instance` method.

        Parameters
        ----------
        cls : type
            Class using metaclass
        args : tuple
            Tuple with arguments for class instantiation
        kwargs : dict
            Dict with all keyword arguments
        """
        if cls not in RegisterMeta._instances:
            RegisterMeta._instances[cls] = super().__call__(*args, **kwargs)
            return RegisterMeta._instances[cls]

        return super().__call__(**kwargs)

    def __init__(cls: Type, cls_name: AnyStr, bases: Tuple, class_dict: Dict):
        """Inject instance, clear_instance classmethods to newly built class

        Parameters
        ----------
        cls : type
            Class using metaclass
        cls_name : str
            Class name
        bases : tuple
            Inherited classes
        class_dict : dict
            Class body as dict
        """
        setattr(cls, instance.__name__, classmethod(instance))
        setattr(cls, clear_instance.__name__, classmethod(clear_instance))


def instance(cls):
    """Returns registered class instance

    This allows us to prevent double initialization
    when needed, reuse previous instance and its attributes,
    and still allow multiple inheritance and __new__.
    """
    if cls not in RegisterMeta._instances:
        return cls.__call__(cls)

    return RegisterMeta._instances[cls]


def clear_instance(cls):
    """Destroys registered class instance"""
    if cls in RegisterMeta._instances:
        del RegisterMeta._instances[cls]
