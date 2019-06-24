"""This module contains all the custom made exceptions used in the pycomed sdk.

"""


class PathNotSpecifiedException(Exception):
    """Exception thrown when the path is not specified.

    """

    def __init__(self):
        super(PathNotSpecifiedException, self).__init__("The path is not specified and cannot be None.")


class MalformedDatasetException(Exception):
    """Exception thrown when the dataset that needs to be organized has a different
    schema and cannot be organized.

    """

    def __init__(self):
        super(MalformedDatasetException, self).__init__("The dataset is not following the schema used by pycomed.")


class WrongDateIntervalException(Exception):
    """Exception thrown when a date interval is not specified correctly.

    """

    def __init__(self):
        super(WrongDateIntervalException, self).__init__(
            "There is a problem in the date interval, check if date interval is correctly specified.")


class ScanTypeNotSupportedException(Exception):
    """Exception thrown when the scan type is not supported.
    """

    def __init__(self):
        super(ScanTypeNotSupportedException, self).__init__("pycomed currently does not support this scan type.")
