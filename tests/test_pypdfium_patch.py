import os
import unittest
import weakref

os.environ.setdefault("API_TOKEN", "test-token")

import app


class PypdfiumPatchTests(unittest.TestCase):
    def test_finalizer_patch_tolerates_stale_child_weakref(self):
        import pypdfium2.internal.bases as pdfium_bases

        app.patch_pypdfium2_autoclose_finalizer()

        closed = []

        class Parent:
            _kids = set()

            def _tree_closed(self):
                return False

        class Kid:
            pass

        kid = Kid()

        class Info:
            state = pdfium_bases._STATE.AUTO
            tracked = True
            args = ()
            kwargs = {}

            @staticmethod
            def close_func(raw):
                closed.append(raw)

        class Owner:
            raw = "raw-page"
            parent = Parent()
            wref = weakref.ref(kid)
            type = Kid
            repr = "<PdfPage test>"

        pdfium_bases._close_template(Info(), Owner())

        self.assertEqual(closed, ["raw-page"])


if __name__ == "__main__":
    unittest.main()
