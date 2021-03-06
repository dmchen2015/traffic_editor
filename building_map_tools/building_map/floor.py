import math
import os
import shutil

import shapely.geometry
import shapely.ops

from xml.etree.ElementTree import SubElement
from ament_index_python.packages import get_package_share_directory


class Floor:
    def __init__(self, yaml_node, level_vertices):
        self.vertices = []
        self.thickness = 0.1
        vert_list = []
        for v_idx in yaml_node['vertices']:
            v = level_vertices[v_idx]
            #self.vertices.append([v.x, v.y])
            self.vertices.append(shapely.geometry.Point(v.x, v.y))
            vert_list.append((v.x, v.y))

        self.polygon = shapely.geometry.Polygon(vert_list)
        self.multipoint = shapely.geometry.MultiPoint(vert_list)

    def __str__(self):
        return f'floor ({len(self.vertices)} vertices)'

    def __repr__(self):
        return self.__str__()

    def find_vertex_idx(self, x, y):
        for v_idx, v in enumerate(self.vertices):
            dx = x - v.x
            dy = y - v.y
            d = math.sqrt(dx*dx + dy*dy)
            if d < 0.0001:
                return v_idx
        raise RuntimeError("Couldn't find vertex index!")

    def triangle_to_vertex_index_list(self, triangle, vertices):
        vertex_idx_list = []
        c = triangle.exterior.coords  # save typing, make it easier to read
        vertex_idx_list.append(self.find_vertex_idx(c[0][0], c[0][1]))
        vertex_idx_list.append(self.find_vertex_idx(c[1][0], c[1][1]))
        vertex_idx_list.append(self.find_vertex_idx(c[2][0], c[2][1]))
        return vertex_idx_list

    def generate(self, model_ele, floor_cnt, model_name, model_path):
        print(f'generating floor polygon {floor_cnt} on floor')
        # for v in self.vertices:
        #     print(f'  {v.x} {v.y}')

        link_ele = SubElement(model_ele, 'link')
        link_ele.set('name', f'floor_{floor_cnt}')

        visual_ele = SubElement(link_ele, 'visual')
        visual_ele.set('name', 'visual')

        visual_geometry_ele = SubElement(visual_ele, 'geometry')

        mesh_ele = SubElement(visual_geometry_ele, 'mesh')
        mesh_uri_ele = SubElement(mesh_ele, 'uri')

        meshes_path = f'{model_path}/meshes'
        if not os.path.exists(meshes_path):
            os.makedirs(meshes_path)

        obj_model_rel_path = f'meshes/floor_{floor_cnt}.obj'
        mesh_uri_ele.text = f'model://{model_name}/{obj_model_rel_path}'

        '''
        material_ele = SubElement(visual_ele, 'material')
        material_script_ele = SubElement(material_ele, 'script')
        material_script_name_ele = SubElement(material_script_ele, 'name')
        material_script_name_ele.text = 'SossSimulation/SimpleFloor'

        self.generate_geometry(visual_ele)
        '''

        collision_ele = SubElement(link_ele, 'collision')
        collision_ele.set('name', 'collision')
        # Use the mesh as a collision element
        collision_geometry_ele = SubElement(collision_ele, 'geometry')
        collision_mesh_ele = SubElement(collision_geometry_ele, 'mesh')
        collision_mesh_uri_ele = SubElement(collision_mesh_ele, 'uri')
        collision_mesh_uri_ele.text = f'model://{model_name}/{obj_model_rel_path}'


        surface_ele = SubElement(collision_ele, 'surface')
        contact_ele = SubElement(surface_ele, 'contact')
        collide_bitmask_ele = SubElement(contact_ele, 'collide_bitmask')
        collide_bitmask_ele.text = '0x01'

        #triangles = tripy.earclip(self.vertices)
        triangles_convex = shapely.ops.triangulate(self.multipoint)
        triangles = []
        for triangle_convex in triangles_convex:
            print(f'before intersection: {triangle_convex.wkt}')
            poly = triangle_convex.intersection(self.polygon)
            #poly = triangle_convex
            if poly.is_empty:
                print("empty intersection")
                continue
            if poly.geom_type == 'Polygon':
                print(f'  after: {poly.wkt}')
                poly = shapely.geometry.polygon.orient(poly)
                print(f'  after orient: {poly.wkt}')
                triangles.append(poly)
            elif poly.geom_type == 'MultiLineString':
                print('Found a multilinestring. Ignoring it...')
            else:
                print('Found something else weird. Ignoring it...')

        # for unknown reasons, it seems that shapely.ops.triangulate
        # doesn't return a list of vertices and triangles as indices,
        # instead you get a bunch of coordinates, so we'll re-build
        # a triangle index list now. There must be an easier way...
        tri_vertex_indices = []
        for triangle in triangles:
            tri_vertex_indices.append(
                self.triangle_to_vertex_index_list(triangle, self.vertices))
        print(tri_vertex_indices)
            
        obj_path = f'{model_path}/{obj_model_rel_path}'
        with open(obj_path, 'w') as f:
            f.write('# The Great Editor v0.0.1\n')
            f.write(f'mtllib floor_{floor_cnt}.mtl\n')
            f.write(f'o floor_{floor_cnt}\n')

            # this assumes that the vertices are in "correct" (OBJ) winding
            # ordering already. todo: detect if the winding order is
            # inverted and re-wind appropriately
            # In order for the floors to be seen from below,
            # we also add another set of vertices "below" the floor thickness
            for v in self.vertices:
                f.write(f'v {v.x} {v.y} 0\n')
                f.write(f'v {v.x} {v.y} -{self.thickness}\n')

            # in the future we may have texture tiles of a different size,
            # but for now let's assume 1-meter x 1-meter tiles, so we don't
            # need to scale the texture coordinates currently.
            for v in self.vertices:
                f.write(f'vt {v.x} {v.y} 0\n')

            # our floors are always flat (for now), so normals are up or down
            f.write(f'vn 0 0 1\n')
            f.write(f'vn 0 0 -1\n')

            f.write(f'usemtl floor_{floor_cnt}\n')
            f.write('s off\n')

            for triangle in tri_vertex_indices:
                # todo... clean this up. For now, wind the triangles both ways

                f.write('f')
                for v_idx in triangle:
                    f.write(f' {2*v_idx+1}/{v_idx+1}/1')
                f.write('\n')

                # now add the triangle on the bottom-side of the floor
                f.write('f')
                for v_idx in reversed(triangle):
                    f.write(f' {2*v_idx+2}/{v_idx+1}/2')
                f.write('\n')

        print(f'  wrote {obj_path}')

        mtl_path = f'{model_path}/meshes/floor_{floor_cnt}.mtl'
        with open(mtl_path, 'w') as f:
            f.write('# The Great Editor v0.0.1\n')
            f.write(f'newmtl floor_{floor_cnt}\n')
            f.write('Ka 1.0 1.0 1.0\n')  # ambient
            f.write('Kd 1.0 1.0 1.0\n')  # diffuse
            f.write('Ke 0.0 0.0 0.0\n')  # emissive
            f.write('Ns 50.0\n')  # specular highlight, 0..100 (?)
            f.write('Ni 1.0\n')  # no idea what this is
            f.write('d 1.0\n')  # alpha (maybe?)
            f.write('illum 2\n')  # illumination model (enum)
            f.write(f'map_Kd floor_{floor_cnt}.png\n')

        print(f'  wrote {mtl_path}')

        # todo: read texture parameter somehow from YAML
        # for now, just use blue linoleum
        # todo: use ament_resource_index somehow to calculate this path
        texture_path_source = os.path.join(
            get_package_share_directory('building_map_tools'),
            'textures/blue_linoleum.png')
        texture_path_dest = f'{model_path}/meshes/floor_{floor_cnt}.png'
        shutil.copyfile(texture_path_source, texture_path_dest)
        print(f'  wrote {texture_path_dest}')
