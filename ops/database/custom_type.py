# -*- coding: utf-8 -*-

import sqlalchemy.types as types

class ChoiceType(types.TypeDecorator):

    impl = types.String(100)

    def __init__(self, choices=[], **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        result = [k for k, v in self.choices.iteritems() if k == value]
        if result:
            return result[0]

    def process_result_value(self, value, dialect):
        _dict = self.choices

        class Choice(object):
            def __init__(self):
                if not value == None:
                    self.label = _dict[value]
                    self.value = value
                else:
                    self.label = None
                    self.value = None
        return Choice()


class ChoiceTypeInteger(types.TypeDecorator):

    impl = types.Integer

    def __init__(self, choices=[], **kw):
        self.choices = dict(choices)
        super(ChoiceTypeInteger, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        result = [k for k, v in self.choices.iteritems() if k == value]
        if result:
            return result[0]

    def process_result_value(self, value, dialect):
        _dict = self.choices

        class Choice(object):
            def __init__(self):
                if not value == None:
                    self.label = _dict[value]
                    self.value = value
                else:
                    self.label = None
                    self.value = None
        return Choice()