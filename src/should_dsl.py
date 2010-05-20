import sys

class Should(object):

    def __init__(self, negate=False, have=False):
        self._negate = negate
        self._have = have
        self._matchers_by_name = dict()
        self.__set_default_matcher()

    def _evaluate(self, value):
        if self._negate:
            return not value
        return value

    def _negate_str(self):
        if not self._negate:
            return 'not '
        return ''

    def __ror__(self, lvalue):
        self._lvalue = lvalue
        self._create_local_matchers()
        return self

    def __or__(self, rvalue):
        self._destroy_local_matchers()
        if not isinstance(rvalue, _Matcher):
            self._rvalue = rvalue
            return self._check_expectation()
        else:
            self._rvalue = rvalue.arg
            return self._make_a_copy(rvalue.function,
                rvalue.error_message, copy_values=True)._check_expectation()

    def __set_default_matcher(self):
        '''The default behavior for a should object, called on constructor'''
        if self._have:
            self._turn_into_should_have()
        else:
            self._turn_into_should_be()

    def _turn_into_should_have(self):
        self._func = lambda container, item: item in container
        self._error_message = '%s does %shave %s'

    def _turn_into_should_be(self):
        self._func = lambda x, y: x is y
        self._error_message = '%s is %s%s'

    def _make_a_copy(self, func, error_message, copy_values=False):
        clone = Should(self._negate)
        clone._matchers_by_name = self._matchers_by_name
        clone._func = func
        clone._error_message = error_message
        if copy_values:
          if hasattr(self, '_lvalue'):
              clone._lvalue = self._lvalue
          if hasattr(self, '_rvalue'):
              clone._rvalue = self._rvalue
        return clone

    def _check_expectation(self):
        evaluation = self._evaluate(self._func(self._lvalue, self._rvalue))
        if not evaluation:
            raise ShouldNotSatisfied(self._error_message % (self._lvalue,
                                                            self._negate_str(),
                                                            self._rvalue))
        return True

    def add_matcher(self, matcher_function):
        '''Adds a new matcher.
        The function must return a tuple (or any other __getitem__ compatible object)
        containing two elements:
        [0] = a function taking one or two parameters, that will do the desired comparison
        [1] = the error message. this message must contain three %s placeholders. By example,
        "%s is %snicer than %s" can result in "Python is nicer than Ruby" or
        "Python is not nicer than Ruby" depending whether |should_be.function_name| or
        |should_not_be.function_name| be applied.
        '''
        self._matchers_by_name[matcher_function.__name__] = matcher_function

    def __getattr__(self, method_name):
        if method_name not in self._matchers_by_name:
            raise AttributeError("%s object has no matcher '%s'" % (
                self.__class__.__name__, method_name))
        matcher_function = self._matchers_by_name[method_name]
        func, error_message = matcher_function()
        return self._make_a_copy(func, error_message)

    def _create_local_matchers(self):
        f_locals = sys._getframe(2).f_locals
        for matcher_name, matcher_function in self._matchers_by_name.iteritems():
            func, error_message = matcher_function()
            f_locals[matcher_name] = _Matcher(func, error_message)
            if not matcher_name.startswith('have_'):
                f_locals['have_' + matcher_name] = _Matcher(func, error_message)

    def _destroy_local_matchers(self):
        f_locals = sys._getframe(2).f_locals
        for matcher_name in self._matchers_by_name:
            del f_locals[matcher_name]
            if f_locals.has_key('have_'+matcher_name):
                del f_locals['have_'+matcher_name]


class _Matcher(object):
    def __init__(self, function, error_message):
        self.function = function
        self.error_message = error_message

    def __call__(self, arg):
        self.arg = arg
        return self


class ShouldNotSatisfied(AssertionError):
    '''Extends AssertionError for unittest compatibility'''

should_be = Should(negate=False)
should_not_be = Should(negate=True)
should_have = Should(negate=False, have=True)
should_not_have = Should(negate=True, have=True)
should = should_be
should_not = should_not_be

def matcher(matcher_function):
    '''Create customer should_be matchers. We recommend you use it as a decorator'''
    for should_object in (should_be, should_not_be, should_have, should_not_have):
        should_object.add_matcher(matcher_function)
    return matcher_function

import matchers

