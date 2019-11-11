# Functions that are only used in the command line version of the app.
def print_metadata(track):
    for k, v in track.items():
        print(k, ":", v)


def amend_metadata(metadata):
    for k, v in metadata.items():
        print("")
        print(k, ":", v)
        while True:
            new = input("Enter new value or if no change required, press [Enter] ==> ")
            if new == "":
                break
            print("New value for {} is:".format(k))
            print("==>", new)
            check = input("Are you sure? [y]/[Enter]    [n] ==> ")
            if check == "" or check == "y":
                metadata[k] = new
                print("OK. {} value saved.".format(k))
                break
            else:
                continue
    print("Final metadata:")
    print_metadata(metadata)
    return metadata