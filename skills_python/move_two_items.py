from skills_python import move_item_to_target_location

def move_two_items(item1, target1, item2, target2):
    # Move the first item to its target location
    move_item_to_target_location(item_name=item1, target_name=target1)
    
    # Move the second item to its target location
    move_item_to_target_location(item_name=item2, target_name=target2)