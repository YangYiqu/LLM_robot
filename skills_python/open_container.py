import random


def open_container(robot_info):
    def open_container(container_name):
        if container_name in robot_info.openned_containers:
            return (
                "Fail to open container, because the robot has openned the "
                + container_name
                + "before, you should try other containers."
            )
        elif (
            robot_info.current_loc[0] == robot_info.known_dict.get(container_name)
            and random.random() < 0.95
        ):
            robot_info.openned_containers.append(container_name)
            return (
                "Success open container: "
                + container_name
                + ", Please search the target object by search_object tool again"
            )
        elif robot_info.current_loc[0] != robot_info.known_dict.get(container_name):
            return (
                "Fail to open container, the robot is in a wrong location, you can choose to 1. move to the "
                + container_name
                + " by move_to_object tool or 2. you should review the task and change the thought to move to the right location"
            )
        else:
            return (
                "Fail to open container, please try to open it again, using open_container("
                + container_name
                + ")"
            )

    return open_container


# def open_container(container_name):
#     global known_dict, grabbed_objects, current_loc, openned_containers
#     if container_name in openned_containers:
#         return (
#             "The robot has openned the "
#             + container_name
#             + "before, you should try other containers."
#         )
#     elif current_loc[0] == known_dict.get(container_name) and random.random() < 0.95:
#         openned_containers.append(container_name)
#         return (
#             "Success open container: "
#             + container_name
#             + ", Please search the target object by search_object tool again"
#         )
#     elif current_loc[0] != known_dict.get(container_name):
#         return (
#             "Fail to open container, the robot is in a wrong location, you can choose to 1. move to the "
#             + container_name
#             + " by move_to_object tool or 2. you should review the task and change the thought to move to the right location"
#         )
#     else:
#         return (
#             "Fail to open container, please try to open it again, using open_container("
#             + container_name
#             + ")"
#         )
