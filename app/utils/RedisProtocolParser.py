def parse_protocol(data):
    if not data:
        return None

    marker = data[0]
    parser = ProtocolParserFactory.create_parser(marker)
    if parser:
        return parser.parse(data[1:])
    else:
        raise ValueError("Invalid marker: {}".format(marker))


class RedisProtocolParser:
    def parse(self, data):
        raise NotImplementedError("Subclasses must implement parse method")


class BulkStringParser(RedisProtocolParser):
    def parse(self, data):
        length, data = data.split('\r\n', 1)
        length = int(length)
        if length == -1:
            return None, data
        else:
            return data[:length], data[length + 2:]


class ArrayParser(RedisProtocolParser):
    def parse(self, data):
        length, data = data.split('\r\n', 1)
        length = int(length)
        result = []
        for _ in range(length):
            element, data = parse_protocol(data)
            result.append(element)
        return result, data


class SimpleStringParser(RedisProtocolParser):
    def parse(self, data):
        return data.split('\r\n', 1)[0], data.split('\r\n', 1)[1]


class ErrorParser(RedisProtocolParser):
    def parse(self, data):
        return data.split('\r\n', 1)[0], data.split('\r\n', 1)[1]


class IntegerParser(RedisProtocolParser):
    def parse(self, data):
        return int(data.split('\r\n', 1)[0]), data.split('\r\n', 1)[1]


class MapParser(RedisProtocolParser):
    def parse(self, data):
        length, data = data.split('\r\n', 1)
        length = int(length)
        result = {}
        for _ in range(length):
            key, data = parse_protocol(data)
            value, data = parse_protocol(data)
            result[key] = value
        return result, data


class ProtocolParserFactory:
    @staticmethod
    def create_parser(marker):
        parsers = {
            '$': BulkStringParser(),
            '*': ArrayParser(),
            '+': SimpleStringParser(),
            '-': ErrorParser(),
            ':': IntegerParser(),
            '%': MapParser(),
        }
        return parsers.get(marker, None)
