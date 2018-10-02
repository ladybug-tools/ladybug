"""Comfort model object."""


class ComfortModel(object):
    """
    thermal Comfort Model base class.
    """

    def __init__(self):
        self.__calcLength = None
        self.__isDataAligned = False
        self.__isRelacNeeded = True

        self.__headerIncl = False
        self.__headerStr = []
        self.__singleVals = False

    def _check_input_list(self, input_value, default_value,
                          input_val_name, header_val_name):
        """
        Check length of the input_value list and evaluate the contents.
        """
        check_data = False
        final_vals = []
        mult_val = False
        if len(input_value) != 0:
            try:
                if header_val_name in input_value[2]:
                    final_vals = input_value[7:]
                    check_data = True
                    self.__headerIncl = True
                    self.__headerStr = input_value[0:7]
            except BaseException:
                pass
            if check_data is False:
                for item in input_value:
                    try:
                        final_vals.append(float(item))
                        check_data = True
                    except BaseException:
                        check_data = False
            if len(final_vals) > 1:
                mult_val = True
            if check_data is False:
                raise Exception(input_val_name + " input is not of a valid input type.")
        else:
            check_data = True
            final_vals = default_value
            if len(final_vals) > 1:
                mult_val = True

        return check_data, final_vals, mult_val

    def build_custom_header(self, header_name, header_units):
        """
        Builds a customized header for a certain data type given the header on the
        inputs.
        """
        new_head_str = self.__headerStr
        new_head_str[2] = header_name
        new_head_str[3] = header_units
        return new_head_str
