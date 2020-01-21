import os
from xml.etree.ElementTree import Element, SubElement, parse

from .level import Level


class Building:
    def __init__(self, yaml_node):
        if 'building_name' in yaml_node:
          self.name = yaml_node['building_name']
        else:
          self.name = yaml_node['name']
        print(f'building name: {self.name}')

        self.levels = {}
        for level_name, level_yaml in yaml_node['levels'].items():
            self.levels[level_name] = Level(level_yaml, level_name)

    def __str__(self):
        s = ''
        for level_name, level_data in self.levels.items():
            s += f'{level_name}: ({len(level_data.vertices)} vertices) '
        return s

    def generate_nav_graphs(self):
        """ Returns a dict of all non-empty nav graphs """
        print("generating nav data")
        nav_graphs = {}
        # at the moment, graphs are numbered 0..9
        # iterate through and generate any non-empty graphs
        for i in range(0, 9):
            g = {}
            g['building_name'] = self.name
            g['levels'] = {}
            empty = True
            for level_name, level in self.levels.items():
                level_graph = level.generate_nav_graph(i)
                g['levels'][level_name] = level_graph
                if level_graph['lanes']:
                    empty = False
            if not empty:
                nav_graphs[f'{i}'] = g
        return nav_graphs

    def generate_sdf_world(self):
        """ Return an etree of this Building in SDF starting from a template"""
        file_dir = os.path.dirname(os.path.realpath(__file__))
        tree = parse(file_dir + '/templates/ign_world.sdf')
        sdf = tree.getroot()

        world = sdf.find('world')

        for level_name, level in self.levels.items():
            level.generate_sdf_models(world)  # todo: a better name
            level.generate_doors(world)

            level_include_ele = SubElement(world, 'include')
            level_model_name = f'{self.name}_{level_name}'
            name_ele = SubElement(level_include_ele, 'name')
            name_ele.text = level_model_name
            uri_ele = SubElement(level_include_ele, 'uri')
            uri_ele.text = f'model://{level_model_name}'
            pose_ele = SubElement(level_include_ele, 'pose')
            pose_ele.text = '0 0 0 0 0 0'

        return sdf

    def generate_sdf_models(self, models_path):
        for level_name, level in self.levels.items():
            model_name = f'{self.name}_{level_name}'
            model_path = os.path.join(models_path, model_name)
            if not os.path.exists(model_path):
                os.makedirs(model_path)

            level.generate_sdf_model(model_name, model_path)
