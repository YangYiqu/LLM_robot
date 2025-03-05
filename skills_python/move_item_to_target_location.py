from skills_python import search_object, move_to_object, grab_object, release_object


def move_item_to_target_location(item_name, target_name):
    # Find the location of the item to be moved
    item_location = search_object(object_name=item_name)

    # Move the robot to the location of the item
    move_to_object(object_name=item_name)

    # Grab the item
    grab_object(object_name=item_name, tableware_name="hand")

    # Find the location of the target object
    target_location = search_object(object_name=target_name)

    # Move the robot to the location of the target object
    move_to_object(object_name=target_name)

    # Release the item at the location of the target object
    release_object()
