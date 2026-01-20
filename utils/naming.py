import cr_tempController.constants as constants

def build_temp_control_data_name(controller: str) -> str:
    return f"{controller}{constants.SUFFIXE_TEMP_CONTROL_DATA}"
