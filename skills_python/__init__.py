from ._robot_info import robot_info

from .grab_object import grab_object

grab_object = grab_object(robot_info)

from .release_object import release_object

release_object = release_object(robot_info)

from .search_object import search_object

search_object = search_object(robot_info)

from .move_to_coordinates import move_to_coordinates

move_to_coordinates = move_to_coordinates(robot_info)

from .move_to_object import move_to_object

move_to_object = move_to_object(robot_info)

from .release_object import release_object

release_object = release_object(robot_info)

from .move_item_to_target_location import move_item_to_target_location


from .move_two_items import move_two_items
