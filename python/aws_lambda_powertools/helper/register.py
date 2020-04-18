class RegisterMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Register class instance at initialization

        It only returns an existing instance via `instance`
        method  e.g. `Tracer.instance()`.

        Not a Singleton per se as it only returns an existing
        instance via the `instance` method.
        """
        if cls not in RegisterMeta._instances:
            RegisterMeta._instances[cls] = super().__call__(*args, **kwargs)
            return RegisterMeta._instances[cls]
        
        return super().__call__(**kwargs)

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
