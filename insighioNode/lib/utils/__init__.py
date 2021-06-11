import logging

def copyFile(source, destination):
    try:
        in_file = open(source, "r")
        out_file = open(destination, "w")
        contents = in_file.read()
        out_file.write(contents)
        in_file.close()
        out_file.close()
        return True
    except Exception as e:
        logging.exception(e, "Error copying file [{}] to [{}]".format(source, destination))
        return False


def readFromFile(source):
    try:
        f = open(source, "r")
        contents = f.read()
        f.close()
        return contents
    except Exception as e:
        logging.exception(e, "Error reading file [{}]".format(source))
        return ""


def writeToFile(destination, content):
    try:
        out_file = open(destination, "w")
        out_file.write(content)
        out_file.close()
        return True
    except Exception as e:
        logging.exception(e, "Error writing to file [{}]".format(destination))
        return False
