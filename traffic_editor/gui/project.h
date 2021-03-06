/*
 * Copyright (C) 2019-2020 Open Source Robotics Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
*/

#ifndef PROJECT_H
#define PROJECT_H

#include "building.h"
#include "editor_model.h"
#include "editor_mode_id.h"
#include "scenario.h"

#include <string>
#include <vector>
#include <yaml-cpp/yaml.h>

class QGraphicsScene;
class QGraphicsItem;
class QGraphicsLineItem;


class Project
{
public:
  std::string name;
  std::string filename;

  Building building;
  std::vector<Scenario> scenarios;

  int scenario_idx = -1;  // the current scenario being viewed/edited

  /////////////////////////////////
  Project();
  ~Project();

  bool save();
  bool load(const std::string& _filename);

  void add_scenario_vertex(int level_index, double x, double y);
  void scenario_row_clicked(const int row);
  void draw(
      QGraphicsScene *scene,
      const int level_idx,
      std::vector<EditorModel>& editor_models);
  void clear_selection(const int level_idx);
  bool delete_selected(const int level_idx);

  struct NearestItem
  {
    double model_dist = 1e100;
    int model_idx = -1;

    double vertex_dist = 1e100;
    int vertex_idx = -1;

    double fiducial_dist = 1e100;
    int fiducial_idx = -1;
  };

  NearestItem nearest_items(
      EditorModeId mode,
      const int level_index,
      const double x,
      const double y);

  ScenarioLevel *scenario_level(const int building_level_idx);

  void set_selected_containing_polygon(
      const EditorModeId mode,
      const int level_idx,
      const double x,
      const double y);

  void mouse_select_press(
      const EditorModeId mode,
      const int level_idx,
      const double x,
      const double y,
      QGraphicsItem *graphics_item);

  Polygon::EdgeDragPolygon polygon_edge_drag_press(
      const EditorModeId mode,
      const int level_idx,
      const Polygon *polygon,
      const double x,
      const double y);

  Polygon *get_selected_polygon(const EditorModeId mode, const int level_idx);

private:
  bool load_yaml_file(const std::string& _filename);
  bool save_yaml_file() const;

  void set_selected_line_item(
      const int level_idx,
      QGraphicsLineItem *line_item);
};

#endif
