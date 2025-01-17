"""Tests for handling PYI code."""

from pytype import file_utils
from pytype.tests import test_base


class PYITest(test_base.BaseTest):
  """Tests for PYI."""

  def test_unneccessary_any_import(self):
    ty = self.Infer("""
        import typing
        def foo(**kwargs: typing.Any) -> int: return 1
        def bar(*args: typing.Any) -> int: return 2
        """)
    self.assertTypesMatchPytd(ty, """
        typing = ...  # type: module
        def foo(**kwargs) -> int: ...
        def bar(*args) -> int: ...
        """)

  def test_static_method_from_pyi_as_callable(self):
    with file_utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        class A:
          @staticmethod
          def callback(msg: str) -> None: ...
      """)
      self.Check("""
        from typing import Any, Callable
        import foo
        def func(c: Callable[[Any], None], arg: Any) -> None:
          c(arg)
        func(foo.A.callback, 'hello, world')
      """, pythonpath=[d.path])

  def test_class_method_from_pyi_as_callable(self):
    with file_utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        class A:
          @classmethod
          def callback(cls, msg: str) -> None: ...
      """)
      self.Check("""
        from typing import Any, Callable
        import foo
        def func(c: Callable[[Any], None], arg: Any) -> None:
          c(arg)
        func(foo.A.callback, 'hello, world')
      """, pythonpath=[d.path])


class PYITestPython3Feature(test_base.BaseTest):
  """Tests for PYI."""

  def test_bytes(self):
    with file_utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        def f() -> bytes: ...
      """)
      ty = self.Infer("""
        import foo
        x = foo.f()
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        foo = ...  # type: module
        x = ...  # type: bytes
      """)

  def test_collections_abc_callable(self):
    with file_utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        from collections.abc import Callable
        def f() -> Callable[[], float]: ...
      """)
      ty, _ = self.InferWithErrors("""
        import foo
        func = foo.f()
        func(0.0)  # wrong-arg-count
        x = func()
      """, pythonpath=[d.path])
      self.assertTypesMatchPytd(ty, """
        from typing import Callable
        foo: module
        func: Callable[[], float]
        x: float
      """)


if __name__ == "__main__":
  test_base.main()
