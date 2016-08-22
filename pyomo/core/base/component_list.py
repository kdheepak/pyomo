#  _________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2014 Sandia Corporation.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  This software is distributed under the BSD License.
#  _________________________________________________________________________

__all__ = ("ComponentList",)

import weakref
import collections

from pyomo.core.base.component_interface import \
    (IComponentContainer,
     _abstract_readwrite_property)

class ComponentList(IComponentContainer,
                    collections.MutableSequence):
    """A partial implementation of the IComponentContainer
    interface that presents list-like storage functionality.
    """
    __slots__ = ()

    def __init__(self, *args):
        self._data = []
        if len(args) > 0:
            if len(args) > 1:
                raise TypeError(
                    "%s expected at most 1 arguments, "
                    "got %s" % (self.__class__.__name__,
                                len(args)))
            for item in args[0]:
                self.append(item)

    #
    # Implementations can choose to define these
    # properties as using __slots__, __dict__, or
    # by overriding the @property method
    #

    _data = _abstract_readwrite_property()

    #
    # Define the IComponentContainer abstract methods
    #

    def components(self):
        return self._data.__iter__()
    children = components

    def child_key(self, child):
        return self.index(child)

    #
    # Define the MutableSequence abstract methods
    #

    def __setitem__(self, i, item):
        if item.ctype == self.ctype:
            if item._parent is None:
                # be sure to "delete" the current
                # item by resetting its ._parent
                self._data[i]._parent = None
                item._parent = weakref.ref(self)
                if hasattr(self, "_active"):
                    self._active |= getattr(item, '_active', True)
                self._data[i] = item
                return
            elif self._data[i] is item:
                # a very special case that makes sense to handle
                # because the implied order should be: (1) delete
                # the object at the current index, (2) insert the
                # the new object. This performs both without any
                # actions, but it is an extremely rare case, so
                # it should go last.
                return
            # see note about allowing components to live in more than
            # one container
            raise ValueError(
                "Invalid assignment to %s type with name '%s' "
                "at index %s. A parent container has already been "
                "assigned to the component being inserted: %s"
                % (self.__class__.__name__,
                   self.name(True),
                   i,
                   item.parent.name(True)))
        else:
            raise TypeError(
                "Invalid assignment to type %s with index %s. "
                "The component being inserted has the wrong "
                "component type: %s"
                % (self.__class__.__name__,
                   i,
                   item.ctype))

    def insert(self, i, item):
        if item.ctype == self.ctype:
            if item._parent is None:
                item._parent = weakref.ref(self)
                if hasattr(self, "_active"):
                    self._active |= getattr(item, '_active', True)
                self._data.insert(i, item)
                return
            # see note about allowing components to live
            # in more than one container
            raise ValueError(
                "Invalid assignment to type %s with index %s. "
                "A parent container has already been "
                "assigned to the component being inserted: %s"
                % (self.__class__.__name__,
                   i,
                   item.parent.name(True)))
        else:
            raise TypeError(
                "Invalid assignment to type %s with index %s. "
                "The component being inserted has the wrong "
                "component type: %s"
                % (self.__class__.__name__,
                   i,
                   item.ctype))

    def __delitem__(self, i):
        obj = self._data[i]
        obj._parent = None
        del self._data[i]

    def __getitem__(self, i):
        return self._data[i]

    def __len__(self):
        return self._data.__len__()

    #
    # Override a few default implementations on MutableSequence
    #

    # We want to avoid generating Pyomo expressions by
    # comparing values
    def __contains__(self, item):
        item_id = id(item)
        return any(item_id == id(_v) for _v in self._data)

    # We want to avoid generating Pyomo expressions by
    # comparing values
    def index(self, item, start=0, stop=None):
        """S.index(value, [start, [stop]]) -> integer -- return first index of value.

           Raises ValueError if the value is not present.
        """
        if start is not None and start < 0:
            start = max(len(self) + start, 0)
        if stop is not None and stop < 0:
            stop += len(self)

        i = start
        while stop is None or i < stop:
            try:
                if self[i] is item:
                    return i
            except IndexError:
                break
            i += 1
        raise ValueError

    # We want to avoid generating Pyomo expressions by
    # comparing values
    def count(self, item):
        'S.count(value) -> integer -- return number of occurrences of value'
        item_id = id(item)
        cnt = sum(1 for _v in self._data if id(_v) == item_id)
        assert cnt == 1
        return cnt

    # Avoid errors related to calling __setitem__
    # with a component that is already owned
    def reverse(self):
        'S.reverse() -- reverse *IN PLACE*'
        n = len(self)
        data = self._data
        for i in range(n//2):
            data[i], data[n-i-1] = data[n-i-1], data[i]

if __name__ == "__main__":

    class VarList(ComponentList):
        __slots__ = ("_ctype",
                     "_parent",
                     "_data")
        def __init__(self, *args, **kwds):
            self._ctype = "Var"
            self._parent = None
            self._data = {}
            super(VarList, self).__init__(*args, **kwds)

    v = VarList()
    print("issubclass: "+str(issubclass(ComponentList,
                                        collections.MutableMapping)))
    print("issubclass: "+str(issubclass(VarList,
                                        collections.MutableMapping)))
    print("isinstance: "+str(isinstance(v,
                                        collections.MutableMapping)))
    print(v)