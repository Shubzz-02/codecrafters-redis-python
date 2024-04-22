# Create python code to construct string/array into proper RESP data type,
# for example for Bulk String if the input is "$hello"
# create function to return proper RESP data type as -> $5\r\nhello\r\n

def resp_builder(marker, data):
    parser = RESPBuilderFactory.create_builder(marker)
    if parser:
        return parser.builder(data)
    else:
        raise ValueError("Invalid marker: {}".format(marker))


class RESPBuilder:
    def builder(self, data):
        raise NotImplementedError("Subclasses must implement parse method")


class BulkStringBuilder(RESPBuilder):
    def builder(self, data):
        if data is None:
            return "$-1\r\n"
        return f"${len(data)}\r\n{data}\r\n"


class SimpleStringBuilder(RESPBuilder):
    def builder(self, data):
        return f"+{data}\r\n"


class ErrorBuilder(RESPBuilder):
    def builder(self, data):
        return f"-{data}\r\n"


class IntegerBuilder(RESPBuilder):
    def builder(self, data):
        return f":{data}\r\n"


# create Array Builder the input will be
# class ArrayBuilder(RESPBuilder):


class RESPBuilderFactory:
    @staticmethod
    def create_builder(marker):
        builders = {
            '$': BulkStringBuilder(),
            '+': SimpleStringBuilder(),
            '-': ErrorBuilder(),
            ':': IntegerBuilder(),
        }
        return builders.get(marker, None)
