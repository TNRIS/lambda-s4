import os

# get this directory
cur_dir = os.path.dirname(os.path.realpath(__file__))
print(cur_dir)

# non-whitelist files that we don't want to delete
hrd_whitelist = []
hrd_whitelist.append(cur_dir + "/dep_cleanup.py")
hrd_whitelist.append(cur_dir + "/dep_whitelist.txt")
hrd_whitelist.append(cur_dir + "/lambda_function.py")
hrd_whitelist.append(cur_dir + "/requirements.txt")
print("hardcoded to include:")
print(hrd_whitelist)

# open dep_whitelist file and merge with hardcoded list
dep_whitelist = open("dep_whitelist.txt", "r")
dep_lines = dep_whitelist.read().splitlines()
whitelist = hrd_whitelist + dep_lines

# count files deleted
counter = 0

# walk all files and folders and check if it is in the dep_whitelist
for (dirpath, dirnames, filenames) in os.walk(cur_dir):
    for filename in filenames:
        single_file = os.path.join(dirpath, filename)
        # if not in dep_whitelist then delete
        if single_file not in whitelist:
            os.remove(single_file)
            counter += 1

print(str(counter) + " files deleted")
print("that's all folks!!")
