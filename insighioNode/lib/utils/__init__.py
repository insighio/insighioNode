import logging
import esp32
import uos

key_value_storage = esp32.NVS("insighio")

def existsFile(source):
    try:
        uos.stat(source)
        return True
    except Exception as e:
        return False

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

def renameFile(source, destination):
    try:
        uos.rename(source, destination)
        return True
    except Exception as e:
        logging.exception(e, "Error renaming file [{}] to [{}]".format(source, destination))
        return False


def readFromFile(source):
    try:
        f = open(source, "r")
        contents = f.read()
        f.close()
        return contents
    except Exception as e:
        logging.error("Error reading file [{}]".format(source))
        return ""


def appendToFile(destination, content):
    return writeToFile(destination, content, True)


def writeToFile(destination, content, do_append=False):
    try:
        out_file = open(destination, "w" if not do_append else "a")
        out_file.write(content)
        out_file.close()
        return True
    except Exception as e:
        logging.exception(e, "Error writing to file [{}]".format(destination))
        return False


def deleteFile(destination):
    try:
        import uos
        uos.remove(destination)
    except Exception as e:
        logging.exception(e, "Error writing to file [{}]".format(destination))
        return False


def countFileLines(fname):
    lines = 0
    buf_size = 256
    has_any_bytes = False
    try:
        with open(fname) as f:
            buf = f.read(buf_size)
            while buf:
                lines += buf.count("\n")
                buf = f.read(buf_size)
    except:
        pass

    return lines


# key max length: 15 chars
def getKeyValueInteger(key):
    try:
        return key_value_storage.get_i32(key)
    except:
        return None


def saveKeyValueInteger(key, value):
    current_value = getKeyValueInteger(key)
    if current_value != value:
        logging.debug("key-value storage: saving [{}]={}".format(key, value))
        try:
            key_value_storage.set_i32(key, value)
            key_value_storage.commit()
        except Exception as e:
            logging.exception(e, "Error saving key-value [{}]={}".format(key, value))


def eraseKeyValue(key):
    try:
        key_value_storage.erase_key(key)
    except Exception as e:
        logging.debug("Key [{}] not set".format(key))


def clearCachedStates():
    eraseKeyValue("tz_sec_offset")
