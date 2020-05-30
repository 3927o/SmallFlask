class ModelMeta(type):
    def __new__(cls, name, base, attr_dict):
        if name == 'Model':
            return type.__new__(cls, name, base, attr_dict)
        attr_dict['__tablename__'] = attr_dict.get('__tablename__', name)
        mapping = dict()
        primary_key = None
        for k, v in attr_dict.items():
            if isinstance(v, Filed):
                mapping[k] = v

                if v.primary_key:
                    if primary_key:
                        raise TypeError("only one primary key allowed")
                    primary_key = v.name

        for k in mapping:
            attr_dict.pop(k)

        if not primary_key:
            raise TypeError("primary key is needed")

        attr_dict['__primary_key__'] = primary_key
        attr_dict['__mappings__'] = mapping

        return type.__new__(cls, name, base, attr_dict)


class Model(dict, metaclass=ModelMeta):
    def __init__(self, **kws):
        super(Model, self).__init__(kws)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise KeyError("object {} has no attribute {}".format(__name__, item))

    def __setattr__(self, key, value):
        self[key] = value


class Filed:
    def __init__(self, name, column_type, primary_key=False, default=None, nullable=True):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
        self.nullable = nullable


class IntegerField(Filed):
    def __init__(self, name, column_type='int', primary_key=False, default=None, nullable=True):
        super(IntegerField, self).__init__(name, column_type, primary_key, default, nullable)


class StringField(Filed):
    def __init__(self, name, column_type='varchar(255)', primary_key=False, default=None, nullable=True):
        super(StringField, self).__init__(name, column_type, primary_key, default, nullable)


class User(Model):
    id = IntegerField('id', primary_key=True)
    name = StringField('name')

    def __init__(self, id, name):
        self.id = id
        self.name = name


new_user = User(1, 'lin')
print(new_user)
