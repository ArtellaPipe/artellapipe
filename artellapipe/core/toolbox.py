from collections import OrderedDict

import artellapipe.register
from artellapipe.utils import plugin


class ToolBox(plugin.PluginManager, object):
    def __init__(self, project, parent=None):
        super(ToolBox, self).__init__()

        self._project = project
        self._parent = parent
        self._sub_menus = dict()

        self._menu_name = project.config_data.get('menu_name')
        self._menu_object_name = '{}_mainMenu'.format(self._project.get_clean_name())
        self._menu = None
        self._layout = dict()
        self._load_layouts()
        self._load_all_plugins()

    def create_menus(self):
        pass
        # self.clean_menus()
        # self.create_main_menu()

    def create_main_menu(self):
        self._menu = self._parent.menuBar().addMenu(self._menu_name)
        self._menu.setObjectName(self._menu_object_name)
        self._menu.setTearOffEnabled(True)

    def _load_layouts(self):
        pass

    def _load_all_plugins(self):
        pass


class ToolSet(object):
    def __init__(self):
        self._roots = OrderedDict()
        self._extension = '.json'


class MenuLayout(dict):
    pass


artellapipe.register.register_class('ToolBox', ToolBox)
