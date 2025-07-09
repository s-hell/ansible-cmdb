import os
import importlib.util
import importlib.machinery
from mako.template import Template
from mako.lookup import TemplateLookup


class Render:
    """
    Wrapper class to facilitate rendering.

    This is mostly a helper class for finding template locations and
    initializing Mako properly. It can also call executable "templates" (python
    scripts) for rendering.

    """
    def __init__(self, tpl, tpl_dirs):
        self.tpl = tpl
        self.tpl_dirs = tpl_dirs
        self.tpl_possibilities = self._tpl_possibilities()
        self.tpl_file = self._find_tpl()

    def _tpl_possibilities(self):
        """
        Construct a list of possible paths to templates.
        """
        tpl_possibilities = [
            os.path.realpath(self.tpl)
        ]
        for tpl_dir in self.tpl_dirs:
            tpl_possibilities.append(os.path.realpath(os.path.join(tpl_dir, "{0}.tpl".format(self.tpl))))
            tpl_possibilities.append(os.path.realpath(os.path.join(tpl_dir, "{0}.py".format(self.tpl))))

        return tpl_possibilities

    def _find_tpl(self):
        """
        Find a template in the list of possible paths.
        """
        for tpl_possibility in self.tpl_possibilities:
            if os.path.isfile(tpl_possibility):
                return tpl_possibility

        return None

    def render(self, hosts, vars={}):
        """
        Render a mako or .py file.
        """
        if self.tpl_file.endswith(".tpl"):
            return self._render_mako(hosts, vars)
        elif self.tpl_file.endswith(".py"):
            return self._render_py(hosts, vars)
        else:
            raise ValueError("Don't know how to handle '{0}'".format(self.tpl_file))

    def _render_mako(self, hosts, vars={}):
        lookup = TemplateLookup(directories=self.tpl_dirs,
                                default_filters=['decode.utf8'],
                                input_encoding='utf-8',
                                output_encoding='utf-8',
                                encoding_errors='replace')
        template = Template(filename=self.tpl_file,
                            lookup=lookup,
                            default_filters=['decode.utf8'],
                            input_encoding='utf-8',
                            output_encoding='utf-8')
        return template.render(hosts=hosts, **vars)

    def load_source(self, modname, filename):
        loader = importlib.machinery.SourceFileLoader(modname, filename)
        spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module

    def _render_py(self, hosts, vars={}):
        module = self.load_source('r', self.tpl_file)
        return module.render(hosts, vars=vars, tpl_dirs=self.tpl_dirs)
