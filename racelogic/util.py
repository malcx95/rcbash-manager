def get_previous_group_wrap_around(heat_start_lists, race_order, index):
    temp_index = index
    while True:
        if temp_index == 0:
            temp_index = len(race_order) - 1
        else:
            temp_index -= 1
        previous_rcclass, previous_group = race_order[temp_index]

        if previous_group in heat_start_lists[previous_rcclass]:
            return previous_rcclass, previous_group
