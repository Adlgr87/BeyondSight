"""
Tests de seguridad en el manejo de errores (Fase 0.3).

Estos tests inspeccionan el SOURCE de ``app.py`` para verificar que no se
introducen regresiones donde contenido de excepciones se expone a la UI.

No se importa app.py directamente porque ejecuta código Streamlit en el
import (components.html, set_page_config) que no está disponible fuera
de ``streamlit run``. En su lugar, parseamos el AST y validamos patrones.
"""
import ast
import re
import unittest
from pathlib import Path


APP_PATH = Path(__file__).parent.parent / "app.py"


class ErrorSafetyTests(unittest.TestCase):

    def setUp(self):
        self.source = APP_PATH.read_text(encoding="utf-8")
        self.tree   = ast.parse(self.source)

    def _st_error_calls(self):
        """Yield every ``st.error(...)`` AST Call node in app.py."""
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "error"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "st"):
                yield node

    def test_no_st_exception_en_app(self):
        """``st.exception()`` imprime stack trace completo — nunca debe usarse."""
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "exception"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "st"):
                self.fail(
                    f"línea {node.lineno}: st.exception(...) filtra stack traces "
                    "completos a la UI. Usa _mostrar_error_seguro(e, contexto)."
                )

    def test_no_st_error_con_interpolacion_de_excepcion(self):
        """
        Cada argumento f-string de ``st.error(...)`` no puede interpolar la
        variable de excepción ``e`` (fuga de payload). Se permite
        explícitamente ``type(e).__name__`` que solo expone el nombre de
        clase.
        """
        problemas: list[str] = []
        for node in self._st_error_calls():
            for arg in node.args:
                if not isinstance(arg, ast.JoinedStr):
                    continue
                for pieza in arg.values:
                    if not isinstance(pieza, ast.FormattedValue):
                        continue
                    expr_src = ast.unparse(pieza.value).strip()
                    if expr_src == "type(e).__name__":
                        continue
                    if re.search(r"\be\b", expr_src):
                        problemas.append(
                            f"línea {node.lineno}: st.error f-string interpola '{expr_src}'"
                        )
        self.assertEqual(
            problemas, [],
            "Uso inseguro de st.error con la excepción:\n  "
            + "\n  ".join(problemas)
            + "\nReemplaza por _mostrar_error_seguro(e, 'contexto').",
        )

    def test_helper_mostrar_error_seguro_existe(self):
        """El wrapper de error seguro debe estar definido en app.py."""
        nombres_fn = {
            node.name for node in ast.walk(self.tree)
            if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("_mostrar_error_seguro", nombres_fn)

    def test_helper_tiene_firma_esperada(self):
        """_mostrar_error_seguro(e, contexto) — firma estable."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_mostrar_error_seguro":
                args = [a.arg for a in node.args.args]
                self.assertEqual(args, ["e", "contexto"])
                return
        self.fail("_mostrar_error_seguro no encontrado")

    def test_excepts_con_variable_e_usan_el_helper(self):
        """
        Todo bloque ``except ... as e:`` que referencia ``e`` en una
        llamada a ``st.*`` debe hacerlo vía ``_mostrar_error_seguro``.
        """
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.name != "e":
                continue
            # Recoge toda invocación st.xxx(...) dentro del handler que
            # referencie la variable `e` por su nombre en los argumentos.
            for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
                if not (isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and isinstance(child.func.value, ast.Name)
                        and child.func.value.id == "st"):
                    continue
                # ¿alguno de los argumentos del st.xxx() menciona `e`?
                src_args = " ".join(ast.unparse(a) for a in child.args)
                if re.search(r"\be\b", src_args):
                    self.fail(
                        f"línea {child.lineno}: except ... as e pasa `e` directamente "
                        f"a st.{child.func.attr}(...). Usa _mostrar_error_seguro(e, 'contexto')."
                    )


if __name__ == "__main__":
    unittest.main()
