class RegisterMeta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        """Register class instance at first initialization

        It only returns an existing instance via `instance`
        method  e.g. `Tracer.instance()`.

        Not a Singleton per se as it only returns an existing
        instance via the `instance` method.
        """
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
            return cls._instance
        return super().__call__(*args, **kwargs)

    def instance(cls):
        """Returns registered class instance

        This allows us to prevent double initialization
        when needed, reuse previous instance and its attributes,
        and still allow multiple inheritance and __new__.
        """
        if cls._instance is None:
            return cls.__call__(cls)

        return cls._instance

    def clear_instance(cls):
        """Destroys registered class instance"""
        if cls._instance is not None:
            cls._instance = None
